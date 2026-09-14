"""The live view of a running turn, carried from the worker that runs it to the API.

A turn runs in a Celery worker; the browser is attached to the API. Neither process can
see the other's memory, so the two are joined by one Redis pub/sub channel per turn -
Redis is already the Celery broker, so a token-by-token transcript costs no new
infrastructure and nothing new to deploy.

What travels over that channel is a *view* of the turn, never the turn itself. Every
message the agent produces is still committed to `agent_messages` by the worker, and
that transcript remains the only source of truth: a reader who subscribed late, missed
an event, or never subscribed at all still gets the whole answer by reading the
conversation back. That is the invariant this module exists to protect, and it is why
publishing here swallows everything it catches. A broker that is down should cost a
reader an animation, never a user their answer.
"""

from __future__ import annotations

import json
import logging
from typing import Any
from uuid import UUID

from redis.asyncio import Redis
from redis.asyncio.client import PubSub

from app.core.config import get_settings
from app.models import AgentMessage, AgentTurnStatus
from app.schemas.agent import AgentMessageResponse

logger = logging.getLogger(__name__)

# The four things a reader is told. `done` is the only one that is load-bearing: it is
# what lets a client stop waiting, so it is published on every exit path a turn has.
TOKEN = "token"
MESSAGE = "message"
STATUS = "status"
DONE = "done"

# An idle stream is indistinguishable from a dead one to a proxy, and the ones in front
# of this API will close it. A comment frame costs four bytes and keeps it open.
HEARTBEAT_SECONDS = 15.0

# How long to wait for the server to confirm a subscription before giving up on it.
SUBSCRIBE_TIMEOUT_SECONDS = 5.0


def channel(turn_id: UUID) -> str:
    return f"agent:turn:{turn_id}"


def redis_client() -> Redis:
    """A connection to the broker Redis, decoded to `str` on the way in and out.

    This is the one seam the tests replace; everything else in this module runs for real
    against whatever this hands back.
    """
    return Redis.from_url(get_settings().redis_url, decode_responses=True)


def encode(event: str, data: dict[str, Any]) -> str:
    """One event as it travels on the channel: its name alongside its payload, because a
    subscriber reading a bare object would have no way to tell a token from a status."""
    return json.dumps({"event": event, "data": data})


def decode(payload: str | bytes) -> tuple[str, dict[str, Any]] | None:
    """Read an event back, or `None` for anything that is not one of ours.

    A pub/sub channel is a public place. Nothing published there is trusted enough to be
    allowed to end a reader's stream by raising inside its generator.
    """
    try:
        if isinstance(payload, bytes):
            payload = payload.decode()
        envelope = json.loads(payload)
    except (UnicodeDecodeError, ValueError):
        return None
    if not isinstance(envelope, dict):
        return None
    event, data = envelope.get("event"), envelope.get("data")
    if not isinstance(event, str) or not isinstance(data, dict):
        return None
    return event, data


def sse(event: str, data: dict[str, Any]) -> str:
    """One server-sent event. The `data` field of an SSE frame cannot carry a raw
    newline - it would end the frame early - which is exactly what `json.dumps` escapes."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


class TurnEvents:
    """The worker's end of one turn's channel.

    Every method here is best-effort by design. A turn's correctness does not depend on
    anyone listening, so a broker that is unreachable, a channel nobody reads, or a value
    that will not serialise is logged and stepped over rather than raised at the caller.
    """

    def __init__(self, turn_id: UUID) -> None:
        self._channel = channel(turn_id)
        self._client: Redis | None = None
        # Latched by the first failure. A broker that refused one publish will refuse the
        # next fifty, and a turn that emits four hundred token deltas must not pay a
        # connection timeout for each of them.
        self._broken = False

    async def publish(self, event: str, data: dict[str, Any]) -> None:
        if self._broken:
            return
        try:
            if self._client is None:
                self._client = redis_client()
            await self._client.publish(self._channel, encode(event, data))
        except Exception:  # noqa: BLE001 - a reader's animation is never worth a turn
            logger.warning(
                "Could not publish %s on %s", event, self._channel, exc_info=True
            )
            self._broken = True

    async def token(self, text: str) -> None:
        if text:
            await self.publish(TOKEN, {"text": text})

    async def message(self, row: AgentMessage) -> None:
        """A message that is now in the transcript, in the shape the REST API returns it
        in, so a client can append it to what it already has without a second read."""
        try:
            data = AgentMessageResponse.model_validate(row).model_dump(mode="json")
        except Exception:  # noqa: BLE001 - the row is written; only its echo failed
            logger.warning("Could not serialise agent message %s", row.id, exc_info=True)
            return
        await self.publish(MESSAGE, data)

    async def status(self, status: AgentTurnStatus, current_tool: str | None) -> None:
        await self.publish(STATUS, {"status": status.value, "current_tool": current_tool})

    async def done(self, status: AgentTurnStatus, error: str | None) -> None:
        """The last thing a reader hears, and the only event it needs to stop waiting.

        A publisher latched shut by an earlier failure is given one more attempt here: a
        reader that never hears this waits out the stream's whole lifetime cap.
        """
        self._broken = False
        await self.publish(DONE, {"status": status.value, "error": error})

    async def aclose(self) -> None:
        client, self._client = self._client, None
        if client is None:
            return
        try:
            await client.aclose()
        except Exception:  # noqa: BLE001 - the turn is over; a leaked socket is not its problem
            logger.warning("Could not close the stream connection for %s", self._channel)


class TurnSubscription:
    """A reader's end of one turn's channel.

    Opening is separate from reading so the API can subscribe *before* it re-reads the
    turn's state. In the other order there is a window in which the turn finishes, its
    `done` is published to nobody, and the reader then settles in to wait for an event
    that has already been and gone.
    """

    def __init__(self, turn_id: UUID) -> None:
        self._channel = channel(turn_id)
        self._client: Redis | None = None
        self._pubsub: PubSub | None = None

    async def open(self) -> None:
        """Subscribe, and wait for the server to say so. `subscribe` only writes the
        command; without the confirmation "subscribed before I looked" would not hold."""
        self._client = redis_client()
        self._pubsub = self._client.pubsub()
        await self._pubsub.subscribe(self._channel)
        await self._pubsub.get_message(timeout=SUBSCRIBE_TIMEOUT_SECONDS)

    async def next_event(self, timeout: float) -> tuple[str, dict[str, Any]] | None:
        """The next event on the channel, or `None` if `timeout` passed without one.

        Anything unreadable is reported as nothing rather than raised: the caller's only
        reaction to `None` is a heartbeat, which is the right thing to do about a message
        that meant nothing to us either.
        """
        if self._pubsub is None:
            return None
        message = await self._pubsub.get_message(
            ignore_subscribe_messages=True, timeout=timeout
        )
        if message is None or message.get("type") != "message":
            return None
        return decode(message["data"])

    async def aclose(self) -> None:
        pubsub, client = self._pubsub, self._client
        self._pubsub = self._client = None
        for closing in (pubsub, client):
            if closing is None:
                continue
            try:
                await closing.aclose()
            except Exception:  # noqa: BLE001 - the reader is gone either way
                logger.warning("Could not close a subscription to %s", self._channel)


__all__ = [
    "DONE",
    "HEARTBEAT_SECONDS",
    "MESSAGE",
    "STATUS",
    "TOKEN",
    "TurnEvents",
    "TurnSubscription",
    "channel",
    "decode",
    "encode",
    "redis_client",
    "sse",
]
