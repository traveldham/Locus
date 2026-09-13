"""The whole-audit summary shown on the Overview: all six workers in a few sentences.

Written once per audit after the six workers have reported, from their own summaries,
the category scores and the top priorities. Never from raw data: the workers already
decided what matters. Falls back to a deterministic paragraph when no model answers.
"""

from datetime import UTC, datetime

from app.core.config import Settings, get_settings
from app.services.recommendations.suggestions.llm import (
    SuggestionError,
    provider_from_settings,
)

POINT = {
    "type": "OBJECT",
    "properties": {"category": {"type": "STRING"}, "text": {"type": "STRING"}},
    "required": ["category", "text"],
}
RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "summary": {"type": "STRING"},
        "strengths": {"type": "ARRAY", "items": POINT},
        "attention": {"type": "ARRAY", "items": POINT},
    },
    "required": ["summary", "strengths", "attention"],
}
MAX_POINTS = 4

BANNED = ("revenue", "guarantee", "rank #1", "rankings will")


def build_prompt(report: dict) -> str:
    location = report["location"]
    health = location["health"]
    by_key = {item["key"]: item for item in report["items"]}
    categories = "\n".join(
        f"- {c['label']}: "
        + (
            f"{c['score']}/100, {c['issues']} issue{'s' if c['issues'] != 1 else ''}"
            if c["score"] is not None
            else "not evaluated"
        )
        for c in health["categories"]
    )
    summaries = "\n".join(
        f"- {key}: {value['text']}" for key, value in (location.get("summaries") or {}).items()
    )
    priorities = "\n".join(
        f"- [{by_key[k]['severity']}] {by_key[k]['title']}: {by_key[k]['why']}"
        + (" (a draft is ready)" if by_key[k].get("suggestion") else "")
        for k in location.get("priorities", [])
        if k in by_key
    )
    changes = location.get("changes") or {}
    fixed, new = len(changes.get("fixed", [])), len(changes.get("new", []))
    if changes.get("first_audit", True):
        since_last = "This is the first audit of this profile; do not mention previous audits."
    elif not fixed and not new:
        since_last = "Nothing changed since the last audit; do not mention it."
    else:
        since_last = f"Since the last audit: {fixed} checks fixed, {new} new problems."
    drafts = sum(1 for item in report["items"] if item.get("suggestion"))
    severity = {}
    for item in report["items"]:
        severity[item["severity"]] = severity.get(item["severity"], 0) + 1
    counts = ", ".join(f"{n} {level}" for level, n in severity.items())
    return f"""You write the opening paragraph of a Google Business Profile audit for the
manager of one location: {location["name"]}. Health score {health["score"]} of 100
({health["grade"]}), {health["issues"]} findings across six categories ({counts}).
{since_last} {drafts} findings already have a draft fix prepared; say drafts are
ready without giving the number.

Return three things, all in plain language for a busy manager, using only the material
below. No scores or percentages, no promises about rankings or revenue.

- summary: three to five short sentences covering the whole audit, not one category:
  the one or two areas that most need attention and why a customer would notice, what
  to do first (mention when a draft is ready to use), what changed since the last audit
  if this is not the first, and which areas are in good shape.
- strengths: up to {MAX_POINTS} things that are genuinely working, one sentence each,
  with the category key (one of profile, reputation, visibility, operations,
  performance, content). Each must restate something that category's own audit text
  below says is fine; never attribute a fact to the wrong category.
- attention: up to {MAX_POINTS} things that need fixing, most important first, one
  sentence each with the category key. Each must come from a listed finding, and each
  must be a different kind of problem: never list several instances of the same check
  (say "four appointment requests have waited over a month" once, not four times), and
  cover different categories where the findings allow.

Category scores:
{categories}

What each category's audit said:
{summaries}

Top priorities:
{priorities}
"""


def fallback_points(report: dict) -> tuple[list[dict], list[dict]]:
    """Strengths and attention points written by code from scores and findings."""
    location = report["location"]
    health = location["health"]
    scored = [c for c in health["categories"] if c["score"] is not None]
    strengths = [
        {
            "category": c["category"],
            "text": f"{c['label']}: {c['checks_passed']} of "
            f"{c['checks_passed'] + c['checks_failed']} checks passed.",
        }
        for c in sorted(scored, key=lambda c: -c["score"])
        if c["score"] >= 85
    ][:MAX_POINTS]
    by_key = {item["key"]: item for item in report["items"]}
    attention = [
        {"category": by_key[k]["category"], "text": by_key[k]["title"].rstrip(".") + "."}
        for k in location.get("priorities", [])
        if k in by_key
    ][:MAX_POINTS]
    return strengths, attention


def fallback_summary(report: dict) -> dict:
    location = report["location"]
    health = location["health"]
    scored = [c for c in health["categories"] if c["score"] is not None]
    weak = sorted(scored, key=lambda c: c["score"])[:2]
    strong = [c for c in scored if c["score"] >= 90]
    by_key = {item["key"]: item for item in report["items"]}
    first = next((by_key[k] for k in location.get("priorities", []) if k in by_key), None)
    strengths, attention = fallback_points(report)
    parts = []
    if weak:
        parts.append(
            "Most attention is needed on " + " and ".join(c["label"].lower() for c in weak) + "."
        )
    if first:
        parts.append(f"Start with: {first['title'].rstrip('.')}.")
    if strong:
        parts.append(
            ", ".join(c["label"] for c in strong)
            + (" is" if len(strong) == 1 else " are")
            + " in good shape."
        )
    if not parts:
        parts.append("No category could be evaluated yet.")
    return {
        "text": " ".join(parts),
        "strengths": strengths,
        "attention": attention,
        "source": "deterministic",
        "model": None,
        "generated_at": datetime.now(UTC).isoformat(),
    }


def clean_points(raw, categories: set[str]) -> list[dict]:
    """Validated points, at most two per category so one noisy worker cannot fill it."""
    points: list[dict] = []
    per_category: dict[str, int] = {}
    for entry in raw or []:
        if not isinstance(entry, dict):
            continue
        category = str(entry.get("category") or "").strip().lower()
        text = str(entry.get("text") or "").strip()
        if category not in categories or not text or any(w in text.lower() for w in BANNED):
            continue
        if per_category.get(category, 0) >= 2:
            continue
        points.append({"category": category, "text": text[:240]})
        per_category[category] = per_category.get(category, 0) + 1
        if len(points) == MAX_POINTS:
            break
    return points


async def overall_summary(report: dict, settings: Settings | None = None) -> dict:
    """Never raises: a model answer when possible, the fallback otherwise."""
    settings = settings or get_settings()
    provider = provider_from_settings(settings) if settings.suggestions_enabled else None
    if provider is None or not report["items"]:
        return fallback_summary(report)
    try:
        response = await provider.generate_json(build_prompt(report), RESPONSE_SCHEMA)
    except SuggestionError:
        return fallback_summary(report)
    text = str(response.get("summary") or "").strip()
    if not text or any(word in text.lower() for word in BANNED):
        return fallback_summary(report)
    health_categories = report["location"]["health"]["categories"]
    categories = {c["category"] for c in health_categories}
    # A strength may only be claimed for a category whose own checks mostly passed.
    doing_well = {c["category"] for c in health_categories if (c["score"] or 0) >= 75}
    strengths = clean_points(response.get("strengths"), doing_well)
    attention = clean_points(response.get("attention"), categories)
    fallback_strengths, fallback_attention = fallback_points(report)
    return {
        "text": text[:1200],
        "strengths": strengths or fallback_strengths,
        "attention": attention or fallback_attention,
        "source": provider.name,
        "model": provider.model,
        "generated_at": datetime.now(UTC).isoformat(),
    }
