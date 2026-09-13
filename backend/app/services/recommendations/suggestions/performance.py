"""Draft an investigation plan for each performance decline the audit found.

The deterministic worker decides what fell. This module asks the model for an
ordered checklist of three to five concrete things to verify, grounded in the stored
profile (hours, categories, website, status) and the operator's projects, plus a short
summary. Never a cause, never a promise: the plan says what to look at first.
"""

import re
from datetime import UTC, datetime

from app.services.recommendations.categories.performance import CHECKS, card
from app.services.recommendations.suggestions.matching import resolve_target
from app.services.recommendations.types import Suggestion

# Which field each check may have drafted, for matching a reply back to its finding.
SUGGESTS = {rule: spec["suggests"] for rule, spec in CHECKS.items() if spec.get("suggests")}

PLAN_MIN, PLAN_MAX, ITEM_MAX_CHARS = 3, 5, 160

FIELD_SHAPES = {
    "investigation_plan": (
        "a list of 3 to 5 short checks, each one sentence under 160 characters, ordered "
        "from most to least likely cause, no URLs, no phone numbers"
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

# Links, e-mail addresses, phone numbers, and promises the audit never makes.
BANNED = re.compile(
    r"(?:https?://|www\.|\b\S+@\S+\.\S+\b|\+?\d[\d\s().-]{7,}\d"
    r"|\b(?:revenue|guarantee[ds]?|rankings?)\b)",
    re.I,
)


def targets(result: dict) -> list[dict]:
    """The findings a plan may be drafted for: every check that names a field."""
    return [
        item for item in result.get("items", []) if CHECKS.get(item["rule"], {}).get("suggests")
    ]


def business_context(snapshot: dict) -> dict:
    loc = snapshot["locations"][0]
    location_id = loc["id"]
    rows = lambda source: [  # noqa: E731 - tiny local helper
        r for r in snapshot.get(source, []) if r.get("location_id") == location_id
    ]
    hours = rows("hours")
    visual = card(snapshot)
    metrics = visual.get("metrics", {})
    return {
        "name": loc.get("title"),
        "primary_category": loc.get("primary_category_display"),
        "additional_categories": [
            r.get("display_name") for r in rows("categories") if not r.get("is_primary")
        ],
        "city": loc.get("locality"),
        "state": loc.get("administrative_area"),
        "open_status": loc.get("open_status"),
        "verified": loc.get("has_voice_of_merchant"),
        "has_pending_edits": loc.get("has_pending_edits"),
        "phone_present": bool(loc.get("phone_primary")),
        "website": loc.get("website_uri"),
        "hours_days": sorted({str(r.get("open_day") or "").title() for r in hours}),
        "hours_count": len(hours),
        "window": visual.get("window"),
        "days_with_data": visual.get("days_with_data"),
        "metric_deltas": {
            name: {
                "current": m.get("current"),
                "previous": m.get("previous"),
                "change": m.get("change"),
            }
            for name, m in metrics.items()
        },
        "maps_share": visual.get("maps_share"),
        "mobile_share": visual.get("mobile_share"),
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
    return f"""You help a location manager investigate a change in Google Business Profile
performance. You are given the stored profile, the operator's own description of the
business (projects), the four-week metric deltas, and the audit findings that need a
plan. Return one investigation plan per finding.

Rules you must follow:
- A plan is a checklist to verify, in order of likelihood, not a diagnosis. Never state
  a cause as fact. Never promise more calls, customers, rankings or revenue.
- Ground each step in the context: refer to the stored hours, categories, website,
  open status, pending edits, verification and the metric deltas by name. If the
  website is missing, say to add it rather than to check it. If impressions held while
  one action fell, point at that action's button or destination first.
- Usual causes to draw on, in rough order: profile state (suspension, temporary
  closure, hours or holiday hours changed, an edit reverted), identity changes
  (category, name, address or pin), the website or phone number changed or broken, a
  new or improved competitor, seasonal demand across the area, and Google restating
  a day's data.
- Put the value in value_list, matching the field's shape:
{shapes}
- reason: one short sentence naming the stored fact or delta that shaped the order.
- confidence: high when the context points clearly at one step, medium for a
  reasonable order, low when it is a generic checklist.

- summary: two or three short sentences for the location manager, in plain language,
  built only from the findings listed below. Say what changed, what to check first, and
  what is holding steady. No scores, no percentages beyond those in the findings, no
  promises about rankings or revenue.

Profile and context (JSON):
{context}

All findings from the audit:
{all_findings}

Findings needing a plan:
{asks}
"""


def fallback_summary(result: dict) -> dict:
    """A summary written by code, used when no model answered."""
    items = result.get("items", [])
    if not items:
        text = (
            "Impressions and actions are holding steady against the four weeks before. "
            "Nothing needs attention right now."
        )
    else:
        by_severity = {"critical": [], "warning": [], "notice": []}
        for item in items:
            by_severity[item["severity"]].append(item["title"])
        parts = []
        if by_severity["critical"]:
            parts.append("Look into first: " + "; ".join(by_severity["critical"][:3]).lower() + ".")
        if by_severity["warning"]:
            parts.append("Then: " + "; ".join(by_severity["warning"][:3]).lower() + ".")
        if by_severity["notice"]:
            parts.append(
                f"{len(by_severity['notice'])} smaller "
                + ("change" if len(by_severity["notice"]) == 1 else "changes")
                + " to keep an eye on."
            )
        parts.append("These are measured changes, not causes; check before acting.")
        text = " ".join(parts)
    return {
        "text": text,
        "source": "deterministic",
        "model": None,
        "generated_at": datetime.now(UTC).isoformat(),
    }


def _safe_plan(value) -> list[str] | None:
    """Enforce the shape in code: 3 to 5 items, short, no links, phones or promises."""
    if not isinstance(value, list):
        return None
    steps: list[str] = []
    for raw in value:
        if not isinstance(raw, str):
            continue
        step = " ".join(raw.split()).strip()
        if not step or len(step) > ITEM_MAX_CHARS or BANNED.search(step):
            continue
        if step.casefold() in {s.casefold() for s in steps}:
            continue
        steps.append(step)
    if len(steps) < PLAN_MIN:
        return None
    return steps[:PLAN_MAX]


def apply(result: dict, response: dict, source: str, model: str, context: dict) -> int:
    """Attach validated plans to the findings they answer. Returns how many."""
    by_key = {(i["rule"], i.get("subject") or ""): i for i in targets(result)}
    stamped = datetime.now(UTC).isoformat()
    attached = 0
    seen: set[tuple[str, str]] = set()
    summary = str(response.get("summary") or "").strip()
    if summary and not BANNED.search(summary):
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
        plan = _safe_plan(raw.get("value_list"))
        if not plan:
            continue
        item["suggestion"] = Suggestion(
            field=field,
            value=plan,
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
