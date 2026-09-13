"""The operations suggestion layer: generic drafts, no identity, never able to fail an audit."""

from datetime import timedelta

from test_operations_worker import AS_OF, booking, complete
from test_profile_suggestions import FakeProvider, settings, use

from app.services.recommendations.engine import run_worker
from app.services.recommendations.suggestions import enrich, llm
from app.services.recommendations.suggestions import operations as so
from app.services.recommendations.types import EngineConfig


def weak_operations():
    """Stale requests, high no-shows, Saturday demand with no Saturday hours."""
    snapshot = complete()
    snapshot["bookings"][-1] = booking(99, "new", 30, 10, service="Root canal")
    snapshot["bookings"][-2] = booking(98, "new", 12, 10, service="Kids checkup")
    for row in snapshot["bookings"][:5]:
        row["status"] = "no_show"
    saturday = AS_OF + timedelta(days=(5 - AS_OF.weekday()) % 7 or 7)
    for row in snapshot["bookings"][21:27]:
        row["requested_for_date"] = str(saturday)
    for row in snapshot["bookings"]:
        row["customer_name"] = "Should Not Leak"
    return snapshot


def result_for(snapshot):
    return run_worker(snapshot, AS_OF, EngineConfig(), "operations")


def test_targets_are_only_findings_whose_check_suggests_a_field():
    items = so.targets(result_for(weak_operations()))
    by_rule = {}
    for item in items:
        by_rule.setdefault(item["rule"], []).append(item)
    assert set(by_rule) == {
        "requests_unanswered",
        "no_show_rate_high",
        "weekend_demand_without_hours",
    }
    assert [i["subject"] for i in by_rule["requests_unanswered"]] == ["BK-0099", "BK-0098"]


def test_followup_drafts_are_capped_to_the_oldest_requests():
    snapshot = complete()
    snapshot["bookings"] = [booking(n, "new", 40 - n, 10) for n in range(20)]
    items = so.targets(result_for(snapshot))
    followups = [i for i in items if i["rule"] == "requests_unanswered"]
    assert len(followups) == so.MAX_FOLLOWUPS
    assert followups[0]["subject"] == "BK-0000"


def test_context_carries_anonymised_stats_and_projects():
    context = so.business_context(weak_operations())
    assert context["name"] == "Brightpath Dental" and context["city"] == "Austin"
    assert context["booking_stats"]["requests"] == 40
    assert context["booking_stats"]["by_status"]["no_show"] == 6
    assert context["booking_stats"]["channels"]["phone"] == 10
    assert "Routine cleaning" in context["listed_services"]
    assert context["projects"][0]["name"] == "Brightpath Dental Group"
    assert "Should Not Leak" not in str(context)
    prompt = so.build_prompt(context, so.targets(result_for(weak_operations())))
    assert "rule=requests_unanswered subject=BK-0099" in prompt
    assert "field=reminder_plan" in prompt and "field=hours_note" in prompt
    assert "Never include a customer name" in prompt
    assert "Should Not Leak" not in prompt


async def test_enrich_attaches_validated_suggestions(monkeypatch):
    snapshot = weak_operations()
    result = result_for(snapshot)
    provider = FakeProvider(
        {
            "summary": "Two requests have waited too long. Answer them first.",
            "suggestions": [
                {
                    "rule": "requests_unanswered",
                    "subject": "BK-0099",
                    "field": "followup_message",
                    "value_text": (
                        "Sorry for the wait on your root canal request. We have times this "
                        "week. Reply with a day and time that suits and we will confirm."
                    ),
                    "reason": "The request is for a root canal.",
                    "confidence": "high",
                },
                {
                    "rule": "no_show_rate_high",
                    "field": "reminder_plan",
                    "value_list": [
                        "Send a confirmation text as soon as the visit is booked.",
                        "Send a reminder two days before with a one-tap confirm.",
                        "Send a second reminder the morning of the visit.",
                        "Call anyone unconfirmed by the evening before.",
                    ],
                    "reason": "Six of 21 settled visits were missed.",
                    "confidence": "medium",
                },
                {
                    "rule": "weekend_demand_without_hours",
                    "subject": "Saturday",
                    "field": "hours_note",
                    "value_text": "Six requests asked for a Saturday. Either open Saturday "
                    "mornings and post the hours, or remove Saturday from the form.",
                    "reason": "Six weekend requests with no Saturday hours.",
                    "confidence": "medium",
                },
                # Wrong field for the rule: dropped.
                {
                    "rule": "no_show_rate_high",
                    "field": "followup_message",
                    "value_text": "nope",
                    "reason": "x",
                    "confidence": "high",
                },
                # Duplicate for a subject already drafted: dropped.
                {
                    "rule": "requests_unanswered",
                    "subject": "BK-0099",
                    "field": "followup_message",
                    "value_text": "Second draft for the same request.",
                    "reason": "x",
                    "confidence": "high",
                },
            ],
        }
    )
    use(monkeypatch, provider)
    enriched = await enrich("operations", snapshot, result, settings())
    assert enriched["suggestions"]["status"] == "generated"
    assert enriched["suggestions"]["attached"] == 3
    assert provider.calls[0][1] is so.RESPONSE_SCHEMA
    assert enriched["summary"]["text"].startswith("Two requests")
    by_key = {(i["rule"], i["subject"]): i for i in enriched["items"]}
    followup = by_key[("requests_unanswered", "BK-0099")]["suggestion"]
    assert followup["field"] == "followup_message" and followup["value"].startswith("Sorry")
    assert by_key[("requests_unanswered", "BK-0099")]["explanation_source"] == (
        "deterministic+generated"
    )
    assert by_key[("requests_unanswered", "BK-0098")]["suggestion"] is None
    assert len(by_key[("no_show_rate_high", "")]["suggestion"]["value"]) == 4
    assert by_key[("weekend_demand_without_hours", "Saturday")]["suggestion"]["field"] == (
        "hours_note"
    )
    assert enriched["evaluations"] == result_for(snapshot)["evaluations"]


async def test_enrich_drops_drafts_with_names_contact_details_or_too_few_steps(monkeypatch):
    snapshot = weak_operations()
    result = result_for(snapshot)
    provider = FakeProvider(
        {
            "summary": "",
            "suggestions": [
                {
                    "rule": "requests_unanswered",
                    "subject": "BK-0099",
                    "field": "followup_message",
                    "value_text": "Hi Matthew, sorry for the wait on your root canal.",
                    "reason": "x",
                    "confidence": "high",
                },
                {
                    "rule": "requests_unanswered",
                    "subject": "BK-0098",
                    "field": "followup_message",
                    "value_text": "Sorry for the wait. Call us on 512-555-0199 to confirm.",
                    "reason": "x",
                    "confidence": "high",
                },
                {
                    "rule": "no_show_rate_high",
                    "field": "reminder_plan",
                    "value_list": ["Send a reminder.", "Email https://example.org/confirm"],
                    "reason": "x",
                    "confidence": "high",
                },
                {
                    "rule": "weekend_demand_without_hours",
                    "subject": "Saturday",
                    "field": "hours_note",
                    "value_text": "Open Saturdays. " * 60,
                    "reason": "x",
                    "confidence": "low",
                },
            ],
        }
    )
    use(monkeypatch, provider)
    enriched = await enrich("operations", snapshot, result, settings())
    assert enriched["suggestions"]["attached"] == 1
    by_key = {(i["rule"], i["subject"]): i for i in enriched["items"]}
    assert by_key[("requests_unanswered", "BK-0099")]["suggestion"] is None
    assert by_key[("requests_unanswered", "BK-0098")]["suggestion"] is None
    assert by_key[("no_show_rate_high", "")]["suggestion"] is None
    note = by_key[("weekend_demand_without_hours", "Saturday")]["suggestion"]["value"]
    assert len(note) <= so.HOURS_NOTE_MAX_CHARS
    # An empty model summary falls back to the deterministic one.
    assert enriched["summary"]["source"] == "deterministic"


def test_followup_over_the_cap_is_trimmed_on_a_word():
    value = so._safe_value("followup_message", "word " * 100)
    assert value and len(value) <= so.FOLLOWUP_MAX_CHARS and not value.endswith(" ")
    assert so._safe_value("reminder_plan", "not a list") is None
    assert so._safe_value("reminder_plan", ["a"] * 7) == ["a"] * 5


async def test_enrich_records_failure_and_keeps_findings(monkeypatch):
    use(monkeypatch, FakeProvider(error=llm.SuggestionError("Vertex AI returned 429: quota")))
    snapshot = weak_operations()
    enriched = await enrich("operations", snapshot, result_for(snapshot), settings())
    assert enriched["suggestions"]["status"] == "failed"
    assert "429" in enriched["suggestions"]["error"]
    assert enriched["items"] and all(i["suggestion"] is None for i in enriched["items"])
    assert enriched["summary"]["source"] == "deterministic"
    assert "Fix first" in enriched["summary"]["text"]


async def test_enrich_skips_when_disabled_or_nothing_to_draft(monkeypatch):
    snapshot = weak_operations()
    off = await enrich(
        "operations", snapshot, result_for(snapshot), settings(suggestions_enabled=False)
    )
    assert off["suggestions"]["status"] == "skipped"
    use(monkeypatch, FakeProvider({"suggestions": []}))
    clean = await enrich("operations", complete(), result_for(complete()), settings())
    assert clean["suggestions"]["status"] == "skipped"
    assert "passed" in clean["summary"]["text"]
