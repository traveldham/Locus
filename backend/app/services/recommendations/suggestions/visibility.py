"""Draft the next move for the keywords and search terms the visibility audit flagged.

The deterministic worker decides which keywords sit just below the pack, which
high-intent keywords lag, and which search terms are losing volume. This module asks
the model for one concrete, profile-side action per finding, grounded in the stored
profile, the keyword table and the operator's own service list. It never promises a
position and never drafts anything about a keyword the audit did not name.
"""

import re
from datetime import UTC, datetime

from app.services.recommendations.categories.visibility import (
    CHECKS,
)
from app.services.recommendations.categories.visibility import (
    card as visibility_card,
)
from app.services.recommendations.suggestions.matching import resolve_target
from app.services.recommendations.types import Suggestion

# Which field each check may have drafted, for matching a reply back to its finding.
SUGGESTS = {rule: spec["suggests"] for rule, spec in CHECKS.items() if spec.get("suggests")}

SENTENCE_MAX_CHARS = 240

# Which suggestion fields may be drafted, and what shape the value takes.
FIELD_SHAPES = {
    "keyword_plan": (
        "an object mapping the finding's keyword to one sentence naming the exact profile "
        "change to make for it: which category, service, attribute or post to add"
    ),
    "term_action": (
        "a single sentence naming the exact profile change that answers the search term: "
        "a service to list, an attribute to set, hours to confirm or a post to publish"
    ),
}

RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "summary": {"type": "STRING"},
        "suggestions": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "rule": {"type": "STRING"},
                    "subject": {"type": "STRING"},
                    "field": {"type": "STRING"},
                    "value_text": {"type": "STRING"},
                    "value_map": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "name": {"type": "STRING"},
                                "value": {"type": "STRING"},
                            },
                            "required": ["name", "value"],
                        },
                    },
                    "reason": {"type": "STRING"},
                    "confidence": {"type": "STRING", "enum": ["high", "medium", "low"]},
                },
                "required": ["rule", "subject", "field", "reason", "confidence"],
            },
        },
    },
    "required": ["summary", "suggestions"],
}


def targets(result: dict) -> list[dict]:
    """The findings a suggestion may be drafted for, one per rule and subject."""
    return [
        item
        for item in result.get("items", [])
        if CHECKS.get(item["rule"], {}).get("suggests") and item.get("subject")
    ]


def business_context(snapshot: dict) -> dict:
    loc = snapshot["locations"][0]
    location_id = loc["id"]
    rows = lambda source: [  # noqa: E731 - tiny local helper
        r for r in snapshot.get(source, []) if r.get("location_id") == location_id
    ]
    card = visibility_card(snapshot)
    return {
        "name": loc.get("title"),
        "primary_category": loc.get("primary_category_display"),
        "additional_categories": [
            r.get("display_name") for r in rows("categories") if not r.get("is_primary")
        ],
        "city": loc.get("locality"),
        "state": loc.get("administrative_area"),
        "description": loc.get("description"),
        "keywords": [
            {
                "keyword": k["keyword"],
                "intent": k["intent"],
                "device": k["device"],
                "latest_position": k["position"],
                "weeks_in_pack": k["weeks_in_pack"],
            }
            for k in card["keywords"]
        ],
        "top_search_terms": card["top_terms"],
        "rivals_ahead": card["rivals_ahead"],
        "ours": card["ours"],
        "projects": [
            {
                "name": p.get("name"),
                "website": p.get("website_url"),
                "description": p.get("description"),
                "services": p.get("services") or [],
            }
            for p in snapshot.get("projects", [])
        ],
    }


def wants(result: dict) -> bool:
    """A model call is worth making when there is anything to draft or summarise."""
    return bool(result.get("items"))


def build_prompt(context: dict, items: list[dict], findings: list[dict] | None = None) -> str:
    findings = findings if findings is not None else items
    all_findings = "\n".join(f"- [{f['severity']}] {f['title']}: {f['why']}" for f in findings)
    asks = "\n".join(
        f"- rule={item['rule']} subject={item['subject']} "
        f"field={CHECKS[item['rule']]['suggests']}: {item['why']}"
        for item in items
    )
    shapes = "\n".join(f"- {field}: {shape}" for field, shape in FIELD_SHAPES.items())
    return f"""You plan concrete profile-side actions for one Google Business Profile's local
search visibility. You are given the stored profile, its tracked keywords with their
latest positions, the search terms that surface it, the rivals ranked ahead, the
operator's own description of the business (projects), and the audit findings that need
a draft. Return one suggestion per finding.

Rules you must follow:
- Draft only for the field named in each finding, and only about the keyword or search
  term named as its subject. Never mention any other keyword or term.
- keyword_plan: value_map with exactly one entry, name = the subject keyword, value = one
  sentence naming the profile change: the category to add, the service to list, the
  attribute to set to yes, or the post to publish. Tie it to a service from the projects
  context when one matches; never invent a service the context does not support.
- term_action: value_text, one sentence naming the profile change that answers the term.
- Never promise a position, a ranking gain or revenue. Never include a URL, a phone
  number, a price or a competitor's name in a value.
- Put the value in exactly one of value_text or value_map, matching the field's shape:
{shapes}
- reason: one short sentence naming the exact stored fact or project detail that supports the draft.
- confidence: high when the context states the service is offered, medium when it is a
  reasonable inference, low when it is a guess a manager must check.

- summary: two or three short sentences for the location manager, in plain language, built
  only from the findings listed below (all of them, not only those needing a draft).
  Say where the profile stands in local search, what to do first, and what is already
  fine. No scores, no percentages, no promises about rankings or revenue.

Profile and context (JSON):
{context}

All findings from the audit:
{all_findings}

Findings needing a draft:
{asks}
"""


def fallback_summary(result: dict) -> dict:
    """A summary written by code, used when no model answered."""
    items = result.get("items", [])
    if not items:
        text = (
            "Every visibility check that could run passed. The profile holds its ground in "
            "local search right now."
        )
    else:
        by_rule: dict[str, list[dict]] = {}
        for item in items:
            by_rule.setdefault(item["rule"], []).append(item)
        parts = []
        if "branded_not_first" in by_rule:
            parts.append("Fix first: the profile does not come first for its own name.")
        if "pack_share_low" in by_rule:
            parts.append(by_rule["pack_share_low"][0]["why"])
        near = by_rule.get("near_pack_opportunity", [])
        if near:
            parts.append(
                f"{len(near)} "
                + ("keyword sits" if len(near) == 1 else "keywords sit")
                + " just below the local pack: "
                + ", ".join(i["subject"] for i in near[:3])
                + ("." if len(near) <= 3 else " and more.")
            )
        losing = by_rule.get("search_term_losing", [])
        if losing:
            parts.append(
                f"{len(losing)} search "
                + ("term is" if len(losing) == 1 else "terms are")
                + " losing impressions month over month."
            )
        rivals = by_rule.get("rival_ahead_gap", [])
        if rivals:
            parts.append(
                f"{len(rivals)} "
                + ("rival is" if len(rivals) == 1 else "rivals are")
                + " ahead on several keywords with a stronger profile."
            )
        if not parts:
            parts.append(items[0]["why"])
        text = " ".join(parts)
    return {
        "text": text,
        "source": "deterministic",
        "model": None,
        "generated_at": datetime.now(UTC).isoformat(),
    }


def _clean_sentence(value) -> str | None:
    """One plain sentence: no links, no phone numbers, capped in length."""
    if not isinstance(value, str):
        return None
    value = " ".join(value.split())
    if not value:
        return None
    if re.search(r"(?:https?://|www\.|\b\S+@\S+\.\S+\b)", value, re.I):
        return None
    if re.search(r"(?:\+?\d[\d\s().-]{7,}\d)", value):
        return None
    if len(value) > SENTENCE_MAX_CHARS:
        cut = value[:SENTENCE_MAX_CHARS]
        value = cut.rsplit(" ", 1)[0].rstrip(",;:") + "."
    return value


def _safe_value(field: str, value, subject: str):
    """Enforce constraints that must not depend on the model following the prompt."""
    if field == "keyword_plan":
        if not isinstance(value, dict):
            return None
        chosen = {}
        for name, sentence in value.items():
            if str(name).strip().casefold() != subject.strip().casefold():
                continue
            cleaned = _clean_sentence(sentence)
            if cleaned:
                chosen[subject] = cleaned
        return chosen or None
    if field == "term_action":
        return _clean_sentence(value)
    return None


def apply(result: dict, response: dict, source: str, model: str, context: dict) -> int:
    """Attach validated suggestions to the findings they answer. Returns how many."""
    by_key = {(i["rule"], i.get("subject") or ""): i for i in targets(result)}
    stamped = datetime.now(UTC).isoformat()
    attached = 0
    seen: set[tuple[str, str]] = set()
    summary = str(response.get("summary") or "").strip()
    if summary:
        result["summary"] = {
            "text": summary[:1200],
            "source": source,
            "model": model,
            "generated_at": stamped,
        }
    for raw in response.get("suggestions", []):
        item = resolve_target(by_key, raw, SUGGESTS)
        if item is None:
            continue
        identity = (item["rule"], item.get("subject") or "")
        if identity in seen:
            continue
        field = CHECKS[item["rule"]]["suggests"]
        if raw.get("field") != field:
            continue
        value: str | dict
        if raw.get("value_map"):
            value = {
                str(e["name"]): str(e["value"])
                for e in raw["value_map"]
                if isinstance(e, dict) and "name" in e and "value" in e
            }
        else:
            value = str(raw.get("value_text") or "").strip()
        value = _safe_value(field, value, item["subject"])
        if not value:
            continue
        item["suggestion"] = Suggestion(
            field=field,
            value=value,
            reason=str(raw.get("reason") or "").strip(),
            confidence=raw.get("confidence") or "low",
            source=source,
            model=model,
            generated_at=stamped,
        ).model_dump(mode="json")
        item["explanation_source"] = "deterministic+generated"
        seen.add(identity)
        attached += 1
    return attached
