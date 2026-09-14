"""The operator agent's chat: post a message, poll the turn, read the transcript.

Posting a message does not answer it. The agent may need several model calls and several
writes to Google to do what was asked, so the request only records the message, queues a
turn and hands back its id — the same shape the audit pipeline uses. Clients poll the turn
for status and re-read the conversation for the messages the agent has produced so far.

`GET /agent/turns/{id}/stream` is the live version of that poll. The turn runs in a Celery
worker, so this process cannot see the model's tokens; it subscribes to the Redis channel
the worker publishes them on and forwards what arrives. It is a faster view of the same
answer and nothing more — the transcript is still written by the worker and still read
back from the database, so a client that never opens this endpoint loses nothing but the
animation.
"""

from collections.abc import AsyncIterator
from datetime import timedelta
from time import monotonic
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.api.dependencies import CurrentUser, DbSession
from app.api.scoping import OrganizationId
from app.core.config import get_settings
from app.models import (
    AgentConversation,
    AgentMessage,
    AgentMessageRole,
    AgentTurn,
    AgentTurnStatus,
    Location,
    utcnow,
)
from app.schemas.agent import (
    ConversationCreateRequest,
    ConversationDetail,
    ConversationSummary,
    PostMessageRequest,
    TurnResponse,
)
from app.services.agent.stream import (
    DONE,
    HEARTBEAT_SECONDS,
    STATUS,
    TurnSubscription,
    sse,
)

router = APIRouter(prefix="/agent", tags=["Agent"])

ACTIVE = (AgentTurnStatus.pending, AgentTurnStatus.running)
TERMINAL = (AgentTurnStatus.succeeded, AgentTurnStatus.failed)
BUSY_DETAIL = "The agent is still working on this chat"
ABANDONED = "The agent stopped without finishing. Ask again."

# How long past its own timeout a turn has to be before it is treated as abandoned. A
# worker killed at its hard time limit never gets to write `failed`, and without this the
# chat it was working on would refuse every later message for good.
ABANDONED_AFTER = timedelta(seconds=get_settings().agent_turn_timeout_seconds + 60)

# A stream must not outlive the turn it is watching. The worker is killed at its own time
# limit and a worker killed that way publishes nothing, so the margin here is the reader's
# only way out of waiting for an event that is never coming.
MAX_STREAM_SECONDS = get_settings().agent_turn_timeout_seconds + 30

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    # nginx buffers a proxied response by default, which would collect a whole turn's
    # tokens and deliver them in one block - exactly the behaviour this endpoint exists
    # to replace.
    "X-Accel-Buffering": "no",
}


async def release_abandoned_turn(db: DbSession, conversation_id: UUID) -> None:
    """Fail a turn no worker can still be running, so its conversation is usable again."""
    cutoff = utcnow() - ABANDONED_AFTER
    stale = await db.scalars(
        select(AgentTurn).where(
            AgentTurn.conversation_id == conversation_id,
            AgentTurn.status.in_(ACTIVE),
            AgentTurn.created_at < cutoff,
        )
    )
    released = False
    for turn in stale.all():
        turn.status = AgentTurnStatus.failed
        turn.error = ABANDONED
        turn.finished_at = utcnow()
        released = True
    if released:
        await db.commit()


async def owned_location(db: DbSession, organization_id: UUID, location_id: UUID) -> Location:
    location = await db.scalar(
        select(Location).where(
            Location.id == location_id, Location.organization_id == organization_id
        )
    )
    if location is None:
        raise HTTPException(status_code=404, detail="Location not found")
    return location


async def owned_conversation(
    db: DbSession, organization_id: UUID, conversation_id: UUID
) -> AgentConversation:
    conversation = await db.scalar(
        select(AgentConversation).where(
            AgentConversation.id == conversation_id,
            AgentConversation.organization_id == organization_id,
        )
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.post("/conversations", response_model=ConversationSummary, status_code=201)
async def create_conversation(
    payload: ConversationCreateRequest,
    organization_id: OrganizationId,
    current_user: CurrentUser,
    db: DbSession,
) -> ConversationSummary:
    """A chat about one profile."""
    location = await owned_location(db, organization_id, payload.location_id)
    conversation = AgentConversation(
        organization_id=organization_id,
        location_id=location.id,
        user_id=current_user.id,
        title=location.title,
    )
    db.add(conversation)
    await db.commit()
    return ConversationSummary.model_validate(conversation)


@router.get("/conversations", response_model=list[ConversationSummary])
async def list_conversations(
    organization_id: OrganizationId,
    db: DbSession,
    location_id: UUID | None = None,
) -> list[ConversationSummary]:
    """Conversations about one location, newest first, or all of this tenant's."""
    statement = select(AgentConversation).where(
        AgentConversation.organization_id == organization_id
    )
    if location_id is not None:
        await owned_location(db, organization_id, location_id)
        statement = statement.where(AgentConversation.location_id == location_id)

    rows = await db.scalars(
        statement.order_by(AgentConversation.created_at.desc(), AgentConversation.id.desc())
    )
    return [ConversationSummary.model_validate(row) for row in rows.all()]


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: UUID, organization_id: OrganizationId, db: DbSession
) -> ConversationDetail:
    conversation = await db.scalar(
        select(AgentConversation)
        .options(selectinload(AgentConversation.messages))
        .where(
            AgentConversation.id == conversation_id,
            AgentConversation.organization_id == organization_id,
        )
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    detail = ConversationDetail.model_validate(conversation)
    # Carries the in-flight turn so a client that reloaded mid-answer knows to keep
    # polling instead of showing a finished-looking chat the agent is still writing to.
    running = await db.scalar(
        select(AgentTurn)
        .where(AgentTurn.conversation_id == conversation.id, AgentTurn.status.in_(ACTIVE))
        .order_by(AgentTurn.created_at.desc())
        .limit(1)
    )
    detail.active_turn = TurnResponse.model_validate(running) if running else None
    return detail


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=TurnResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def post_message(
    conversation_id: UUID,
    payload: PostMessageRequest,
    organization_id: OrganizationId,
    current_user: CurrentUser,
    db: DbSession,
) -> TurnResponse:
    """Record the message and queue the agent's turn. The answer arrives by polling."""
    conversation = await owned_conversation(db, organization_id, conversation_id)

    content = payload.content.strip()
    if not content:
        raise HTTPException(status_code=422, detail="A message cannot be empty")

    # Two turns at once on one conversation would interleave their messages into a
    # transcript neither of them read, and both would replay the same history.
    await release_abandoned_turn(db, conversation.id)
    busy = await db.scalar(
        select(AgentTurn.id).where(
            AgentTurn.conversation_id == conversation.id, AgentTurn.status.in_(ACTIVE)
        )
    )
    if busy is not None:
        raise HTTPException(status_code=409, detail=BUSY_DETAIL)

    message = AgentMessage(
        conversation_id=conversation.id, role=AgentMessageRole.user, content=content
    )
    db.add(message)
    await db.flush()

    turn = AgentTurn(
        conversation_id=conversation.id,
        organization_id=organization_id,
        user_message_id=message.id,
    )
    db.add(turn)
    # Committed before the task is queued: a worker that picks the turn up immediately
    # must be able to find it, and its own message, already written.
    try:
        await db.commit()
    except IntegrityError:
        # The check above is not atomic, so a simultaneous request can get past it too.
        # A partial unique index is what actually enforces one live turn per chat.
        await db.rollback()
        raise HTTPException(status_code=409, detail=BUSY_DETAIL) from None

    from app.tasks.agent import run_agent_turn

    try:
        turn.task_id = run_agent_turn.delay(str(turn.id)).id
    except Exception as error:  # noqa: BLE001 - a broker that is down is not a 500 here
        # The turn row is already committed. Left pending it would block this chat
        # forever, since nothing is coming to pick it up.
        turn.status = AgentTurnStatus.failed
        turn.error = f"The agent could not be queued: {type(error).__name__}: {error}"[:2000]
        turn.finished_at = utcnow()
        await db.commit()
        raise HTTPException(
            status_code=503, detail="The agent is unavailable right now. Try again shortly."
        ) from error
    await db.commit()
    return TurnResponse.model_validate(turn)


async def owned_turn(db: DbSession, organization_id: UUID, turn_id: UUID) -> AgentTurn:
    turn = await db.scalar(
        select(AgentTurn).where(
            AgentTurn.id == turn_id, AgentTurn.organization_id == organization_id
        )
    )
    if turn is None:
        raise HTTPException(status_code=404, detail="Turn not found")
    return turn


@router.get("/turns/{turn_id}", response_model=TurnResponse)
async def get_turn(turn_id: UUID, organization_id: OrganizationId, db: DbSession) -> TurnResponse:
    return TurnResponse.model_validate(await owned_turn(db, organization_id, turn_id))


def one_shot(frames: list[str]) -> StreamingResponse:
    """A stream that is over before it starts, for a turn with nothing left to say."""

    async def frame() -> AsyncIterator[str]:
        for text in frames:
            yield text

    return StreamingResponse(frame(), media_type="text/event-stream", headers=SSE_HEADERS)


@router.get("/turns/{turn_id}/stream")
async def stream_turn(
    turn_id: UUID, organization_id: OrganizationId, db: DbSession
) -> StreamingResponse:
    """Watch one turn happen: its tokens, its messages, and what it is doing, as it does
    it. Scoped exactly like the poll it replaces, so another tenant's turn is a 404."""
    turn = await owned_turn(db, organization_id, turn_id)

    if turn.status in TERMINAL:
        # Its `done` was published before this request existed. Subscribing now would
        # mean waiting out the whole lifetime cap on a channel with no publisher left.
        return one_shot([sse(DONE, {"status": turn.status.value, "error": turn.error})])

    subscription = TurnSubscription(turn_id)
    try:
        await subscription.open()
    except Exception as error:  # noqa: BLE001 - a broker that is down is not a 500 here
        # Said plainly rather than as a dead stream: the client's fallback is the poll it
        # was using before, and it can only choose that if it is told to.
        raise HTTPException(
            status_code=503, detail="Live updates are unavailable. Poll the turn instead."
        ) from error

    # Re-read only now that the channel is open. In the other order a turn that finished
    # in between would be reported as running and its `done` would already be gone.
    await db.refresh(turn)
    # Read out as plain values: this request's session is closed once the response body
    # has been sent, and the generator below outlives that by a whole turn.
    opening = {"status": turn.status.value, "current_tool": turn.current_tool}
    settled = (turn.status.value, turn.error) if turn.status in TERMINAL else None

    async def events() -> AsyncIterator[str]:
        try:
            # Sent before anything is forwarded, so a client that connected late knows
            # where the turn had already got to rather than inferring it from silence.
            yield sse(STATUS, opening)
            if settled is not None:
                yield sse(DONE, {"status": settled[0], "error": settled[1]})
                return

            deadline = monotonic() + MAX_STREAM_SECONDS
            while True:
                remaining = deadline - monotonic()
                if remaining <= 0:
                    yield sse(DONE, {"status": AgentTurnStatus.failed.value, "error": ABANDONED})
                    return
                event = await subscription.next_event(min(HEARTBEAT_SECONDS, remaining))
                if event is None:
                    # An idle connection is one a proxy is entitled to drop, and a turn
                    # can think for a minute without saying anything.
                    yield ": ping\n\n"
                    continue
                name, data = event
                yield sse(name, data)
                if name == DONE:
                    return
        finally:
            # Reached on every ending this generator has, the reader closing the tab
            # included: that arrives as the generator being closed or the request task
            # being cancelled, and either is allowed to carry on once the channel is let
            # go. A subscription nobody unsubscribes holds a connection until Redis
            # notices, which is long enough to matter under a page of open chats.
            await subscription.aclose()

    return StreamingResponse(events(), media_type="text/event-stream", headers=SSE_HEADERS)
