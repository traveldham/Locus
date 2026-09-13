"""Reputation suggestion layer: drafted replies and themes, validated in code, never
able to fail an audit. No real model is ever called."""

from test_reputation_worker import AS_OF, complete

from app.core.config import Settings
from app.services.recommendations.engine import run_worker
from app.services.recommendations.suggestions import enrich, llm
from app.services.recommendations.suggestions import reputation as sr
from app.services.recommendations.types import EngineConfig


def weak_reputation():
    """Two low reviews waiting for a reply, and a rating that fell."""
    snapshot = complete()
    for r in snapshot["reviews"]:
        if r["id"] in ("r-10", "r-14"):
            r["reply_comment"] = None
            r["reply_update_time"] = None
        if r["id"] == "r-14":
            r["comment"] = "Waited forty minutes past my slot and nobody explained why."
    for r in snapshot["reviews"][:12]:
        r["star_rating"] = 3 if r["star_rating"] == 5 else r["star_rating"]
    return snapshot


def result_for(snapshot):
    return run_worker(snapshot, AS_OF, EngineConfig(), "reputation")


def settings(**overrides) -> Settings:
    values = {
        "llm_provider": "vertex",
        "vertex_project": "test-project",
        "vertex_model": "gemini-test",
        "suggestions_enabled": True,
        **overrides,
    }
    return Settings(_env_file=None, **values)


class FakeProvider:
    name = "fake"
    model = "fake-model"

    def __init__(self, response=None, error=None):
        self.response, self.error, self.calls = response, error, []

    async def generate_json(self, prompt: str, schema: dict) -> dict:
        self.calls.append((prompt, schema))
        if self.error:
            raise self.error
        return self.response


def use(monkeypatch, provider):
    monkeypatch.setattr(
        "app.services.recommendations.suggestions.provider_from_settings", lambda s: provider
    )


def test_targets_are_replies_and_themes_only():
    items = sr.targets(result_for(weak_reputation()))
    by_rule = {}
    for item in items:
        by_rule.setdefault(item["rule"], []).append(item["subject"])
    assert by_rule["critical_review_unanswered"] == ["g-10", "g-14"]
    assert by_rule["rating_low"] == [""] and by_rule["rating_trend_falling"] == [""]
    assert "reply_rate_low" not in by_rule


def test_context_carries_projects_and_the_reviews_without_names():
    context = sr.business_context(weak_reputation())
    assert context["name"] == "Brightpath Dental" and context["city"] == "Austin"
    assert context["projects"][0]["services"] == ["Routine cleaning", "Teeth whitening"]
    waiting = context["unanswered_low_reviews"]
    assert [r["id"] for r in waiting] == ["g-10", "g-14"]
    assert waiting[1]["rating"] == 1 and waiting[1]["replied"] is False
    assert "forty minutes" in waiting[1]["comment"] and waiting[1]["date"] == "2026-05-21"
    assert len(context["recent_reviews"]) == 24 and context["recent_reviews"][0]["replied"]
    assert "reviewer" not in str(context)
    prompt = sr.build_prompt(context, sr.targets(result_for(weak_reputation())))
    assert "subject=g-14" in prompt and "field=review_reply" in prompt
    assert "field=themes" in prompt and "under 350 characters" in prompt


async def test_enrich_attaches_validated_replies_and_themes(monkeypatch):
    snapshot = weak_reputation()
    result = result_for(snapshot)
    provider = FakeProvider(
        {
            "summary": "Two low reviews wait for a reply and the recent rating slipped.",
            "suggestions": [
                {
                    "rule": "critical_review_unanswered",
                    "subject": "g-14",
                    "field": "review_reply",
                    "value_text": (
                        "Thank you for telling us about the forty-minute wait. That is not "
                        "the experience we want anyone to have, and we are sorry nobody kept "
                        "you informed. Please contact the practice directly so we can put "
                        "this right. The Brightpath team"
                    ),
                    "reason": "The comment names a long wait with no explanation.",
                    "confidence": "high",
                },
                # Duplicate for the same review: the first one stands.
                {
                    "rule": "critical_review_unanswered",
                    "subject": "g-14",
                    "field": "review_reply",
                    "value_text": "Second attempt.",
                    "reason": "x",
                    "confidence": "low",
                },
                {
                    "rule": "critical_review_unanswered",
                    "subject": "g-10",
                    "field": "review_reply",
                    "value_text": "Thanks for the feedback. " * 30,
                    "reason": "Comment is generic.",
                    "confidence": "low",
                },
                {
                    "rule": "rating_low",
                    "field": "themes",
                    "value_list": ["long waits", "Long waits", "gentle hygienists", ""],
                    "reason": "Several recent reviews mention waiting.",
                    "confidence": "high",
                },
                # Wrong field for the rule: dropped.
                {
                    "rule": "rating_trend_falling",
                    "field": "review_reply",
                    "value_text": "nope",
                    "reason": "x",
                    "confidence": "high",
                },
                # Not a target: dropped.
                {
                    "rule": "reply_rate_low",
                    "field": "themes",
                    "value_list": ["x"],
                    "reason": "x",
                    "confidence": "high",
                },
            ],
        }
    )
    use(monkeypatch, provider)
    enriched = await enrich("reputation", snapshot, result, settings())
    assert enriched["suggestions"]["status"] == "generated"
    assert enriched["suggestions"]["attached"] == 3
    assert provider.calls[0][1] is sr.RESPONSE_SCHEMA
    assert enriched["summary"]["text"].startswith("Two low reviews")
    by_key = {(i["rule"], i["subject"]): i for i in enriched["items"]}
    first = by_key[("critical_review_unanswered", "g-14")]["suggestion"]
    assert first["field"] == "review_reply" and first["value"].startswith("Thank you for telling")
    assert first["source"] == "fake" and first["model"] == "fake-model"
    assert by_key[("critical_review_unanswered", "g-14")]["explanation_source"] == (
        "deterministic+generated"
    )
    long_reply = by_key[("critical_review_unanswered", "g-10")]["suggestion"]["value"]
    assert len(long_reply) <= sr.REPLY_MAX_CHARS
    themes = by_key[("rating_low", "")]["suggestion"]
    assert themes["value"] == ["long waits", "gentle hygienists"]
    assert themes["confidence"] == "medium"  # themes are never high
    assert by_key[("rating_trend_falling", "")]["suggestion"] is None
    assert enriched["evaluations"] == result_for(snapshot)["evaluations"]


async def test_enrich_drops_replies_that_break_google_guidance(monkeypatch):
    snapshot = weak_reputation()
    result = result_for(snapshot)
    bad = {
        "g-14": "Hi Barbara, sorry about the wait. Call us on 512-555-0100.",
        "g-10": "Sorry to hear that. Come back for 20% off your next visit!",
    }
    provider = FakeProvider(
        {
            "summary": "",
            "suggestions": [
                {
                    "rule": "critical_review_unanswered",
                    "subject": subject,
                    "field": "review_reply",
                    "value_text": text,
                    "reason": "x",
                    "confidence": "high",
                }
                for subject, text in bad.items()
            ]
            + [
                {
                    "rule": "rating_low",
                    "field": "themes",
                    "value_list": ["see https://example.org"],
                    "reason": "x",
                    "confidence": "low",
                }
            ],
        }
    )
    use(monkeypatch, provider)
    enriched = await enrich("reputation", snapshot, result, settings())
    assert enriched["suggestions"]["attached"] == 0
    assert all(i["suggestion"] is None for i in enriched["items"])
    assert enriched["summary"]["source"] == "deterministic"


def test_reply_validation_rules():
    ok = "Thank you for your visit. We are sorry about the wait; please reach out so we can help."
    assert sr._safe_value("review_reply", ok, {}) == ok
    assert sr._safe_value("review_reply", "Dear Mr Smith, sorry.", {}) is None
    assert (
        sr._safe_value("review_reply", "Hello there, thank you.", {}) == "Hello there, thank you."
    )
    assert sr._safe_value("review_reply", "Email us at care@example.org", {}) is None
    assert sr._safe_value("review_reply", "Use coupon SAVE10", {}) is None
    assert sr._safe_value("review_reply", 42, {}) is None
    assert sr._safe_value("themes", "not a list", {}) is None
    assert sr._safe_value("themes", [f"theme {n}" for n in range(20)], {}) == [
        f"theme {n}" for n in range(sr.THEME_MAX)
    ]


async def test_enrich_records_failure_and_keeps_findings(monkeypatch):
    use(monkeypatch, FakeProvider(error=llm.SuggestionError("Vertex AI returned 429: quota")))
    snapshot = weak_reputation()
    enriched = await enrich("reputation", snapshot, result_for(snapshot), settings())
    assert enriched["suggestions"]["status"] == "failed"
    assert "429" in enriched["suggestions"]["error"]
    assert enriched["items"] and all(i["suggestion"] is None for i in enriched["items"])


async def test_enrich_skips_when_disabled_or_nothing_to_draft(monkeypatch):
    snapshot = weak_reputation()
    off = await enrich(
        "reputation", snapshot, result_for(snapshot), settings(suggestions_enabled=False)
    )
    assert off["suggestions"]["status"] == "skipped"
    provider = FakeProvider({"summary": "", "suggestions": []})
    use(monkeypatch, provider)
    clean = await enrich("reputation", complete(), result_for(complete()), settings())
    assert clean["suggestions"]["status"] == "skipped" and provider.calls == []
    assert clean["summary"]["source"] == "deterministic"
