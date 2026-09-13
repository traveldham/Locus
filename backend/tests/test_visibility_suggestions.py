"""The visibility suggestion layer: keyword plans and term actions, validated in code."""

from test_visibility_worker import AS_OF, healthy, set_ranks

from app.core.config import Settings
from app.services.recommendations.engine import run_worker
from app.services.recommendations.suggestions import enrich
from app.services.recommendations.suggestions import visibility as sv
from app.services.recommendations.types import EngineConfig

NEAR = "dentist open saturday austin"
LAGGING = "emergency dentist austin"
TERM = "dentist austin"


def weak_visibility():
    snapshot = healthy()
    set_ranks(snapshot, "k4", [6, 7, 10, 6])  # near the pack
    set_ranks(snapshot, "k3", [3, 3, 3, 12])  # high-intent keyword lagging
    snapshot["search_terms"][1]["impressions"] = 200  # a term losing 60%
    return snapshot


def result_for(snapshot):
    return run_worker(snapshot, AS_OF, EngineConfig(), "visibility")


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

    def __init__(self, response=None):
        self.response, self.calls = response, []

    async def generate_json(self, prompt: str, schema: dict) -> dict:
        self.calls.append((prompt, schema))
        return self.response


def use(monkeypatch, provider):
    monkeypatch.setattr(
        "app.services.recommendations.suggestions.provider_from_settings", lambda s: provider
    )


def test_targets_are_keyword_and_term_findings_only():
    items = sv.targets(result_for(weak_visibility()))
    assert {(i["rule"], i["subject"]) for i in items} == {
        ("near_pack_opportunity", NEAR),
        ("high_intent_lagging", LAGGING),
        ("search_term_losing", TERM),
    }


def test_context_carries_keywords_terms_rivals_and_projects():
    context = sv.business_context(weak_visibility())
    assert context["name"] == "Brightpath Dental" and context["city"] == "Austin"
    by_keyword = {k["keyword"]: k for k in context["keywords"]}
    assert by_keyword[NEAR]["latest_position"] == 6 and by_keyword[NEAR]["weeks_in_pack"] == 0
    assert by_keyword[LAGGING]["intent"] == "emergency"
    assert context["top_search_terms"][0]["term"] == "teeth whitening austin"
    assert context["projects"][0]["services"] == ["Teeth whitening", "Invisalign"]
    assert context["ours"]["review_count"] == 100
    prompt = sv.build_prompt(context, sv.targets(result_for(weak_visibility())))
    assert f"subject={NEAR}" in prompt and "field=keyword_plan" in prompt
    assert f"subject={TERM}" in prompt and "field=term_action" in prompt
    assert "Never promise a position" in prompt


async def test_enrich_attaches_validated_drafts(monkeypatch):
    snapshot = weak_visibility()
    result = result_for(snapshot)
    provider = FakeProvider(
        {
            "summary": "The profile holds the pack on its own name.",
            "suggestions": [
                {
                    "rule": "near_pack_opportunity",
                    "subject": NEAR,
                    "field": "keyword_plan",
                    "value_map": [
                        {
                            "name": NEAR,
                            "value": "Add Saturday hours and set Saturday appointments to yes.",
                        },
                        {"name": "some other keyword", "value": "Ignored."},
                    ],
                    "reason": "Saturday hours are missing from the profile.",
                    "confidence": "medium",
                },
                {
                    "rule": "search_term_losing",
                    "subject": TERM,
                    "field": "term_action",
                    "value_text": "  List routine cleaning as a service and post about it.  ",
                    "reason": "Cleanings are a project service.",
                    "confidence": "high",
                },
                # Wrong field for the rule: dropped.
                {
                    "rule": "high_intent_lagging",
                    "subject": LAGGING,
                    "field": "term_action",
                    "value_text": "nope",
                    "reason": "x",
                    "confidence": "high",
                },
                # Unknown subject: dropped.
                {
                    "rule": "near_pack_opportunity",
                    "subject": "invented keyword",
                    "field": "keyword_plan",
                    "value_map": [{"name": "invented keyword", "value": "x"}],
                    "reason": "x",
                    "confidence": "high",
                },
            ],
        }
    )
    use(monkeypatch, provider)
    enriched = await enrich("visibility", snapshot, result, settings())
    assert enriched["suggestions"]["status"] == "generated"
    assert enriched["suggestions"]["attached"] == 2
    assert enriched["suggestions"]["requested"] == 3
    assert provider.calls[0][1] is sv.RESPONSE_SCHEMA
    by_key = {(i["rule"], i["subject"]): i for i in enriched["items"]}
    plan = by_key[("near_pack_opportunity", NEAR)]["suggestion"]
    assert plan["field"] == "keyword_plan"
    assert plan["value"] == {NEAR: "Add Saturday hours and set Saturday appointments to yes."}
    assert by_key[("near_pack_opportunity", NEAR)]["explanation_source"] == (
        "deterministic+generated"
    )
    action = by_key[("search_term_losing", TERM)]["suggestion"]
    assert action["value"] == "List routine cleaning as a service and post about it."
    assert by_key[("high_intent_lagging", LAGGING)]["suggestion"] is None
    assert enriched["summary"]["text"].startswith("The profile holds")
    assert enriched["evaluations"] == result_for(snapshot)["evaluations"]


async def test_enrich_drops_links_phones_and_caps_sentence_length(monkeypatch):
    snapshot = weak_visibility()
    provider = FakeProvider(
        {
            "summary": "",
            "suggestions": [
                {
                    "rule": "near_pack_opportunity",
                    "subject": NEAR,
                    "field": "keyword_plan",
                    "value_map": [{"name": NEAR, "value": "See https://example.org for tips."}],
                    "reason": "x",
                    "confidence": "high",
                },
                {
                    "rule": "search_term_losing",
                    "subject": TERM,
                    "field": "term_action",
                    "value_text": "Call 512-555-0199 to book.",
                    "reason": "x",
                    "confidence": "high",
                },
                {
                    "rule": "high_intent_lagging",
                    "subject": LAGGING,
                    "field": "keyword_plan",
                    "value_map": [{"name": LAGGING.upper(), "value": "Add emergency care. " * 30}],
                    "reason": "x",
                    "confidence": "low",
                },
            ],
        }
    )
    use(monkeypatch, provider)
    enriched = await enrich("visibility", snapshot, result_for(snapshot), settings())
    by_key = {(i["rule"], i["subject"]): i for i in enriched["items"]}
    assert by_key[("near_pack_opportunity", NEAR)]["suggestion"] is None
    assert by_key[("search_term_losing", TERM)]["suggestion"] is None
    capped = by_key[("high_intent_lagging", LAGGING)]["suggestion"]["value"][LAGGING]
    assert len(capped) <= sv.SENTENCE_MAX_CHARS + 1 and capped.endswith(".")
    # No model summary: the deterministic one fills in.
    assert enriched["summary"]["source"] == "deterministic"


def test_fallback_summary_names_the_opportunities():
    summary = sv.fallback_summary(result_for(weak_visibility()))
    assert summary["source"] == "deterministic" and summary["model"] is None
    assert NEAR in summary["text"] and "losing impressions" in summary["text"]
    clean = sv.fallback_summary(result_for(healthy()))
    assert "passed" in clean["text"]
