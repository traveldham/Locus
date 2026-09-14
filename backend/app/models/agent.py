from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utcnow


class AgentConversation(Base):
    """One chat thread between a user and the GBP operator agent.

    A chat is about exactly one location. That location is what every tool the agent
    holds is bound to, so a conversation without one would be an agent with no boundary -
    which is why `location_id` is NOT NULL rather than merely expected to be set.
    """

    __tablename__ = "agent_conversations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    location_id: Mapped[UUID] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    messages: Mapped[list["AgentMessage"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="AgentMessage.created_at",
    )


class AgentMessageRole(StrEnum):
    user = "user"
    assistant = "assistant"
    tool = "tool"


class AgentMessage(Base):
    """One immutable turn in a conversation transcript: a human message, an assistant
    reply (optionally requesting tools), or a tool's result fed back to the model.

    Tool-calling chat models require the exact original ordering and linkage between an
    assistant message's tool_calls and the following tool messages' tool_call_id to be
    replayed on every later turn, so both are persisted rather than only the text.
    """

    __tablename__ = "agent_messages"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey("agent_conversations.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[AgentMessageRole] = mapped_column(
        Enum(AgentMessageRole, name="agent_message_role")
    )
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    tool_calls: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    tool_call_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tool_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    conversation: Mapped[AgentConversation] = relationship(back_populates="messages")


class AgentTurnStatus(StrEnum):
    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


class AgentTurn(Base):
    """One agent invocation triggered by a user message: may call several tools and
    several model turns before it produces a final reply. Mirrors AuditJob's shape."""

    __tablename__ = "agent_turns"
    __table_args__ = (
        # One live turn per conversation, enforced rather than merely checked: two
        # requests can pass the API's check at the same moment, and two agents writing
        # into one transcript would interleave it into something neither can replay.
        Index(
            "uq_agent_turns_one_active_per_conversation",
            "conversation_id",
            unique=True,
            postgresql_where=text("status IN ('pending', 'running')"),
            sqlite_where=text("status IN ('pending', 'running')"),
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey("agent_conversations.id", ondelete="CASCADE"), index=True
    )
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[AgentTurnStatus] = mapped_column(
        Enum(AgentTurnStatus, name="agent_turn_status"), default=AgentTurnStatus.pending
    )
    user_message_id: Mapped[UUID] = mapped_column(
        ForeignKey("agent_messages.id", ondelete="CASCADE")
    )
    current_tool: Mapped[str | None] = mapped_column(String(64), nullable=True)
    task_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
