"""The whole-audit summary: model when possible, deterministic otherwise."""

from test_profile_worker import AS_OF, complete

from app.core.config import Settings
from app.services.recommendations.engine import analyze
from app.services.recommendations.suggestions import overall
from app.services.recommendations.suggestions.llm import SuggestionError


def report():
    snapshot = complete()
    snapshot["locations"][0]["phone_primary"] = None
    return analyze(snapshot, AS_OF)


def offline() -> Settings:
    return Settings(_env_file=None, llm_provider="gemini", gemini_api_key=None)


async def test_fallback_names_weak_categories_and_first_priority():
    summary = await overall.overall_summary(report(), offline())
    assert summary["source"] == "deterministic"
    assert "Start with: Add a phone number" in summary["text"]
    assert "attention is needed on" in summary["text"]
    assert summary["attention"][0]["category"] == "profile"
    assert "phone" in summary["attention"][0]["text"].lower()
    assert all(p["category"] and p["text"] for p in summary["strengths"])


async def test_model_answer_is_used_and_banned_words_fall_back(monkeypatch):
    class Fake:
        name, model = "fake", "fake-model"

        def __init__(self, text):
            self.text = text

        async def generate_json(self, prompt, schema):
            assert "Category scores" in prompt and "Top priorities" in prompt
            return {
                "summary": self.text,
                "strengths": [
                    # Profile scored well in this fixture, so it may be a strength.
                    {"category": "profile", "text": "Contact details are complete."},
                    # Content scored 0 and performance was not evaluated: rejected.
                    {"category": "content", "text": "Photos look great."},
                    {"category": "performance", "text": "Traffic is steady."},
                ],
                "attention": [
                    {"category": "profile", "text": "Add the phone number."},
                    {"category": "nonsense", "text": "dropped"},
                ],
            }

    settings = Settings(_env_file=None, llm_provider="vertex", vertex_project="p")
    monkeypatch.setattr(overall, "provider_from_settings", lambda s: Fake("Fix the phone first."))
    good = await overall.overall_summary(report(), settings)
    assert good["source"] == "fake" and good["text"] == "Fix the phone first."
    assert good["strengths"] == [{"category": "profile", "text": "Contact details are complete."}]
    assert good["attention"] == [{"category": "profile", "text": "Add the phone number."}]

    monkeypatch.setattr(
        overall, "provider_from_settings", lambda s: Fake("This will double your revenue.")
    )
    assert (await overall.overall_summary(report(), settings))["source"] == "deterministic"

    class Broken(Fake):
        async def generate_json(self, prompt, schema):
            raise SuggestionError("down")

    monkeypatch.setattr(overall, "provider_from_settings", lambda s: Broken(""))
    assert (await overall.overall_summary(report(), settings))["source"] == "deterministic"
