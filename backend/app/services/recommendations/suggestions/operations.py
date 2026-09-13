"""Draft the operational follow-ups the operations audit calls for.

The deterministic worker decides what failed. This module asks the model for a generic
follow-up message for requests left waiting, a reminder plan when no-shows run high, and
a note on weekend hours when weekend demand exists, plus a plain-language summary. The
booking stats it sees are anonymised counts; no customer name or contact detail ever
reaches the prompt, and none may appear in a draft.
"""

import re
from collections import Counter
from datetime import UTC, datetime

from app.services.recommendations.categories.operations import (
    CHECKS,
    lead_days,
    project_services,
    status_of,
)
from app.services.recommendations.suggestions.matching import resolve_target
from app.services.recommendations.types import Suggestion

# Which field each check may have drafted, for matching a reply back to its finding.
SUGGESTS = {rule: spec["suggests"] for rule, spec in CHECKS.items() if spec.get("suggests")}

FOLLOWUP_MAX_CHARS = 300
HOURS_NOTE_MAX_CHARS = 400
REMINDER_STEPS = (3, 5)
# The oldest waiting requests get a draft; a long backlog would otherwise swamp the call.
MAX_FOLLOWUPS = 10

FIELD_SHAPES = {
    "followup_message": (
        "a single string under 300 characters: a message the front desk can send to the "
        "customer who asked for the service named in the finding, apologising for the wait, "
        "naming the service, and asking them to confirm a time. No customer name, no "
        "phone number, no email, no URL, no prices."
    ),
    "reminder_plan": (
        "a list of 3 to 5 concrete steps the front desk can run to cut no-shows: what to "
        "send, when, and what to do when nobody confirms. No names, no contact details."
    ),
    "hours_note": (
        "a single string under 400 characters for the manager: what the weekend demand "
        "shows and the options (open that day and post hours, or stop offering it on the "
        "booking form). No names, no contact details, no URL."
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
    """The findings a suggestion may be drafted for, one per rule and subject."""
    chosen, followups = [], 0
    for item in result.get("items", []):
        field = CHECKS.get(item["rule"], {}).get("suggests")
        if not field:
            continue
        if field == "followup_message":
            if followups >= MAX_FOLLOWUPS:
                continue
            followups += 1
        chosen.append(item)
    return chosen


def business_context(snapshot: dict) -> dict:
    loc = snapshot["locations"][0]
    location_id = loc["id"]
    rows = [r for r in snapshot.get("bookings", []) if r.get("location_id") == location_id]
    hours = [r for r in snapshot.get("hours", []) if r.get("location_id") == location_id]
    statuses = Counter(status_of(r) for r in rows)
    services = Counter(str(r.get("service")).strip() for r in rows if r.get("service"))
    channels = Counter(str(r.get("booking_source")) for r in rows if r.get("booking_source"))
    leads = [lead for r in rows if (lead := lead_days(r)) is not None and lead >= 0]
    return {
        "name": loc.get("title"),
        "primary_category": loc.get("primary_category_display"),
        "city": loc.get("locality"),
        "hours": sorted(
            f"{r.get('open_day')} {int(r.get('open_hour') or 0):02d}:"
            f"{int(r.get('open_minute') or 0):02d}-{int(r.get('close_hour') or 0):02d}:"
            f"{int(r.get('close_minute') or 0):02d}"
            for r in hours
            if (r.get("hours_type") or "REGULAR") == "REGULAR"
        ),
        "booking_stats": {
            "requests": len(rows),
            "by_status": dict(statuses),
            "services_requested": dict(services.most_common(10)),
            "channels": dict(channels),
            "median_lead_days": sorted(leads)[len(leads) // 2] if leads else None,
        },
        "listed_services": project_services(snapshot),
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
    return f"""You draft practical front-desk follow-ups for one local business, based on its
appointment requests. You are given the business, its hours, anonymised booking
statistics, the operator's own description (projects), and the audit findings that need
a draft. Return one suggestion per finding.

Rules you must follow:
- Draft only for the field named in each finding.
- Never include a customer name, a phone number, an email address, a URL, or a price.
  You are never given a customer's identity and must not invent one.
- followup_message: warm, short, from the business to the customer, under 300
  characters; apologise for the wait, name the service from the finding, ask them to
  reply with a time that suits. Generic enough to send as is.
- reminder_plan: 3 to 5 steps, each one sentence, concrete: what is sent, when, and
  what happens when nobody confirms.
- hours_note: for the manager, under 400 characters, plain language, the trade-off.
- Put the value in value_text for a string field or value_list for a list field:
{shapes}
- reason: one short sentence naming the exact statistic or project detail behind the draft.
- confidence: high when the context states it, medium when it is a reasonable
  inference, low when it is a guess a manager must check.

- summary: two or three short sentences for the location manager, in plain language, built
  only from the findings listed below (all of them, not only those needing a draft).
  Say what is wrong and why it matters to a customer, what to do first, and what is
  already fine. No scores, no percentages, no promises about rankings or revenue.

Business and context (JSON):
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
            "Every operations check that could run passed. Requests are being answered "
            "and visits are being kept."
        )
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
# A capitalised word after a greeting reads as a name; the drafts must stay generic.
GREETING_NAME = re.compile(r"\b(?i:hi|hello|dear|hey)\s+[A-Z][a-z]+\b")


def _clean_text(value, cap: int) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value or CONTACT.search(value) or GREETING_NAME.search(value):
        return None
    if len(value) > cap:
        value = value[:cap].rsplit(" ", 1)[0].rstrip(",;:")
    return value or None


def _safe_value(field: str, value):
    """Enforce constraints that must not depend on the model following the prompt."""
    if field == "followup_message":
        return _clean_text(value, FOLLOWUP_MAX_CHARS)
    if field == "hours_note":
        return _clean_text(value, HOURS_NOTE_MAX_CHARS)
    if field == "reminder_plan":
        if not isinstance(value, list):
            return None
        steps = [s for s in (_clean_text(v, 200) for v in value) if s]
        low, high = REMINDER_STEPS
        if len(steps) < low:
            return None
        return steps[:high]
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
        value = _safe_value(field, value)
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
