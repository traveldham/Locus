"""The suggestion layer: optional, structured, never able to fail an audit."""

import httpx
import pytest
from test_profile_worker import AS_OF, complete

from app.core.config import Settings
from app.services.recommendations.engine import run_worker
from app.services.recommendations.suggestions import enrich, llm
from app.services.recommendations.suggestions import profile as sp
from app.services.recommendations.types import EngineConfig


def weak_profile():
    snapshot = complete()
    loc = snapshot["locations"][0]
    loc["description"] = None
    loc["phone_primary"] = None
    snapshot["categories"] = snapshot["categories"][:2]
    snapshot["attributes"] = [
        r for r in snapshot["attributes"] if "hearing" not in r["attribute_id"]
    ]
    snapshot["projects"] = [
        {
            "id": "p1",
            "name": "Brightpath Dental Group",
            "website_url": "https://example.org",
            "description": "Family dental group across Texas offering general and cosmetic care.",
            "services": ["Cleanings", "Whitening", "Invisalign"],
            "slug": "bdg",
            "status": "active",
        }
    ]
    return snapshot


def result_for(snapshot):
    return run_worker(snapshot, AS_OF, EngineConfig(), "profile")


def settings(**overrides) -> Settings:
    values = {
        "llm_provider": "vertex",
        "vertex_project": "test-project",
        "vertex_model": "gemini-test",
        "gemini_api_key": "test-key",
        "gemini_model": "gemini-test",
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


def test_targets_are_only_findings_whose_check_suggests_a_field():
    items = sp.targets(result_for(weak_profile()))
    rules = {i["rule"] for i in items}
    assert "description_missing" in rules and "secondary_categories_few" in rules
    assert "accessibility_unanswered" in rules
    assert "phone_missing" not in rules  # a fact only the business knows


def test_context_carries_profile_and_project_details():
    context = sp.business_context(weak_profile())
    assert context["name"] == "Brightpath Dental" and context["city"] == "Austin"
    assert context["projects"][0]["services"] == ["Cleanings", "Whitening", "Invisalign"]
    assert "hearing_loop" in context["attributes_unanswered"]
    assert "orthodontic_care" in context["attributes_no"]
    prompt = sp.build_prompt(context, sp.targets(result_for(weak_profile())))
    assert "Invisalign" in prompt and "rule=description_missing" in prompt
    assert "Never invent a phone number" in prompt


async def test_enrich_attaches_validated_suggestions(monkeypatch):
    snapshot = weak_profile()
    result = result_for(snapshot)
    provider = FakeProvider(
        {
            "suggestions": [
                {
                    "rule": "description_missing",
                    "field": "description",
                    "value_text": "A family dental practice in Austin. " * 40,
                    "reason": "Built from the project description and services.",
                    "confidence": "medium",
                },
                {
                    "rule": "secondary_categories_few",
                    "field": "additional_categories",
                    "value_list": ["Teeth whitening service", "Orthodontist"],
                    "reason": "Whitening and Invisalign are listed services.",
                    "confidence": "high",
                },
                {
                    "rule": "accessibility_unanswered",
                    "subject": "hearing_loop",
                    "field": "attributes",
                    "value_map": [{"name": "hearing_loop", "value": False}],
                    "reason": "Nothing in the context mentions a hearing loop.",
                    "confidence": "low",
                },
                # Wrong field for the rule: dropped.
                {
                    "rule": "secondary_categories_few",
                    "field": "description",
                    "value_text": "nope",
                    "reason": "x",
                    "confidence": "high",
                },
                # Unknown rule: dropped.
                {
                    "rule": "phone_missing",
                    "field": "phone",
                    "value_text": "555",
                    "reason": "x",
                    "confidence": "high",
                },
            ]
        }
    )
    use(monkeypatch, provider)
    enriched = await enrich("profile", snapshot, result, settings())
    assert enriched["suggestions"]["status"] == "generated"
    assert enriched["suggestions"]["attached"] == 3
    assert enriched["suggestions"]["model"] == "fake-model"
    assert provider.calls[0][1] is sp.RESPONSE_SCHEMA
    by_key = {(i["rule"], i["subject"]): i for i in enriched["items"]}
    description = by_key[("description_missing", "")]["suggestion"]
    assert description["field"] == "description" and len(description["value"]) <= 750
    assert description["source"] == "fake" and description["model"] == "fake-model"
    assert by_key[("description_missing", "")]["explanation_source"] == "deterministic+generated"
    assert by_key[("secondary_categories_few", "")]["suggestion"]["value"] == [
        "Teeth whitening service",
        "Orthodontist",
    ]
    assert by_key[("accessibility_unanswered", "hearing_loop")]["suggestion"]["value"] == {
        "hearing_loop": False
    }
    assert by_key[("phone_missing", "")]["suggestion"] is None
    # Verdicts are untouched by the suggestion pass.
    assert enriched["evaluations"] == result_for(snapshot)["evaluations"]


async def test_enrich_records_failure_and_keeps_findings(monkeypatch):
    use(monkeypatch, FakeProvider(error=llm.SuggestionError("Vertex AI returned 429: quota")))
    snapshot = weak_profile()
    enriched = await enrich("profile", snapshot, result_for(snapshot), settings())
    assert enriched["suggestions"]["status"] == "failed"
    assert "429" in enriched["suggestions"]["error"]
    assert enriched["items"] and all(i["suggestion"] is None for i in enriched["items"])


async def test_enrich_skips_when_unconfigured_disabled_or_nothing_to_draft(monkeypatch):
    snapshot = weak_profile()
    no_project = await enrich(
        "profile", snapshot, result_for(snapshot), settings(vertex_project=None)
    )
    assert no_project["suggestions"]["status"] == "skipped"
    assert "VERTEX_PROJECT" in no_project["suggestions"]["reason"]
    no_key = await enrich(
        "profile",
        snapshot,
        result_for(snapshot),
        settings(llm_provider="gemini", gemini_api_key=None),
    )
    assert "key" in no_key["suggestions"]["reason"]
    off = await enrich(
        "profile", snapshot, result_for(snapshot), settings(suggestions_enabled=False)
    )
    assert off["suggestions"]["status"] == "skipped"
    use(monkeypatch, FakeProvider({"suggestions": []}))
    clean = await enrich("profile", complete(), result_for(complete()), settings())
    assert clean["suggestions"]["status"] == "skipped"
    other = await enrich("content", snapshot, {"items": [], "evaluations": []}, settings())
    assert other["suggestions"]["status"] == "skipped"


def test_provider_factory_follows_settings():
    vertex = llm.provider_from_settings(settings())
    assert isinstance(vertex, llm.VertexProvider) and vertex.model == "gemini-test"
    assert vertex.endpoint.startswith("https://aiplatform.googleapis.com/v1/projects/test-project/")
    assert (
        "locations/global/publishers/google/models/gemini-test:generateContent" in vertex.endpoint
    )
    regional = llm.VertexProvider("p", "m", 5, "us-central1")
    assert regional.endpoint.startswith("https://us-central1-aiplatform.googleapis.com/")
    gemini = llm.provider_from_settings(settings(llm_provider="gemini"))
    assert isinstance(gemini, llm.GeminiApiProvider)
    assert llm.provider_from_settings(settings(vertex_project=None)) is None


def mock_http(monkeypatch, handler):
    transport = httpx.MockTransport(handler)
    original = httpx.AsyncClient

    class Client(original):
        def __init__(self, **kwargs):
            super().__init__(transport=transport, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", Client)


async def fake_token():
    return "tok"


async def test_vertex_provider_sends_bearer_token_and_parses_candidates(monkeypatch):
    provider = llm.VertexProvider("p", "m", 5)
    monkeypatch.setattr(provider, "token", fake_token)

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer tok"
        assert request.url.path.endswith("/publishers/google/models/m:generateContent")
        assert b'"responseMimeType":"application/json"' in request.read()
        return httpx.Response(
            200,
            json={"candidates": [{"content": {"parts": [{"text": '{"suggestions": []}'}]}}]},
        )

    mock_http(monkeypatch, handler)
    assert await provider.generate_json("p", {}) == {"suggestions": []}


@pytest.mark.parametrize("status", [401, 429, 500])
async def test_vertex_provider_turns_http_errors_into_suggestion_errors(monkeypatch, status):
    provider = llm.VertexProvider("p", "m", 5)
    monkeypatch.setattr(provider, "token", fake_token)
    mock_http(monkeypatch, lambda request: httpx.Response(status, json={"error": "bad"}))
    with pytest.raises(llm.SuggestionError, match=str(status)):
        await provider.generate_json("p", {})


async def test_vertex_provider_reports_missing_credentials(monkeypatch):
    provider = llm.VertexProvider("p", "m", 5)

    def broken():
        raise RuntimeError("no adc")

    monkeypatch.setattr(provider, "_token_sync", broken)
    with pytest.raises(llm.SuggestionError, match="application default credentials"):
        await provider.token()


async def test_gemini_provider_parses_interaction_steps(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-goog-api-key"] == "k"
        assert request.url.path == "/v1beta/interactions"
        assert b'"mime_type":"application/json"' in request.read()
        return httpx.Response(
            200,
            json={
                "steps": [
                    {"type": "user_input", "content": [{"type": "text", "text": "p"}]},
                    {
                        "type": "model_output",
                        "content": [{"type": "text", "text": '{"suggestions": []}'}],
                    },
                ]
            },
        )

    mock_http(monkeypatch, handler)
    provider = llm.GeminiApiProvider("k", "m", 5)
    assert await provider.generate_json("p", {}) == {"suggestions": []}
