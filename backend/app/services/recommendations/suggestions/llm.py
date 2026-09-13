"""The one place the audit talks to a language model.

A provider turns a prompt and a JSON schema into a parsed JSON object. Two are built:

- `VertexProvider`: Vertex AI on the global endpoint, authenticated with the machine's
  Google application default credentials (`gcloud auth application-default login`).
  No API key. This is the default.
- `GeminiApiProvider`: the Gemini Developer API with an API key, over the Interactions
  endpoint.

To add another provider, implement `generate_json` and register it in `provider_from_settings`.
Everything that goes wrong is a `SuggestionError`, so a caller can record it and move
on: suggestions are optional and an audit never fails because of them.
"""

from __future__ import annotations

import asyncio
import json
from typing import Protocol

import httpx

from app.core.config import Settings

CLOUD_PLATFORM_SCOPE = "https://www.googleapis.com/auth/cloud-platform"


class SuggestionError(RuntimeError):
    pass


class LlmProvider(Protocol):
    name: str
    model: str

    async def generate_json(self, prompt: str, schema: dict) -> dict: ...


def _post(url: str, headers: dict, body: dict, timeout_seconds: int):
    async def call() -> httpx.Response:
        try:
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                return await client.post(url, headers=headers, json=body)
        except httpx.HTTPError as error:
            raise SuggestionError(f"Request failed: {type(error).__name__}") from error

    return call()


def _expect_ok(response: httpx.Response, who: str) -> dict:
    if response.status_code != 200:
        detail = response.text[:300].replace("\n", " ")
        raise SuggestionError(f"{who} returned {response.status_code}: {detail}")
    try:
        return response.json()
    except ValueError as error:
        raise SuggestionError(f"{who} response was not JSON") from error


def _parse_json_text(text: str, who: str) -> dict:
    if not text:
        raise SuggestionError(f"{who} returned no text")
    try:
        return json.loads(text)
    except ValueError as error:
        raise SuggestionError(f"{who} text was not valid JSON") from error


class VertexProvider:
    """Vertex AI generateContent on the global endpoint, with application default
    credentials. The token is refreshed by google-auth when it expires."""

    name = "vertex"

    def __init__(self, project: str, model: str, timeout_seconds: int, location: str = "global"):
        self.project, self.model, self.timeout_seconds = project, model, timeout_seconds
        self.location = location
        self._credentials = None

    @property
    def endpoint(self) -> str:
        host = (
            "aiplatform.googleapis.com"
            if self.location == "global"
            else f"{self.location}-aiplatform.googleapis.com"
        )
        return (
            f"https://{host}/v1/projects/{self.project}/locations/{self.location}"
            f"/publishers/google/models/{self.model}:generateContent"
        )

    def _token_sync(self) -> str:
        import google.auth
        from google.auth.transport.requests import Request

        if self._credentials is None:
            self._credentials, _ = google.auth.default(scopes=[CLOUD_PLATFORM_SCOPE])
        if not self._credentials.valid:
            self._credentials.refresh(Request())
        return self._credentials.token

    async def token(self) -> str:
        try:
            return await asyncio.to_thread(self._token_sync)
        except Exception as error:  # noqa: BLE001 - any auth failure is one message
            raise SuggestionError(
                "Google application default credentials are not available: "
                f"{type(error).__name__}. Run `gcloud auth application-default login`."
            ) from error

    async def generate_json(self, prompt: str, schema: dict) -> dict:
        body = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": schema,
                "temperature": 0.3,
            },
        }
        headers = {
            "Authorization": f"Bearer {await self.token()}",
            "Content-Type": "application/json",
        }
        payload = _expect_ok(
            await _post(self.endpoint, headers, body, self.timeout_seconds), "Vertex AI"
        )
        try:
            parts = payload["candidates"][0]["content"]["parts"]
        except (KeyError, IndexError, TypeError) as error:
            finish = (payload.get("candidates") or [{}])[0].get("finishReason")
            raise SuggestionError(
                f"Vertex AI returned no content ({finish or 'unknown'})"
            ) from error
        return _parse_json_text("".join(p.get("text", "") for p in parts), "Vertex AI")


class GeminiApiProvider:
    """Gemini Developer API with an API key, over the Interactions endpoint."""

    name = "gemini"
    ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/interactions"

    def __init__(self, api_key: str, model: str, timeout_seconds: int):
        self.api_key, self.model, self.timeout_seconds = api_key, model, timeout_seconds

    async def generate_json(self, prompt: str, schema: dict) -> dict:
        body = {
            "model": self.model,
            "input": prompt,
            "response_format": {"type": "text", "mime_type": "application/json", "schema": schema},
        }
        headers = {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}
        payload = _expect_ok(
            await _post(self.ENDPOINT, headers, body, self.timeout_seconds), "Gemini"
        )
        text = "".join(
            part.get("text", "")
            for step in payload.get("steps", [])
            if step.get("type") == "model_output"
            for part in step.get("content", [])
            if part.get("type") == "text"
        )
        return _parse_json_text(text, "Gemini")


def provider_from_settings(settings: Settings) -> LlmProvider | None:
    """The configured provider, or None with no way to call a model.

    Returns None rather than raising so the caller can record "skipped" with a reason.
    """
    if settings.llm_provider == "vertex":
        if not settings.vertex_project:
            return None
        return VertexProvider(
            settings.vertex_project,
            settings.vertex_model,
            settings.suggestions_timeout_seconds,
            settings.vertex_location,
        )
    if settings.llm_provider == "gemini":
        if not settings.gemini_api_key:
            return None
        return GeminiApiProvider(
            settings.gemini_api_key, settings.gemini_model, settings.suggestions_timeout_seconds
        )
    return None


def unavailable_reason(settings: Settings) -> str:
    if settings.llm_provider == "vertex":
        return "VERTEX_PROJECT is not set."
    if settings.llm_provider == "gemini":
        return "No Gemini API key is configured."
    return f"Unknown LLM provider {settings.llm_provider!r}."
