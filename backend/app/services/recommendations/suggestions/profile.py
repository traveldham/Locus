"""Draft suggestions for the profile fields the audit found missing or weak.

The deterministic worker decides what failed. This module asks Gemini for a draft of
the fields those checks mark as `suggests`, using the whole profile and the operator's
own project description as context so the draft is about this business, not a generic
one. Facts only the business knows are never drafted.
"""

from datetime import UTC, datetime

from app.services.recommendations.categories.profile import (
    CHECKS,
    answered,
    attribute_name,
    truthy,
)
from app.services.recommendations.types import Suggestion

# Which suggestion fields may be drafted, and what shape the value takes.
FIELD_SHAPES = {
    "description": "a single string, at most 750 characters, no URLs, no promotions",
    "additional_categories": "a list of Google Business Profile category names",
    "attributes": (
        "an object mapping attribute names from the catalog list to true or false, "
        "only for attributes the business context makes likely; leave out anything unsure"
    ),
    "title": "a single string: the real-world business name without added keywords",
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
                    "value_map": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "name": {"type": "STRING"},
                                "value": {"type": "BOOLEAN"},
                            },
                            "required": ["name", "value"],
                        },
                    },
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
    categories = rows("categories")
    attributes = rows("attributes")
    hours = rows("hours")
    category = str(loc.get("primary_category_display") or "").casefold()
    catalog = [
        r["attribute_name"]
        for r in snapshot.get("catalog", [])
        if str(r.get("applies_to_category") or "").casefold() == category
    ]
    answered_yes = sorted(attribute_name(r) for r in attributes if truthy(r) is True)
    answered_no = sorted(attribute_name(r) for r in attributes if truthy(r) is False)
    unanswered = sorted(
        n for n in catalog if not any(attribute_name(r) == n and answered(r) for r in attributes)
    )
    return {
        "name": loc.get("title"),
        "primary_category": loc.get("primary_category_display"),
        "additional_categories": [
            r.get("display_name") for r in categories if not r.get("is_primary")
        ],
        "city": loc.get("locality"),
        "state": loc.get("administrative_area"),
        "country": loc.get("region_code"),
        "website": loc.get("website_uri"),
        "description": loc.get("description"),
        "opening_date": loc.get("opening_date"),
        "hours": sorted(
            f"{r.get('open_day')} {r.get('open_hour'):02d}:{r.get('open_minute', 0):02d}"
            f"-{r.get('close_hour'):02d}:{r.get('close_minute', 0):02d}"
            for r in hours
        ),
        "attributes_yes": answered_yes,
        "attributes_no": answered_no,
        "attributes_unanswered": unanswered,
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
    return f"""You draft improvements for one Google Business Profile. You are given the
profile as stored, the operator's own description of the business (projects), and the
audit findings that need a draft. Return one suggestion per finding.

Rules you must follow:
- Draft only for the field named in each finding. Never invent a phone number, street
  address, opening hours, opening date or website; if asked, say so in the reason and
  give an empty value.
- Base every draft on the stored profile and the projects context. Do not add services
  the context does not support. If the context is too thin, lower the confidence.
- description: plain language, what the location offers and who it serves, at most 750
  characters, no URLs, no phone numbers, no promotions or prices, no keyword lists.
- additional_categories: only real Google Business Profile categories that the
  services in the context justify, excluding ones already set.
- attributes: only names from attributes_unanswered, each true or false, and only when
  the context makes the answer likely. Skip anything unsure.
- title: the real-world name only, no category or city words appended.
- Put the value in exactly one of value_text, value_list or value_map, matching the
  field's shape:
{shapes}
- reason: one sentence saying what in the context supports the draft.
- confidence: high when the context states it, medium when it is a reasonable
  inference, low when it is a guess a manager must check.

- summary: three to five sentences for the location manager, in plain language, built
  only from the findings listed below (all of them, not only those needing a draft).
  Say what is wrong and why it matters to a customer, what to do first, and what is
  already fine. No scores, no percentages, no promises about rankings or revenue.

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
        text = "Every profile check that could run passed. Nothing needs attention right now."
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


def apply(result: dict, response: dict, source: str, model: str) -> int:
    """Attach validated suggestions to the findings they answer. Returns how many."""
    by_key = {(i["rule"], i.get("subject") or ""): i for i in targets(result)}
    stamped = datetime.now(UTC).isoformat()
    attached = 0
    summary = str(response.get("summary") or "").strip()
    if summary:
        result["summary"] = {
            "text": summary[:1200],
            "source": source,
            "model": model,
            "generated_at": stamped,
        }
    for raw in response.get("suggestions", []):
        item = by_key.get((raw.get("rule"), raw.get("subject") or ""))
        if item is None:
            continue
        field = CHECKS[item["rule"]]["suggests"]
        if raw.get("field") != field:
            continue
        value: str | list[str] | dict
        if raw.get("value_map"):
            value = {
                str(e["name"]): bool(e["value"])
                for e in raw["value_map"]
                if isinstance(e, dict) and "name" in e and "value" in e
            }
        elif raw.get("value_list"):
            value = [str(v) for v in raw["value_list"]]
        else:
            value = str(raw.get("value_text") or "").strip()
        if not value:
            continue
        if field == "description" and isinstance(value, str) and len(value) > 750:
            value = value[:750].rsplit(" ", 1)[0]
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
        attached += 1
    return attached
