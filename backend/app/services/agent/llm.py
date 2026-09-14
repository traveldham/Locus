"""The chat model the operator agent reasons with.

Separate from `recommendations.suggestions.llm` on purpose. That module asks a model for
one JSON object and can always fall back to no suggestion at all; this one drives a
multi-turn tool-calling loop, which needs a LangChain chat model rather than a raw
`generateContent` call. What the two share is the credential story: Vertex AI on the
machine's Google application default credentials, no API key anywhere.

Vertex is the only provider here. The Gemini Developer API is deliberately not wired up:
a second auth path would double the ways an agent turn can fail to start, and nothing in
the product needs it. A missing or mismatched configuration raises `AgentUnavailable` so
the caller can tell the user exactly which setting to fill in, instead of failing later
inside the graph where the message would read as a model error.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.config import Settings

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel

# Low but not zero: the agent writes review replies, which read as a form letter at 0.
TEMPERATURE = 0.2


class AgentUnavailable(RuntimeError):
    """No chat model can be built from the current configuration."""


def build_chat_model(settings: Settings) -> BaseChatModel:
    """The Vertex chat model for one agent turn, or `AgentUnavailable` with the fix."""
    if settings.llm_provider != "vertex":
        raise AgentUnavailable(
            f"The agent runs on Vertex AI only, but LLM_PROVIDER is {settings.llm_provider!r}. "
            "Set LLM_PROVIDER=vertex."
        )
    if not settings.vertex_project:
        raise AgentUnavailable(
            "VERTEX_PROJECT is not set, so there is no Vertex AI project to call. "
            "Set VERTEX_PROJECT and authenticate with `gcloud auth application-default login`."
        )

    # Imported here rather than at module scope: the vertexai client pulls in the whole
    # google-cloud-aiplatform stack, which the API process should not pay for on startup
    # when no agent turn is running.
    from langchain_google_vertexai import ChatVertexAI

    # `vertex_location` defaults to "global", which ChatVertexAI understands: it maps the
    # global location to the unprefixed aiplatform.googleapis.com endpoint, the same host
    # the audit's Vertex provider builds by hand. Regional values are prefixed as usual.
    return ChatVertexAI(
        model=settings.vertex_model,
        project=settings.vertex_project,
        location=settings.vertex_location,
        temperature=TEMPERATURE,
    )
