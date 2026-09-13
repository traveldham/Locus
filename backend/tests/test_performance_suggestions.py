"""The performance suggestion layer: an investigation plan per decline, validated in code."""

from datetime import timedelta

from test_performance_worker import AS_OF, LATEST, scale_current, steady
from test_profile_suggestions import FakeProvider, settings, use

from app.services.recommendations.categories import performance
from app.services.recommendations.engine import run_worker
from app.services.recommendations.suggestions import enrich
from app.services.recommendations.suggestions import performance as sp
from app.services.recommendations.types import EngineConfig


def falling() -> dict:
    snapshot = steady()
    scale_current(snapshot, performance.IMPRESSIONS, 0.8)
    scale_current(snapshot, ("call_clicks",), 0.5)
    dropped = {(LATEST - timedelta(days=i)).isoformat() for i in (2, 4, 6)}
    snapshot["performance"] = [r for r in snapshot["performance"] if r["date"] not in dropped]
    snapshot["projects"] = [
        {
            "id": "p1",
            "name": "Brightpath Dental Group",
            "website_url": "https://example.org",
            "description": "Family dental group across Texas.",
            "services": ["Cleanings", "Whitening"],
            "slug": "bdg",
            "status": "active",
        }
    ]
    snapshot["hours"] = [
        {"id": f"h-{d}", "location_id": "loc-1", "open_day": d, "hours_type": "REGULAR"}
        for d in ("MONDAY", "TUESDAY")
    ]
    return snapshot


def result_for(snapshot):
    return run_worker(snapshot, AS_OF, EngineConfig(), "performance")


def plan(rule, *steps, field="investigation_plan", confidence="medium", subject=""):
    return {
        "rule": rule,
        "subject": subject,
        "field": field,
        "value_list": list(steps),
        "reason": "Impressions fell while calls fell harder.",
        "confidence": confidence,
    }


def test_targets_are_declines_not_data_gaps():
    rules = {i["rule"] for i in sp.targets(result_for(falling()))}
    assert {"impressions_decline", "calls_decline"} <= rules
    assert "data_gaps" not in rules


def test_context_carries_profile_facts_projects_and_deltas():
    context = sp.business_context(falling())
    assert context["name"] == "Brightpath Dental" and context["website"]
    assert context["hours_days"] == ["Monday", "Tuesday"]
    assert context["projects"][0]["services"] == ["Cleanings", "Whitening"]
    assert context["metric_deltas"]["calls"]["change"] < -0.4
    assert context["metric_deltas"]["impressions"]["change"] < -0.15
    assert context["window"]["current_end"] == LATEST.isoformat()
    prompt = sp.build_prompt(context, sp.targets(result_for(falling())))
    assert "rule=calls_decline" in prompt and "Whitening" in prompt
    assert "Never promise more calls" in prompt


async def test_enrich_attaches_validated_plans(monkeypatch):
    snapshot = falling()
    result = result_for(snapshot)
    provider = FakeProvider(
        {
            "summary": "Impressions and calls both fell. Check the phone number first.",
            "suggestions": [
                plan(
                    "calls_decline",
                    "Dial the stored phone number from a mobile and confirm it rings through.",
                    "Check whether the number on the profile was changed in the last month.",
                    "Compare Monday and Tuesday hours with the door: calls fall when hours hide.",
                    "  Look for  a pending edit on the profile.  ",
                    "Look for a pending edit on the profile.",
                    "Sixth step that should be trimmed off.",
                ),
                # Wrong field: dropped.
                plan("impressions_decline", "a", "b", "c", field="description"),
                # Unknown rule: dropped.
                plan("data_gaps", "a", "b", "c"),
            ],
        }
    )
    use(monkeypatch, provider)
    enriched = await enrich("performance", snapshot, result, settings())
    assert enriched["suggestions"]["status"] == "generated"
    assert enriched["suggestions"]["attached"] == 1
    assert provider.calls[0][1] is sp.RESPONSE_SCHEMA
    by_rule = {i["rule"]: i for i in enriched["items"]}
    calls = by_rule["calls_decline"]["suggestion"]
    assert calls["field"] == "investigation_plan" and len(calls["value"]) == 5
    assert calls["value"][3] == "Look for a pending edit on the profile."
    assert by_rule["calls_decline"]["explanation_source"] == "deterministic+generated"
    assert by_rule["impressions_decline"]["suggestion"] is None
    assert by_rule["data_gaps"]["suggestion"] is None
    assert enriched["summary"]["text"].startswith("Impressions and calls")
    assert enriched["evaluations"] == result_for(snapshot)["evaluations"]


async def test_enrich_drops_plans_that_break_the_rules(monkeypatch):
    snapshot = falling()
    result = result_for(snapshot)
    provider = FakeProvider(
        {
            "summary": "Fix this and revenue will double.",
            "suggestions": [
                # Too short once the bad items are removed.
                plan(
                    "calls_decline",
                    "Call 512-555-0199 to test the line.",
                    "Open https://example.org on a phone.",
                    "This will improve your rankings quickly.",
                    "Confirm the number on the profile.",
                ),
                # One item far over the length cap.
                plan(
                    "impressions_decline",
                    "x" * 200,
                    "Check the category.",
                    "Check the hours.",
                    "Check the pin.",
                ),
            ],
        }
    )
    use(monkeypatch, provider)
    enriched = await enrich("performance", snapshot, result, settings())
    by_rule = {i["rule"]: i for i in enriched["items"]}
    assert by_rule["calls_decline"]["suggestion"] is None
    assert by_rule["impressions_decline"]["suggestion"]["value"] == [
        "Check the category.",
        "Check the hours.",
        "Check the pin.",
    ]
    # A summary that promises revenue is replaced by the deterministic one.
    assert enriched["summary"]["source"] == "deterministic"


def test_fallback_summary_is_deterministic_and_honest():
    text = sp.fallback_summary(result_for(falling()))["text"]
    assert "fall in calls" in text and "not causes" in text
    assert sp.fallback_summary({"items": []})["text"].startswith("Impressions and actions")


async def test_steady_profile_skips_the_model(monkeypatch):
    use(monkeypatch, FakeProvider({"summary": "", "suggestions": []}))
    enriched = await enrich("performance", steady(), result_for(steady()), settings())
    assert enriched["suggestions"]["status"] == "skipped"
    assert enriched["summary"]["source"] == "deterministic"
