"""Draft review replies and name the recurring themes behind a weak rating.

The deterministic worker decides which reviews wait for a reply and whether the rating
is a problem. This module asks the model for one reply per unanswered low review, in
line with Google's reply guidance, and for a short list of themes drawn from the
review text. Every draft is checked in code before it is attached: length, no contact
details, no names, one per finding.
"""

import re
from datetime import UTC, datetime

from app.services.recommendations.categories.reputation import (
    CHECKS,
    critical,
    dated,
    newest_first,
    replied,
    review_ref,
    stars,
)
from app.services.recommendations.suggestions.matching import resolve_target
from app.services.recommendations.types import Suggestion
from app.services.recommendations.values import day

# Which field each check may have drafted, for matching a reply back to its finding.
SUGGESTS = {rule: spec["suggests"] for rule, spec in CHECKS.items() if spec.get("suggests")}

REPLY_MAX_CHARS = 350
THEME_MAX = 8
THEME_MAX_CHARS = 80
COMMENT_CHARS = 400
UNANSWERED_IN_CONTEXT = 10
RECENT_IN_CONTEXT = 40

FIELD_SHAPES = {
    "review_reply": (
        "a single string, under 350 characters: thank the reviewer, acknowledge the "
        "specific concern in their comment, apologise where warranted, invite them to "
        "continue offline with the business. No names, no phone numbers, no email "
        "addresses, no links, no promotions or discounts."
    ),
    "themes": (
        "a list of two to eight short phrases, each naming one recurring complaint or "
        "praise found in the review text, most frequent first, e.g. 'long waits at "
        "reception' or 'gentle hygienists'"
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
                    "value_list": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "reason": {"type": "STRING"},
                    "confidence": {"type": "STRING", "enum": ["high", "medium", "low"]},
                },
                "required": ["rule", "field", "reason", "confidence"],
            },
        },
    },
    "required": ["summary", "suggestions"],
}


def targets(result: dict) -> list[dict]:
    """The findings a draft may be made for, one per rule and subject."""
    return [
        item for item in result.get("items", []) if CHECKS.get(item["rule"], {}).get("suggests")
    ]


def _review_for_context(row: dict) -> dict:
    comment = " ".join(str(row.get("comment") or "").split())
    created = day(row.get("create_time"))
    return {
        "id": review_ref(row),
        "rating": stars(row),
        "date": created.isoformat() if created else None,
        "comment": comment[:COMMENT_CHARS],
        "replied": replied(row),
    }


def business_context(snapshot: dict) -> dict:
    loc = snapshot["locations"][0]
    reviews = newest_first(
        dated([r for r in snapshot.get("reviews", []) if r.get("location_id") == loc["id"]])
    )
    unanswered = [r for r in reviews if critical(r) and not replied(r)]
    with_text = [r for r in reviews if str(r.get("comment") or "").strip()]
    return {
        "name": loc.get("title"),
        "primary_category": loc.get("primary_category_display"),
        "city": loc.get("locality"),
        "projects": [
            {
                "name": p.get("name"),
                "website": p.get("website_url"),
                "description": p.get("description"),
                "services": p.get("services") or [],
            }
            for p in snapshot.get("projects", [])
        ],
        "unanswered_low_reviews": [
            _review_for_context(r) for r in unanswered[:UNANSWERED_IN_CONTEXT]
        ],
        "recent_reviews": [_review_for_context(r) for r in with_text[:RECENT_IN_CONTEXT]],
    }


def wants(result: dict) -> bool:
    """A model call is worth making when there is anything to draft or summarise."""
    return bool(result.get("items"))


def build_prompt(context: dict, items: list[dict], findings: list[dict] | None = None) -> str:
    findings = findings if findings is not None else items
    all_findings = "\n".join(f"- [{f['severity']}] {f['title']}: {f['why']}" for f in findings)
    asks = "\n".join(
        f"- rule={item['rule']}"
        + (f" subject={item['subject']}" if item.get("subject") else "")
        + f" field={CHECKS[item['rule']]['suggests']}: {item['why']}"
        for item in items
    )
    shapes = "\n".join(f"- {field}: {shape}" for field, shape in FIELD_SHAPES.items())
    return f"""You help one local business answer its Google reviews and understand them.
You are given the business (name, category, city, the operator's own project description
and services), its recent reviews, the low reviews still waiting for a reply, and the
audit findings that need a draft. Return one suggestion per finding.

Rules you must follow:
- review_reply: the subject is the review id; find that review in unanswered_low_reviews
  and write a reply to it, following Google's guidance: thank the reviewer, acknowledge
  the specific concern in their own words, apologise where warranted, share no private
  details, and invite them to contact the business directly to put it right. Do not
  address the reviewer by name and do not invent one. Do not mention other customers,
  staff names, prices, offers, discounts, phone numbers, email addresses or links. Keep
  it under 350 characters and sign off as the team. If the comment is empty, keep the
  reply short and general.
- themes: read recent_reviews and list the recurring complaints and praise as short
  phrases, most frequent first. Only themes that appear in more than one review.
  Confidence medium when several reviews say it, low when few do; never high.
- Put the value in exactly one of value_text or value_list, matching the field's shape:
{shapes}
- reason: one short sentence naming the review detail or pattern the draft rests on.
- confidence: for replies, high when the comment states the concern plainly, medium
  when it is inferred, low when the comment is empty.

- summary: two or three short sentences for the location manager, in plain language, built
  only from the findings listed below (all of them, not only those needing a draft).
  Say what customers see, what to do first, and what is already fine. No scores, no
  percentages, no promises about rankings or revenue.

Business and reviews (JSON):
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
        text = "Every reputation check that could run passed. Customers see a healthy profile."
    else:
        by_severity = {"critical": [], "warning": [], "notice": []}
        for item in items:
            by_severity[item["severity"]].append(item["title"])
        parts = []
        if by_severity["critical"]:
            parts.append("Fix first: " + "; ".join(by_severity["critical"][:3]).lower() + ".")
        if by_severity["warning"]:
            parts.append("Then: " + "; ".join(by_severity["warning"][:3]).lower() + ".")
        if by_severity["notice"]:
            parts.append(
                f"{len(by_severity['notice'])} smaller "
                + ("item" if len(by_severity["notice"]) == 1 else "items")
                + " to confirm when convenient."
            )
        text = " ".join(parts)
    return {
        "text": text,
        "source": "deterministic",
        "model": None,
        "generated_at": datetime.now(UTC).isoformat(),
    }


CONTACT = re.compile(r"(?:https?://|www\.|\b\S+@\S+\.\S+\b|\+?\d[\d\s().-]{7,}\d)", re.I)
# A greeting or honorific followed by a capitalised word is a name the model invented.
NAMED = re.compile(
    r"(?:\b(?:Hi|Hello|Hey|Dear)\s+(?!there\b|all\b|team\b)[A-Z][a-z]+|\b(?:Mr|Mrs|Ms|Dr|Miss)\.?\s+[A-Z])"
)
PROMOTION = re.compile(r"\b(?:discount|coupon|% off|free (?:visit|cleaning|consult)|promo)\b", re.I)


def _safe_value(field: str, value, context: dict):
    """Enforce constraints that must not depend on the model following the prompt."""
    if field == "review_reply":
        if not isinstance(value, str):
            return None
        value = " ".join(value.split())
        if CONTACT.search(value) or NAMED.search(value) or PROMOTION.search(value):
            return None
        if len(value) > REPLY_MAX_CHARS:
            value = value[:REPLY_MAX_CHARS].rsplit(" ", 1)[0]
        return value or None
    if field == "themes":
        if not isinstance(value, list):
            return None
        chosen: list[str] = []
        for theme in value:
            text = " ".join(str(theme).split()).strip(" .")
            if (
                not text
                or CONTACT.search(text)
                or text.casefold() in {t.casefold() for t in chosen}
            ):
                continue
            chosen.append(text[:THEME_MAX_CHARS])
            if len(chosen) == THEME_MAX:
                break
        return chosen or None
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
        value: str | list[str]
        if raw.get("value_list"):
            value = [str(v) for v in raw["value_list"]]
        else:
            value = str(raw.get("value_text") or "").strip()
        value = _safe_value(field, value, context)
        if not value:
            continue
        confidence = raw.get("confidence") or "low"
        if field == "themes" and confidence == "high":
            confidence = "medium"
        item["suggestion"] = Suggestion(
            field=field,
            value=value,
            reason=str(raw.get("reason") or "").strip(),
            confidence=confidence,
            source=source,
            model=model,
            generated_at=stamped,
        ).model_dump(mode="json")
        item["explanation_source"] = "deterministic+generated"
        seen.add(identity)
        attached += 1
    return attached
