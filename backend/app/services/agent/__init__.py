"""The GBP operator agent: a chat that can read the audit and act on the profile.

Three modules, each with one job. `tools.py` is the agent's hands - every tool is an
adapter over the same code the human UI runs, so an agent's write is the human write.
`llm.py` builds the Vertex chat model, or says exactly what is not configured.
`graph.py` is the LangGraph loop and the translation between stored transcript rows and
the messages a tool-calling model needs replayed.

Nothing here starts a turn or touches the request cycle: the Celery task and the HTTP API
compose these pieces. A caller's job is to build an `AgentToolContext`, build the tools
and the model from it, compile the graph, invoke it with `RECURSION_LIMIT`, and persist
the new messages with `from_langchain_message`.

The context carries the one location the conversation is about, and everything downstream
reads it from there: every tool binds itself to that location, and no tool takes one as an
argument. The caller supplies the location's title to `system_prompt` because it already
has it; nothing here queries for it.
"""

from app.services.agent.graph import (
    RECURSION_LIMIT,
    AgentState,
    build_graph,
    from_langchain_message,
    system_prompt,
    to_langchain_messages,
)
from app.services.agent.llm import AgentUnavailable, build_chat_model
from app.services.agent.tools import AgentToolContext, build_tools

__all__ = [
    "RECURSION_LIMIT",
    "AgentState",
    "AgentToolContext",
    "AgentUnavailable",
    "build_chat_model",
    "build_graph",
    "build_tools",
    "from_langchain_message",
    "system_prompt",
    "to_langchain_messages",
]
