"""The content suggestion layer: post drafts and shot lists, checked in code."""

from test_content_worker import AS_OF, complete
from test_profile_suggestions import FakeProvider, settings, use

from app.services.recommendations.engine import run_worker
from app.services.recommendations.suggestions import content as sc
from app.services.recommendations.suggestions import enrich
from app.services.recommendations.types import EngineConfig


def weak_content():
    snapshot = complete()
    snapshot["media"][0]["photo_count"] = 6
    snapshot["media"][0]["interior_photo_count"] = 0
    snapshot["media"][0]["video_count"] = 0
    snapshot["posts"] = snapshot["posts"][:3]
    for row in snapshot["posts"]:
        row["published_on"] = "2026-07-01"
        row["post_type"] = "standard"
    return snapshot


def result_for(snapshot):
    return run_worker(snapshot, AS_OF, EngineConfig(), "content")


def shots(n=6):
    return [f"Shot {i}: treatment room {i} with the chair and window in frame" for i in range(n)]


def test_targets_are_only_findings_whose_check_suggests_content():
    items = sc.targets(result_for(weak_content()))
    by = {(i["rule"], i["subject"]) for i in items}
    assert ("photos_few", "") in by and ("photo_type_empty", "interior") in by
    assert ("posts_none_recent", "") in by and ("posts_sparse", "") in by
    assert not any(rule == "video_missing" for rule, _ in by)


def test_context_carries_profile_media_posts_and_projects():
    context = sc.business_context(weak_content())
    assert context["name"] == "Brightpath Dental" and context["city"] == "Austin"
    assert context["media"]["interior_photo_count"] == 0
    assert context["recent_posts"][0]["type"] == "standard"
    assert context["recent_posts"][0]["cta"] == "book"
    assert context["projects"][0]["services"] == [
        "Routine cleaning",
        "Teeth whitening",
        "Invisalign",
    ]
    prompt = sc.build_prompt(context, sc.targets(result_for(weak_content())))
    assert "Invisalign" in prompt and "rule=photo_type_empty subject=interior" in prompt
    assert "Never mention a phone number" in prompt and "ALL CAPS" in prompt


async def test_enrich_attaches_validated_drafts(monkeypatch):
    snapshot = weak_content()
    result = result_for(snapshot)
    provider = FakeProvider(
        {
            "summary": "Add interior photos and start posting again.",
            "suggestions": [
                {
                    "rule": "posts_none_recent",
                    "field": "post_drafts",
                    "value_list": [
                        "Routine cleanings keep small problems small. Our hygienists take "
                        "the time to explain what they see. (Button: Book)",
                        "Whitening consultation this month: ask about brightening your "
                        "smile before the holidays. Manager to add the dates. (Button: Call)",
                    ],
                    "reason": "Routine cleaning and teeth whitening are listed services.",
                    "confidence": "high",
                },
                {
                    "rule": "photo_type_empty",
                    "subject": "interior",
                    "field": "photo_shot_list",
                    "value_list": shots(7),
                    "reason": "The interior photo count is zero.",
                    "confidence": "high",
                },
                # Wrong field for the rule: dropped.
                {
                    "rule": "posts_sparse",
                    "field": "photo_shot_list",
                    "value_list": shots(),
                    "reason": "x",
                    "confidence": "high",
                },
                # Not a target: dropped.
                {
                    "rule": "video_missing",
                    "field": "post_drafts",
                    "value_list": ["a", "b"],
                    "reason": "x",
                    "confidence": "high",
                },
            ],
        }
    )
    use(monkeypatch, provider)
    enriched = await enrich("content", snapshot, result, settings())
    assert enriched["suggestions"]["status"] == "generated"
    assert enriched["suggestions"]["attached"] == 2
    assert provider.calls[0][1] is sc.RESPONSE_SCHEMA
    assert enriched["summary"]["text"].startswith("Add interior")
    by_key = {(i["rule"], i["subject"]): i for i in enriched["items"]}
    drafts = by_key[("posts_none_recent", "")]["suggestion"]
    assert drafts["field"] == "post_drafts" and len(drafts["value"]) == 2
    assert all(len(d) <= 300 for d in drafts["value"])
    assert by_key[("posts_none_recent", "")]["explanation_source"] == "deterministic+generated"
    assert len(by_key[("photo_type_empty", "interior")]["suggestion"]["value"]) == 7
    assert by_key[("posts_sparse", "")]["suggestion"] is None
    assert by_key[("video_missing", "")]["suggestion"] is None
    assert enriched["evaluations"] == result_for(snapshot)["evaluations"]


async def test_enrich_drops_drafts_that_break_post_rules(monkeypatch):
    snapshot = weak_content()
    result = result_for(snapshot)
    provider = FakeProvider(
        {
            "summary": "",
            "suggestions": [
                # A phone number: the whole draft set is rejected because only one survives.
                {
                    "rule": "posts_none_recent",
                    "field": "post_drafts",
                    "value_list": [
                        "Call 512-555-0199 to book a cleaning today.",
                        "Whitening consultations available this month. (Button: Book)",
                    ],
                    "reason": "x",
                    "confidence": "high",
                },
                # A link and shouting in two of three: only one clean draft, so none attach.
                {
                    "rule": "posts_sparse",
                    "field": "post_drafts",
                    "value_list": [
                        "See https://example.org for our offers.",
                        "AMAZING SMILES start here. (Button: Book)",
                        "New patient exams with a full check and x-rays. (Button: Book)",
                    ],
                    "reason": "x",
                    "confidence": "high",
                },
                # Over length, so dropped; the rest is fine and the first two attach.
                {
                    "rule": "post_types_uniform",
                    "field": "post_drafts",
                    "value_list": [
                        "x" * 301,
                        "Meet the team on Friday. (Button: Learn more)",
                        "Invisalign consultations this spring. (Button: Book)",
                    ],
                    "reason": "x",
                    "confidence": "medium",
                },
                # Too few distinct shots: dropped.
                {
                    "rule": "photo_type_empty",
                    "subject": "interior",
                    "field": "photo_shot_list",
                    "value_list": ["Waiting area", "waiting area", "Front desk", "", "Chair"],
                    "reason": "x",
                    "confidence": "high",
                },
                # Nine shots: trimmed to eight.
                {
                    "rule": "photos_few",
                    "field": "photo_shot_list",
                    "value_list": shots(9),
                    "reason": "x",
                    "confidence": "high",
                },
            ],
        }
    )
    use(monkeypatch, provider)
    enriched = await enrich("content", snapshot, result, settings())
    by_key = {(i["rule"], i["subject"]): i for i in enriched["items"]}
    assert by_key[("posts_none_recent", "")]["suggestion"] is None
    assert by_key[("posts_sparse", "")]["suggestion"] is None
    assert by_key[("post_types_uniform", "")]["suggestion"]["value"] == [
        "Meet the team on Friday. (Button: Learn more)",
        "Invisalign consultations this spring. (Button: Book)",
    ]
    assert by_key[("photo_type_empty", "interior")]["suggestion"] is None
    assert len(by_key[("photos_few", "")]["suggestion"]["value"]) == 8
    # No model summary: the deterministic one fills in.
    assert enriched["summary"]["source"] == "deterministic"
    assert enriched["summary"]["text"].startswith("Then: add photos")


async def test_enrich_skips_when_nothing_to_draft(monkeypatch):
    use(monkeypatch, FakeProvider({"suggestions": []}))
    clean = await enrich("content", complete(), result_for(complete()), settings())
    assert clean["suggestions"]["status"] == "skipped"
    assert clean["summary"]["text"].startswith("Every content check")


def test_clean_line_rules():
    assert sc.clean_line("  Fresh   smiles  ", 300) == "Fresh smiles"
    assert sc.clean_line("Call +1 (512) 555-0100", 300) is None
    assert sc.clean_line("Visit www.example.org", 300) is None
    assert sc.clean_line("Write to hi@example.org", 300) is None
    assert sc.clean_line("BOOK NOW", 300) is None
    assert sc.clean_line("Ask about our NEW chairs", 300) == "Ask about our NEW chairs"
    assert sc.clean_line("x" * 301, 300) is None
    assert sc.clean_line(42, 300) is None
