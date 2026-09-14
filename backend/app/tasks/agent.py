"""Run one chat turn off the request thread.

A turn is not a single model call: the agent may read the audit, list reviews, write a
reply and report back, which is several model calls and several tool calls deep. That
cannot sit in an HTTP request, so a turn is queued like an audit is.

Each message the graph produces is written and committed as it appears rather than in one
batch at the end, because the transcript is what the client polls — an agent that spends
forty seconds working should be visibly working, not silent until it finishes.

Nothing here raises into the worker. A model that is unreachable, a tool that fails, a
graph that hits its recursion bound: all of them land as a `failed` turn carrying the
reason, because a chat that stops answering with no explanation is the worst outcome.

The same loop also publishes what it is doing to a Redis channel, so a reader can watch
the answer arrive rather than wait for it. That is an addition and never a replacement:
what is published is a view of what has already been committed, and nothing on the
publishing path is allowed to change, delay or fail what gets written down.
"""

import asyncio
import logging
from typing import Any
from uuid import UUID

from langchain_core.messages import AIMessageChunk
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import (
    AgentConversation,
    AgentMessage,
    AgentMessageRole,
    AgentTurn,
    AgentTurnStatus,
    Location,
)
from app.services.agent.graph import (
    RECURSION_LIMIT,
    build_graph,
    content_text,
    from_langchain_message,
    system_prompt,
    to_langchain_messages,
)
from app.services.agent.llm import AgentUnavailable, build_chat_model
from app.services.agent.stream import TurnEvents
from app.services.agent.tools import AgentToolContext, build_tools
from app.tasks.audit import SessionFactory, _in_task, now
from app.worker import celery_app

logger = logging.getLogger(__name__)

MAX_ERROR_LENGTH = 2000

NO_ANSWER = "The assistant did not return an answer. Ask again."

# What a reader is told when the loop never reached an ending of its own - a soft time
# limit, a cancelled worker. The turn row is left `running` in that case and released by
# `release_abandoned_turn`, but the reader is waiting now and has to be let go now.
UNFINISHED = "The agent stopped without finishing. Ask again."

Outcome = tuple[AgentTurnStatus, str | None]


def _is_empty(fields: dict) -> bool:
    """An assistant message carrying neither words nor a tool call. The provider does
    return these, and they are worth nothing to anyone: unreadable to the user and pure
    noise in the history every later turn replays."""
    return (
        fields["role"] == AgentMessageRole.assistant
        and not fields["content"]
        and not fields["tool_calls"]
    )


async def load_turn(db: AsyncSession, turn_id: UUID) -> AgentTurn | None:
    return await db.scalar(select(AgentTurn).where(AgentTurn.id == turn_id))


async def transcript(db: AsyncSession, conversation_id: UUID) -> list[AgentMessage]:
    rows = await db.scalars(
        select(AgentMessage)
        .where(AgentMessage.conversation_id == conversation_id)
        # Ties are broken by id only to make the order deterministic, not correct: the id
        # is random, so a genuine timestamp collision can still order a tool result before
        # its call. `graph._repair` is what makes that survivable rather than fatal.
        .order_by(AgentMessage.created_at, AgentMessage.id)
    )
    return list(rows.all())


async def fail_turn(db: AsyncSession, turn_id: UUID, error: str) -> None:
    """Record why a turn stopped. Re-read rather than trusted: the session may have been
    rolled back, which expires every object the caller was holding."""
    try:
        turn = await db.get(AgentTurn, turn_id)
        if turn is None:
            return
        turn.status = AgentTurnStatus.failed
        turn.error = error[:MAX_ERROR_LENGTH]
        turn.current_tool = None
        turn.finished_at = now()
        await db.commit()
    except Exception:  # noqa: BLE001 - a turn left running is bad; a dead worker is worse
        logger.exception("Could not record the failure of agent turn %s", turn_id)


async def failed(db: AsyncSession, turn_id: UUID, error: str) -> Outcome:
    """Record the failure and hand back the same reason the row now carries, truncated
    the same way, so what a reader is told and what a reload shows cannot disagree."""
    await fail_turn(db, turn_id, error)
    return AgentTurnStatus.failed, error[:MAX_ERROR_LENGTH]


def delta_text(payload: Any) -> str:
    """The assistant text in one `messages`-mode item, if that is what it holds.

    `stream_mode="messages"` carries `(message, metadata)`, and not every message on it
    is a token. LangGraph emits each node's finished output there too, so a whole
    `ToolMessage` and the completed `AIMessage` arrive on the same stream as the deltas
    that built it - forwarding those would send the answer twice and the tool results as
    if they were words. Only an `AIMessageChunk` is a delta, and only its text is one:
    tool-call arguments stream in `tool_call_chunks`, which nobody is reading.
    """
    if not isinstance(payload, tuple) or not payload:
        return ""
    message = payload[0]
    if not isinstance(message, AIMessageChunk):
        return ""
    return content_text(message.content)


async def run_turn(turn_id: UUID, session_factory: SessionFactory) -> None:
    """Answer one user message: reason, call tools, and write what happened down."""
    async with session_factory() as db:
        turn = await load_turn(db, turn_id)
        if turn is None or turn.status != AgentTurnStatus.pending:
            # Either it is gone or another worker already claimed it.
            return

        turn.status = AgentTurnStatus.running
        turn.started_at = now()
        await db.commit()

        # Opened only once the claim above succeeded. A worker that lost the race must
        # not publish `done` onto a channel the winner is still writing to.
        events = TurnEvents(turn_id)
        outcome: Outcome = (AgentTurnStatus.failed, UNFINISHED)
        try:
            await events.status(AgentTurnStatus.running, None)
            outcome = await answer(db, turn, session_factory, events)
        finally:
            # The one event a reader cannot do without, so it is published on every way
            # out of here - including the ones that are not exceptions the loop caught.
            await events.done(*outcome)
            await events.aclose()


async def answer(
    db: AsyncSession, turn: AgentTurn, session_factory: SessionFactory, events: TurnEvents
) -> Outcome:
    """Run the loop for one claimed turn and say how it ended.

    The outcome is returned rather than only written to the row because the caller has to
    announce it on the channel as well, and a reader that was told nothing would sit
    waiting on a turn that finished.
    """
    turn_id = turn.id
    conversation = await db.scalar(
        select(AgentConversation).where(AgentConversation.id == turn.conversation_id)
    )
    if conversation is None:
        return await failed(db, turn_id, "The conversation this turn belongs to no longer exists.")

    # Read out as plain values before the graph runs. Anything still held as an ORM
    # attribute would have to be lazily reloaded if this session were ever expired
    # mid-turn, and a lazy load inside the streaming loop raises `MissingGreenlet`
    # rather than doing anything useful.
    conversation_id = conversation.id
    context = AgentToolContext(
        session_factory=session_factory,
        organization_id=conversation.organization_id,
        location_id=conversation.location_id,
        user_id=conversation.user_id,
    )
    # What the agent calls the profile it is working on. Read once here rather than on
    # every model call.
    label = await db.scalar(select(Location.title).where(Location.id == context.location_id))

    try:
        model = build_chat_model(get_settings())
    except AgentUnavailable as error:
        return await failed(db, turn_id, str(error))

    graph = build_graph(model, build_tools(context))
    history = to_langchain_messages(await transcript(db, conversation_id))
    seen = len(history)

    answered = False
    current_tool: str | None = None
    try:
        async for mode, payload in graph.astream(
            {"messages": history},
            config={"recursion_limit": RECURSION_LIMIT},
            context={"system_prompt": system_prompt(label)},
            # A list, not a tuple: LangGraph only tags each item with the mode that
            # produced it when `stream_mode` is a list, and an untagged item gives the
            # loop below no way to tell a token from a state.
            stream_mode=["values", "messages"],
        ):
            if mode == "messages":
                await events.token(delta_text(payload))
                continue
            produced = payload["messages"][seen:]
            seen += len(produced)
            for message in produced:
                fields = from_langchain_message(message)
                if _is_empty(fields):
                    # Nothing to read and nothing to answer: storing it would put a
                    # blank bubble in the transcript and replay it on every later turn.
                    continue
                row = AgentMessage(conversation_id=conversation_id, **fields)
                db.add(row)
                turn.current_tool = pending_tool(fields)
                await db.commit()
                # Published after the commit, never before: the channel says what the
                # transcript already holds, so a reader can never be shown a message a
                # reload would then take away.
                await events.message(row)
                if turn.current_tool != current_tool:
                    current_tool = turn.current_tool
                    await events.status(AgentTurnStatus.running, current_tool)
                if fields["role"] == AgentMessageRole.assistant and fields["content"]:
                    answered = True
    except Exception as error:  # noqa: BLE001 - every failure is the turn's, not the worker's
        # Guarded: on a connection-level failure the rollback raises too, and an
        # escaping exception here would leave the turn `running` forever.
        try:
            await db.rollback()
        except Exception:  # noqa: BLE001 - the original failure is the one worth keeping
            logger.exception("Rollback failed while handling a failed agent turn")
        return await failed(db, turn_id, f"{type(error).__name__}: {error}")

    if not answered:
        # The loop ran without error but the model said nothing. Reporting success
        # would leave the reader with a re-enabled composer and no reply at all, which
        # is indistinguishable from the product being broken - because it is.
        return await failed(db, turn_id, NO_ANSWER)

    turn.status = AgentTurnStatus.succeeded
    turn.current_tool = None
    turn.finished_at = now()
    await db.commit()
    return AgentTurnStatus.succeeded, None


def pending_tool(fields: dict) -> str | None:
    """What to show as in-progress after this message: the tool about to run, if any."""
    if fields.get("role") == AgentMessageRole.assistant and fields.get("tool_calls"):
        return str(fields["tool_calls"][0].get("name") or "")[:64] or None
    return None


_settings = get_settings()


@celery_app.task(
    name="agent.run_turn",
    bind=True,
    max_retries=0,
    # The Celery-wide limit is sized for an audit; someone waiting on a chat is not.
    time_limit=_settings.agent_turn_timeout_seconds,
    soft_time_limit=max(_settings.agent_turn_timeout_seconds - 15, 15),
)
def run_agent_turn(self, turn_id: str) -> str:
    asyncio.run(_in_task(run_turn, UUID(turn_id)))
    return turn_id


__all__ = ["answer", "delta_text", "run_agent_turn", "run_turn"]
