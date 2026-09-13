"""Draft posts and photo shot lists for the content findings.

The deterministic worker decides what failed. This module asks the model for two
ready-to-publish posts where the cadence or mix is weak, and for a shot list where a
photo type is empty or the count is low. Every draft is checked in code for the things
Google rejects: phone numbers, links, shouting, and length.
"""

import re
from datetime import UTC, datetime

from app.services.recommendations.categories.content import CHECKS, dated_posts, post_type
from app.services.recommendations.suggestions.matching import resolve_target
from app.services.recommendations.types import Suggestion

# Which field each check may have drafted, for matching a reply back to its finding.
SUGGESTS = {rule: spec["suggests"] for rule, spec in CHECKS.items() if spec.get("suggests")}

POST_MAX_CHARS = 300
POST_DRAFTS = 2
SHOT_LIST_MIN, SHOT_LIST_MAX = 5, 8
SHOT_MAX_CHARS = 120

FIELD_SHAPES = {
    "post_drafts": (
        f"a list of exactly {POST_DRAFTS} posts, each under {POST_MAX_CHARS} characters: "
        "the first a plain update, the second an offer or an event; each about a service "
        "from the projects context; no phone numbers, no links, no words in ALL CAPS, no "
        "prices unless the context states one; end each with the button it should carry, "
        "for example '(Button: Book)'"
    ),
    "photo_shot_list": (
        f"a list of {SHOT_LIST_MIN} to {SHOT_LIST_MAX} specific shots to take, each one "
        f"short line under {SHOT_MAX_CHARS} characters, for example 'Reception desk with "
        "the practice name visible', matched to the photo type in the finding and to the "
        "business category"
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
                    "value_list": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "reason": {"type": "STRING"},
                    "confidence": {"type": "STRING", "enum": ["high", "medium", "low"]},
                },
                "required": ["rule", "field", "value_list", "reason", "confidence"],
            },
        },
    },
    "required": ["summary", "suggestions"],
}

URL_OR_EMAIL = re.compile(r"(?:https?://|www\.|\b\S+@\S+\.\S+\b)", re.I)
PHONE = re.compile(r"(?:\+?\d[\d\s().-]{7,}\d)")
SHOUTING = re.compile(r"\b[A-Z]{4,}\b")


def targets(result: dict) -> list[dict]:
    """The findings a suggestion may be drafted for, one per rule and subject."""
    return [
        item for item in result.get("items", []) if CHECKS.get(item["rule"], {}).get("suggests")
    ]


def business_context(snapshot: dict) -> dict:
    loc = snapshot["locations"][0]
    location_id = loc["id"]
    rows = lambda source: [  # noqa: E731 - tiny local helper
        r for r in snapshot.get(source, []) if r.get("location_id") == location_id
    ]
    media = rows("media")
    row = media[0] if media else {}
    posts = dated_posts(rows("posts"))
    return {
        "name": loc.get("title"),
        "primary_category": loc.get("primary_category_display"),
        "additional_categories": [
            r.get("display_name") for r in rows("categories") if not r.get("is_primary")
        ],
        "city": loc.get("locality"),
        "state": loc.get("administrative_area"),
        "description": loc.get("description"),
        "media": {
            "photo_count": row.get("photo_count"),
            "interior_photo_count": row.get("interior_photo_count"),
            "exterior_photo_count": row.get("exterior_photo_count"),
            "team_photo_count": row.get("team_photo_count"),
            "video_count": row.get("video_count"),
            "last_photo_uploaded_on": row.get("last_photo_uploaded_on"),
        },
        "recent_posts": [
            {
                "type": post_type(r),
                "published_on": str(r.get("published_on"))[:10],
                "summary": str(r.get("summary") or "")[:200],
                "cta": str(r.get("cta_type") or "").casefold() or None,
            }
            for r in posts[:5]
        ],
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
        f"- rule={item['rule']}"
        + (f" subject={item['subject']}" if item.get("subject") else "")
        + f" field={CHECKS[item['rule']]['suggests']}: {item['why']}"
        for item in items
    )
    shapes = "\n".join(f"- {field}: {shape}" for field, shape in FIELD_SHAPES.items())
    return f"""You draft photo and post content for one Google Business Profile.
You are given the stored profile, its photo counts and recent posts, the operator's own
description of the business (projects), and the audit findings that need a draft.
Return one suggestion per finding.

Rules you must follow:
- Draft only for the field named in each finding. Never invent a phone number, street
  address, opening hours, price, discount or website. Never mention a phone number or
  a link inside a post: Google rejects posts that carry them.
- Base every draft on the services in the projects context. Do not add services the
  context does not support. If the context is too thin, lower the confidence.
- Write in plain, professional language. No words in ALL CAPS, no exclamation runs, no
  gimmicky or filler text, no misspellings. Family friendly.
- post_drafts: two posts a manager could publish today. The first is a plain update
  about a service or the team. The second is an offer or an event; if the context gives
  no price or date, describe it without one and say what the manager must fill in.
  Each under {POST_MAX_CHARS} characters.
- photo_shot_list: concrete shots, one per line, that fill the empty photo type in the
  finding (interior, exterior or team) or, for a low count, cover the whole visit. Name
  what is in the frame and why a customer wants to see it.
- Put the value in value_list, matching the field's shape:
{shapes}
- reason: one short sentence naming the exact stored fact or project detail that supports the draft.
- confidence: high when the context states it, medium when it is a reasonable
  inference, low when it is a guess a manager must check.

- summary: two or three short sentences for the location manager, in plain language, built
  only from the findings listed below (all of them, not only those needing a draft).
  Say what is missing and why a customer notices, what to do first, and what is already
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
        text = "Every content check that could run passed. Photos and posts are in good shape."
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


def clean_line(value, limit: int) -> str | None:
    """One line of draft text that breaks none of Google's post rules, or None."""
    if not isinstance(value, str):
        return None
    text = " ".join(value.split())
    if not text or len(text) > limit:
        return None
    if URL_OR_EMAIL.search(text) or PHONE.search(text) or SHOUTING.search(text):
        return None
    return text


def _safe_value(field: str, value) -> list[str] | None:
    """Enforce constraints that must not depend on the model following the prompt."""
    if not isinstance(value, list):
        return None
    if field == "post_drafts":
        drafts = [clean_line(v, POST_MAX_CHARS) for v in value]
        drafts = [d for d in drafts if d]
        return drafts[:POST_DRAFTS] if len(drafts) >= POST_DRAFTS else None
    if field == "photo_shot_list":
        shots: list[str] = []
        for v in value:
            line = clean_line(v, SHOT_MAX_CHARS)
            if line and line.casefold() not in {s.casefold() for s in shots}:
                shots.append(line)
        return shots[:SHOT_LIST_MAX] if len(shots) >= SHOT_LIST_MIN else None
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
        value = _safe_value(field, raw.get("value_list"))
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
