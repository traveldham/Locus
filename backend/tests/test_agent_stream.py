"""Watching a turn happen: what the worker publishes and what the endpoint forwards.

The turn runs in a worker and the reader is attached to the API, so these two halves
never share a process in production. Here they share an event loop and an in-process
broker, which is enough to assert the contract a browser codes against: the event names,
their payloads, the order they arrive in, and the one event that says it is over.

The other half of what is asserted is what streaming is *not* allowed to do. A broker
that is down must cost a reader its animation and a turn nothing, so the turn that runs
against a failing publisher is expected to succeed and to have written every message it
would have written with nobody watching at all.
"""

import asyncio
import json
from uuid import UUID

import pytest
from conftest import sign_in
from httpx import AsyncClient
from langchain_core.messages import AIMessage, AIMessageChunk, ToolMessage
from sqlalchemy import select
from test_agent_turn import make_turn, use_model
from test_reviews import seed_location

from app.api.agent import ABANDONED
from app.models import AgentMessage, AgentMessageRole, AgentTurn, AgentTurnStatus, utcnow
from app.services.agent.stream import TurnEvents, channel, sse
from app.tasks.agent import delta_text, run_turn
from stubs import FakeRedisBroker, StreamingChatModel, StubChatModel

AGENT = "/api/v1/agent"


@pytest.fixture(autouse=True)
def stub_turn_queue(monkeypatch: pytest.MonkeyPatch) -> None:
    """Capture queued turns instead of reaching a broker."""

    class Queued:
        id = "test-turn-task-id"

    monkeypatch.setattr("app.tasks.agent.run_agent_turn.delay", lambda turn_id: Queued())


@pytest.fixture(autouse=True)
def bounded_stream(monkeypatch: pytest.MonkeyPatch) -> None:
    """Shorten the lifetime cap. A test that stops forwarding for the wrong reason should
    fail in seconds rather than sit out the whole of a turn's timeout."""
    monkeypatch.setattr("app.api.agent.MAX_STREAM_SECONDS", 2.0)


def frames(text: str) -> list[tuple[str, dict]]:
    """The `event: ... / data: ...` pairs in a stream, heartbeat comments dropped."""
    parsed: list[tuple[str, dict]] = []
    for block in text.split("\n\n"):
        if not block.strip() or block.startswith(":"):
            continue
        fields = dict(line.split(": ", 1) for line in block.splitlines())
        parsed.append((fields["event"], json.loads(fields["data"])))
    return parsed


def published(broker: FakeRedisBroker, turn_id) -> list[tuple[str, dict]]:
    """What the worker put on one turn's channel, in order."""
    name = channel(turn_id)
    return [
        (json.loads(payload)["event"], json.loads(payload)["data"])
        for topic, payload in broker.published
        if topic == name
    ]


async def pending_turn(client: AsyncClient, session_factory) -> tuple[dict[str, str], UUID]:
    """Sign in, start a chat and leave a turn waiting, with no worker to answer it."""
    headers, org = await sign_in(client)
    location_id = await seed_location(session_factory, org, "Northstar Dental", "locations/live")
    conversation_id = (
        await client.post(
            f"{AGENT}/conversations", json={"location_id": location_id}, headers=headers
        )
    ).json()["id"]
    turn_id = (
        await client.post(
            f"{AGENT}/conversations/{conversation_id}/messages",
            json={"content": "what is going on"},
            headers=headers,
        )
    ).json()["id"]
    return headers, UUID(turn_id)


async def test_the_stream_requires_authentication(client: AsyncClient, session_factory) -> None:
    _, turn_id = await pending_turn(client, session_factory)
    assert (await client.get(f"{AGENT}/turns/{turn_id}/stream")).status_code == 401


async def test_a_turn_from_another_tenant_is_not_found(
    client: AsyncClient, session_factory, turn_stream: FakeRedisBroker
) -> None:
    """Scoped exactly like the poll it replaces: a stream is a live read of a turn, so
    the answer for somebody else's turn is the same 404 the read gives."""
    _, turn_id = await pending_turn(client, session_factory)
    intruder, _ = await sign_in(client, "other@example.com", "Harbour Group", "Other Owner")

    response = await client.get(f"{AGENT}/turns/{turn_id}/stream", headers=intruder)

    assert response.status_code == 404
    assert turn_stream.subscribers(channel(turn_id)) == 0


async def test_a_finished_turn_says_so_at_once_and_subscribes_to_nothing(
    client: AsyncClient, session_factory, turn_stream: FakeRedisBroker
) -> None:
    """The `done` for a turn that is already over was published before this request
    existed. Subscribing for it would be waiting out the lifetime cap on a dead channel."""
    headers, turn_id = await pending_turn(client, session_factory)
    async with session_factory() as db:
        turn = await db.get(AgentTurn, turn_id)
        turn.status = AgentTurnStatus.failed
        turn.error = "Vertex said no"
        turn.finished_at = utcnow()
        await db.commit()

    response = await client.get(f"{AGENT}/turns/{turn_id}/stream", headers=headers)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert frames(response.text) == [("done", {"status": "failed", "error": "Vertex said no"})]
    assert turn_stream.subscribers(channel(turn_id)) == 0


async def test_events_are_forwarded_in_order_and_the_stream_closes_on_done(
    client: AsyncClient, session_factory, turn_stream: FakeRedisBroker
) -> None:
    """The whole contract in one test: the opening status, then whatever the worker says,
    in the order it said it, and nothing at all after `done`."""
    headers, turn_id = await pending_turn(client, session_factory)
    events = TurnEvents(turn_id)

    reading = asyncio.create_task(client.get(f"{AGENT}/turns/{turn_id}/stream", headers=headers))
    await turn_stream.wait_for_subscriber(channel(turn_id))
    await events.status(AgentTurnStatus.running, "list_reviews")
    await events.token("Nothing ")
    await events.token("needs attention.")
    await events.done(AgentTurnStatus.succeeded, None)
    # Nobody is listening for this one: the reader left on `done`.
    await events.token("too late")
    response = await reading

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-cache"
    assert response.headers["x-accel-buffering"] == "no"
    assert frames(response.text) == [
        ("status", {"status": "pending", "current_tool": None}),
        ("status", {"status": "running", "current_tool": "list_reviews"}),
        ("token", {"text": "Nothing "}),
        ("token", {"text": "needs attention."}),
        ("done", {"status": "succeeded", "error": None}),
    ]
    # The subscription is let go on the way out, whichever way out it was.
    assert turn_stream.subscribers(channel(turn_id)) == 0


async def test_a_stream_that_hears_nothing_is_kept_alive_with_comments(
    client: AsyncClient, session_factory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An agent can think for a minute without producing a word, and a proxy in front of
    this API will drop a connection that quiet unless something keeps arriving on it."""
    headers, turn_id = await pending_turn(client, session_factory)
    monkeypatch.setattr("app.api.agent.HEARTBEAT_SECONDS", 0.01)
    events = TurnEvents(turn_id)

    reading = asyncio.create_task(client.get(f"{AGENT}/turns/{turn_id}/stream", headers=headers))
    await asyncio.sleep(0.05)
    await events.done(AgentTurnStatus.succeeded, None)
    response = await reading

    assert ": ping\n\n" in response.text
    # A comment is not an event: it must not land in the transcript a client is building.
    assert frames(response.text)[-1] == ("done", {"status": "succeeded", "error": None})


async def test_a_stream_cannot_outlive_the_turn_it_is_watching(
    client: AsyncClient, session_factory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A worker killed at its hard time limit publishes nothing on the way out, so the
    cap is the reader's only way to stop waiting for an event that is not coming."""
    headers, turn_id = await pending_turn(client, session_factory)
    monkeypatch.setattr("app.api.agent.MAX_STREAM_SECONDS", 0.05)

    response = await client.get(f"{AGENT}/turns/{turn_id}/stream", headers=headers)

    assert frames(response.text)[-1] == ("done", {"status": "failed", "error": ABANDONED})


async def test_a_reader_that_leaves_mid_stream_gives_up_its_subscription(
    client: AsyncClient, session_factory, turn_stream: FakeRedisBroker
) -> None:
    """A closed tab reaches the generator as a close, not as an event, so the cleanup has
    to be in a `finally`. A subscription nobody drops holds a connection until Redis
    notices, which is long enough to matter with a page of open chats."""
    from app.api.agent import stream_turn

    _, turn_id = await pending_turn(client, session_factory)

    async with session_factory() as db:
        organization_id = (await db.scalar(select(AgentTurn))).organization_id
        response = await stream_turn(turn_id, organization_id, db)
        body = response.body_iterator
        assert await anext(body) == sse("status", {"status": "pending", "current_tool": None})
        assert turn_stream.subscribers(channel(turn_id)) == 1

        await body.aclose()

    assert turn_stream.subscribers(channel(turn_id)) == 0


async def test_a_whole_turn_is_announced_as_it_is_written(
    client: AsyncClient, session_factory, monkeypatch: pytest.MonkeyPatch, turn_stream
) -> None:
    """What the worker publishes for a real turn, alongside what it stored. The message
    events carry the REST shape so a client can append them to what it already has."""
    turn_id, _ = await make_turn(client, session_factory)
    use_model(monkeypatch, StubChatModel([AIMessage(content="Nothing needs attention today.")]))

    await run_turn(turn_id, session_factory)

    events = published(turn_stream, turn_id)
    assert [name for name, _ in events] == ["status", "message", "done"]
    assert events[0][1] == {"status": "running", "current_tool": None}
    assert events[-1][1] == {"status": "succeeded", "error": None}

    async with session_factory() as db:
        row = await db.scalar(
            select(AgentMessage).where(AgentMessage.role == AgentMessageRole.assistant)
        )
        stored_id = str(row.id)
    assert events[1][1] == {
        "id": stored_id,
        "role": "assistant",
        "content": "Nothing needs attention today.",
        "tool_calls": None,
        "tool_call_id": None,
        "tool_name": None,
        "created_at": events[1][1]["created_at"],
    }


async def test_the_tool_a_turn_is_running_is_announced_when_it_changes(
    client: AsyncClient,
    session_factory,
    monkeypatch: pytest.MonkeyPatch,
    turn_stream,
    stub_providers,
) -> None:
    """The chip that reads "Checking reviews…" is driven by these, and a status per
    message rather than per change would flicker it on and off between every one."""
    turn_id, _ = await make_turn(client, session_factory, "any reviews waiting?")
    use_model(
        monkeypatch,
        StubChatModel(
            [
                AIMessage(
                    content="", tool_calls=[{"id": "c1", "name": "list_reviews", "args": {}}]
                ),
                AIMessage(content="Nothing is waiting."),
            ]
        ),
    )

    await run_turn(turn_id, session_factory)

    statuses = [data for name, data in published(turn_stream, turn_id) if name == "status"]
    assert statuses == [
        {"status": "running", "current_tool": None},
        {"status": "running", "current_tool": "list_reviews"},
        {"status": "running", "current_tool": None},
    ]


async def test_a_broker_that_is_down_costs_the_turn_nothing(
    client: AsyncClient, session_factory, monkeypatch: pytest.MonkeyPatch, turn_stream
) -> None:
    """The invariant the whole streaming path is subordinate to. Publishing is a view of
    a turn, so a turn whose view cannot be delivered still runs, still writes its
    transcript, and still succeeds."""
    turn_id, _ = await make_turn(client, session_factory)
    turn_stream.fail()
    use_model(monkeypatch, StubChatModel([AIMessage(content="Nothing needs attention today.")]))

    await run_turn(turn_id, session_factory)

    assert turn_stream.published == []
    async with session_factory() as db:
        turn = await db.get(AgentTurn, turn_id)
        assert turn.status == AgentTurnStatus.succeeded
        assert turn.error is None
        rows = (await db.scalars(select(AgentMessage).order_by(AgentMessage.created_at))).all()
        assert [row.role for row in rows] == [AgentMessageRole.user, AgentMessageRole.assistant]
        assert rows[-1].content == "Nothing needs attention today."


async def test_a_failed_turn_still_tells_its_reader_it_is_over(
    client: AsyncClient, session_factory, monkeypatch: pytest.MonkeyPatch, turn_stream
) -> None:
    """`done` is the only event a client cannot do without: without it a failed turn is
    indistinguishable from one still thinking, and the composer stays disabled."""
    turn_id, _ = await make_turn(client, session_factory)

    class Exploding(StubChatModel):
        async def ainvoke(self, messages, **kwargs):
            raise RuntimeError("Vertex said no")

    use_model(monkeypatch, Exploding([]))

    await run_turn(turn_id, session_factory)

    name, data = published(turn_stream, turn_id)[-1]
    assert name == "done"
    assert data["status"] == "failed"
    assert "Vertex said no" in data["error"]
    async with session_factory() as db:
        # What the reader was told and what a reload would show are the same words.
        assert (await db.get(AgentTurn, turn_id)).error == data["error"]


async def test_a_turn_nobody_claimed_publishes_nothing(
    client: AsyncClient, session_factory, monkeypatch: pytest.MonkeyPatch, turn_stream
) -> None:
    """A second worker losing the claim race must not publish `done` onto a channel the
    winner is still writing to, which is why the publisher is opened after the claim."""
    turn_id, _ = await make_turn(client, session_factory)
    async with session_factory() as db:
        turn = await db.get(AgentTurn, turn_id)
        turn.status = AgentTurnStatus.running
        await db.commit()
    use_model(monkeypatch, StubChatModel([AIMessage(content="should never be asked")]))

    await run_turn(turn_id, session_factory)

    assert published(turn_stream, turn_id) == []


async def test_the_answer_arrives_a_word_at_a_time_and_is_stored_whole(
    client: AsyncClient, session_factory, monkeypatch: pytest.MonkeyPatch, turn_stream
) -> None:
    """The point of all of this, against a real chat model and real LangGraph plumbing.

    The node still calls `ainvoke`: LangGraph's messages handler is a streaming callback
    handler, and `BaseChatModel` routes an invoke through `_astream` whenever one is
    attached. So the deltas arrive without the graph knowing it is being watched - and
    the transcript is still written once, whole, from the `values` stream.
    """
    turn_id, _ = await make_turn(client, session_factory)
    answer = AIMessage(content="Nothing needs attention today.")
    use_model(monkeypatch, StreamingChatModel(messages=iter([answer])))

    await run_turn(turn_id, session_factory)

    events = published(turn_stream, turn_id)
    assert "".join(data["text"] for name, data in events if name == "token") == answer.content
    # One stored message, not one per token: the stream is a view, never the record.
    assert [name for name, _ in events].count("message") == 1
    async with session_factory() as db:
        rows = (await db.scalars(select(AgentMessage).order_by(AgentMessage.created_at))).all()
        assert [row.content for row in rows] == ["what is going on", answer.content]
        assert (await db.get(AgentTurn, turn_id)).status == AgentTurnStatus.succeeded


def test_only_assistant_chunks_are_tokens() -> None:
    """`stream_mode="messages"` is not a token stream. LangGraph puts every node's
    finished output on it too, so a completed answer and a whole tool result arrive there
    alongside the deltas - forwarding those would send the reply twice and print tool
    output as if the agent had said it."""
    assert delta_text((AIMessageChunk(content="Noth"), {})) == "Noth"
    # Content blocks, which is the shape a provider returns once output_version is v1.
    assert delta_text((AIMessageChunk(content=[{"type": "text", "text": "ing"}]), {})) == "ing"
    assert delta_text((AIMessage(content="Nothing needs attention."), {})) == ""
    assert delta_text((ToolMessage(content="[]", tool_call_id="c1"), {})) == ""
    # A tool-call delta carries no text of its own, and its arguments are not words.
    assert delta_text((AIMessageChunk(content=""), {})) == ""
    assert delta_text({"messages": []}) == ""
