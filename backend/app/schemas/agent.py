"""Wire shapes for the operator agent's chat.

A transcript is returned whole rather than paginated: a conversation is one location's
working session and the client polls it while a turn runs, so a stable, complete list is
simpler to reason about than a window that shifts as the agent writes new messages.
"""

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models import AgentMessageRole, AgentTurnStatus

MAX_MESSAGE_LENGTH = 4000


class ConversationCreateRequest(BaseModel):
    """The one location the chat is about. Every tool the agent holds is bound to it."""

    location_id: UUID


class ConversationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    location_id: UUID
    title: str | None = None
    created_at: datetime


class AgentMessageResponse(BaseModel):
    """One transcript entry. Named for the agent because `MessageResponse` is already
    the shape of a plain API acknowledgement."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: AgentMessageRole
    content: str | None = None
    # The tool calls an assistant message asked for, and the linkage a tool message
    # answers on. Both are replayed to the model on later turns, so both are exposed.
    tool_calls: Any = None
    tool_call_id: str | None = None
    tool_name: str | None = None
    created_at: datetime


class TurnResponse(BaseModel):
    """The lightweight thing a client polls while the agent works."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    status: AgentTurnStatus
    current_tool: str | None = None
    error: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None


class ConversationDetail(ConversationSummary):
    messages: list[AgentMessageResponse] = []
    # A turn outlives the request that started it, so a client that reloaded mid-answer
    # has no other way to find out the agent is still working and resume polling.
    active_turn: TurnResponse | None = None


class PostMessageRequest(BaseModel):
    content: Annotated[str, Field(min_length=1, max_length=MAX_MESSAGE_LENGTH)]
