"""The chat endpoints: what a client can post, poll and read back.

The agent itself never runs here. Queuing is stubbed the way `stub_queue` stubs audits,
so these tests assert the contract the frontend polls against - a message is recorded, a
turn is queued exactly once, and the transcript reads back in order - without a broker,
a model or a tool in the way.
"""

from datetime import timedelta
from uuid import UUID, uuid4

import pytest
from conftest import sign_in
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from test_reviews import seed_location

from app.models import (
    AgentConversation,
    AgentMessage,
    AgentMessageRole,
    AgentTurn,
    AgentTurnStatus,
    utcnow,
)

AGENT = "/api/v1/agent"


@pytest.fixture(autouse=True)
def stub_turn_queue(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Capture queued turns instead of reaching a broker."""
    queued: list[str] = []

    class Queued:
        id = "test-turn-task-id"

    def delay(turn_id: str) -> Queued:
        queued.append(turn_id)
        return Queued()

    monkeypatch.setattr("app.tasks.agent.run_agent_turn.delay", delay)
    return queued


async def start_chat(client: AsyncClient, headers: dict[str, str], location_id: str) -> str:
    response = await client.post(
        f"{AGENT}/conversations", json={"location_id": location_id}, headers=headers
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def test_every_agent_endpoint_requires_authentication(client: AsyncClient) -> None:
    assert (await client.get(f"{AGENT}/conversations")).status_code == 401
    assert (await client.post(f"{AGENT}/conversations", json={})).status_code == 401
    assert (await client.get(f"{AGENT}/conversations/{uuid4()}")).status_code == 401
    assert (await client.get(f"{AGENT}/turns/{uuid4()}")).status_code == 401


async def test_conversation_is_created_against_an_owned_location(
    client: AsyncClient, session_factory
) -> None:
    headers, org = await sign_in(client)
    location_id = await seed_location(session_factory, org, "Northstar Dental", "locations/one")

    conversation_id = await start_chat(client, headers, location_id)
    listed = await client.get(f"{AGENT}/conversations?location_id={location_id}", headers=headers)
    assert [row["id"] for row in listed.json()] == [conversation_id]
    # The location's name is the chat's name, so a picker never shows an unlabelled row.
    assert listed.json()[0]["title"] == "Northstar Dental"

    detail = await client.get(f"{AGENT}/conversations/{conversation_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["messages"] == []


async def test_a_conversation_without_a_location_is_rejected(client: AsyncClient) -> None:
    """A chat is about one profile. Without one the agent would have no boundary at all,
    so the request is refused rather than stored as a conversation about nothing."""
    headers, _ = await sign_in(client)
    response = await client.post(f"{AGENT}/conversations", json={}, headers=headers)
    assert response.status_code == 422


async def test_a_location_from_another_tenant_is_not_found(
    client: AsyncClient, session_factory
) -> None:
    _, org = await sign_in(client)
    location_id = await seed_location(session_factory, org, "Theirs", "locations/theirs")
    other, _ = await sign_in(client, "outsider@example.org", "Other organization")

    response = await client.post(
        f"{AGENT}/conversations", json={"location_id": location_id}, headers=other
    )
    assert response.status_code == 404


async def test_posting_a_message_records_it_and_queues_one_turn(
    client: AsyncClient, session_factory, stub_turn_queue: list[str]
) -> None:
    headers, org = await sign_in(client)
    location_id = await seed_location(session_factory, org, "Northstar", "locations/two")
    conversation_id = await start_chat(client, headers, location_id)

    response = await client.post(
        f"{AGENT}/conversations/{conversation_id}/messages",
        json={"content": "  reply to my unanswered reviews  "},
        headers=headers,
    )
    assert response.status_code == 202, response.text
    turn = response.json()
    assert turn["status"] == "pending"
    assert turn["conversation_id"] == conversation_id
    assert stub_turn_queue == [turn["id"]]

    async with session_factory() as db:
        message = await db.scalar(select(AgentMessage))
        assert message.role == AgentMessageRole.user
        # Stored trimmed: the model should not have to read around the user's whitespace.
        assert message.content == "reply to my unanswered reviews"
        row = await db.scalar(select(AgentTurn))
        assert row.user_message_id == message.id
        assert row.task_id == "test-turn-task-id"

    polled = await client.get(f"{AGENT}/turns/{turn['id']}", headers=headers)
    assert polled.status_code == 200
    assert polled.json()["status"] == "pending"
    assert polled.json()["current_tool"] is None

    # A client that reloaded mid-answer finds the running turn on the conversation.
    detail = (await client.get(f"{AGENT}/conversations/{conversation_id}", headers=headers)).json()
    assert detail["active_turn"]["id"] == turn["id"]

    async with session_factory() as db:
        row = await db.scalar(select(AgentTurn))
        row.status = AgentTurnStatus.succeeded
        await db.commit()
    finished = (
        await client.get(f"{AGENT}/conversations/{conversation_id}", headers=headers)
    ).json()
    assert finished["active_turn"] is None


async def test_a_second_turn_is_refused_while_one_is_running(
    client: AsyncClient, session_factory
) -> None:
    """Two turns would replay the same history and interleave into one transcript."""
    headers, org = await sign_in(client)
    location_id = await seed_location(session_factory, org, "Northstar", "locations/three")
    conversation_id = await start_chat(client, headers, location_id)
    path = f"{AGENT}/conversations/{conversation_id}/messages"

    assert (await client.post(path, json={"content": "first"}, headers=headers)).status_code == 202
    second = await client.post(path, json={"content": "second"}, headers=headers)
    assert second.status_code == 409

    async with session_factory() as db:
        turn = await db.scalar(select(AgentTurn))
        turn.status = AgentTurnStatus.succeeded
        await db.commit()

    assert (await client.post(path, json={"content": "third"}, headers=headers)).status_code == 202


async def test_an_empty_message_is_rejected(client: AsyncClient, session_factory) -> None:
    headers, org = await sign_in(client)
    location_id = await seed_location(session_factory, org, "Northstar", "locations/four")
    conversation_id = await start_chat(client, headers, location_id)
    path = f"{AGENT}/conversations/{conversation_id}/messages"

    assert (await client.post(path, json={"content": ""}, headers=headers)).status_code == 422
    assert (await client.post(path, json={"content": "   "}, headers=headers)).status_code == 422
    too_long = await client.post(path, json={"content": "x" * 4001}, headers=headers)
    assert too_long.status_code == 422


async def test_transcript_reads_back_in_order_with_tool_calls_intact(
    client: AsyncClient, session_factory
) -> None:
    """The linkage between a tool call and its result is what the next turn replays."""
    headers, org = await sign_in(client)
    location_id = await seed_location(session_factory, org, "Northstar", "locations/five")
    conversation_id = await start_chat(client, headers, location_id)

    async with session_factory() as db:
        conversation = await db.scalar(select(AgentConversation))
        db.add_all(
            [
                AgentMessage(
                    conversation_id=conversation.id,
                    role=AgentMessageRole.user,
                    content="how are the reviews",
                ),
                AgentMessage(
                    conversation_id=conversation.id,
                    role=AgentMessageRole.assistant,
                    content="",
                    tool_calls=[{"id": "call-1", "name": "list_reviews", "args": {}}],
                ),
                AgentMessage(
                    conversation_id=conversation.id,
                    role=AgentMessageRole.tool,
                    content='{"items": []}',
                    tool_call_id="call-1",
                    tool_name="list_reviews",
                ),
                AgentMessage(
                    conversation_id=conversation.id,
                    role=AgentMessageRole.assistant,
                    content="There are no reviews waiting.",
                ),
            ]
        )
        await db.commit()

    body = (
        await client.get(f"{AGENT}/conversations/{conversation_id}", headers=headers)
    ).json()
    assert [row["role"] for row in body["messages"]] == ["user", "assistant", "tool", "assistant"]
    assert body["messages"][1]["tool_calls"][0]["name"] == "list_reviews"
    assert body["messages"][2]["tool_call_id"] == "call-1"
    assert body["messages"][3]["content"] == "There are no reviews waiting."


async def test_conversations_and_turns_are_tenant_scoped(
    client: AsyncClient, session_factory
) -> None:
    headers, org = await sign_in(client)
    location_id = await seed_location(session_factory, org, "Northstar", "locations/six")
    conversation_id = await start_chat(client, headers, location_id)
    turn_id = (
        await client.post(
            f"{AGENT}/conversations/{conversation_id}/messages",
            json={"content": "hello"},
            headers=headers,
        )
    ).json()["id"]

    other, _ = await sign_in(client, "nosy@example.org", "Other organization")
    assert (
        await client.get(f"{AGENT}/conversations/{conversation_id}", headers=other)
    ).status_code == 404
    assert (await client.get(f"{AGENT}/turns/{turn_id}", headers=other)).status_code == 404
    assert (
        await client.post(
            f"{AGENT}/conversations/{conversation_id}/messages",
            json={"content": "hello"},
            headers=other,
        )
    ).status_code == 404
    assert (await client.get(f"{AGENT}/conversations", headers=other)).json() == []


async def test_unknown_ids_are_not_found(client: AsyncClient) -> None:
    headers, _ = await sign_in(client)
    missing_chat = await client.get(f"{AGENT}/conversations/{uuid4()}", headers=headers)
    assert missing_chat.status_code == 404
    assert (await client.get(f"{AGENT}/turns/{uuid4()}", headers=headers)).status_code == 404
    missing = await client.post(
        f"{AGENT}/conversations", json={"location_id": str(uuid4())}, headers=headers
    )
    assert missing.status_code == 404


async def test_conversation_ids_are_real_uuids(client: AsyncClient, session_factory) -> None:
    headers, org = await sign_in(client)
    location_id = await seed_location(session_factory, org, "Northstar", "locations/seven")
    UUID(await start_chat(client, headers, location_id))


async def test_a_turn_no_worker_can_still_be_running_stops_blocking_the_chat(
    client: AsyncClient, session_factory
) -> None:
    """A worker killed at its hard time limit never writes `failed`. Without a way out,
    the chat it died on would refuse every later message for good."""
    headers, org = await sign_in(client)
    location_id = await seed_location(session_factory, org, "Northstar", "locations/stale")
    conversation_id = await start_chat(client, headers, location_id)
    path = f"{AGENT}/conversations/{conversation_id}/messages"
    assert (await client.post(path, json={"content": "first"}, headers=headers)).status_code == 202
    assert (await client.post(path, json={"content": "again"}, headers=headers)).status_code == 409

    async with session_factory() as db:
        turn = await db.scalar(select(AgentTurn))
        turn.status = AgentTurnStatus.running
        turn.created_at = utcnow() - timedelta(hours=2)
        await db.commit()

    assert (await client.post(path, json={"content": "again"}, headers=headers)).status_code == 202
    async with session_factory() as db:
        abandoned = await db.scalar(
            select(AgentTurn).where(AgentTurn.status == AgentTurnStatus.failed)
        )
        assert abandoned is not None
        assert "stopped without finishing" in abandoned.error


async def test_a_broker_that_cannot_be_reached_fails_the_turn_instead_of_stranding_it(
    client: AsyncClient, session_factory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The turn row is committed before the task is queued, so a queue failure that left
    it `pending` would block the chat with nothing coming to pick it up."""
    headers, org = await sign_in(client)
    location_id = await seed_location(session_factory, org, "Northstar", "locations/broker")
    conversation_id = await start_chat(client, headers, location_id)

    def unreachable(turn_id: str):
        raise OSError("Connection refused")

    monkeypatch.setattr("app.tasks.agent.run_agent_turn.delay", unreachable)

    response = await client.post(
        f"{AGENT}/conversations/{conversation_id}/messages",
        json={"content": "hello"},
        headers=headers,
    )
    assert response.status_code == 503

    async with session_factory() as db:
        turn = await db.scalar(select(AgentTurn))
        assert turn.status == AgentTurnStatus.failed
        assert "could not be queued" in turn.error

    # Once the broker is back the chat still works, rather than staying wedged behind a
    # turn that never ran. Restored by re-patching, never by undoing: `monkeypatch.undo()`
    # would also drop the autouse stub and let this reach a real broker.
    class Queued:
        id = "recovered-task-id"

    monkeypatch.setattr("app.tasks.agent.run_agent_turn.delay", lambda turn_id: Queued())
    retry = await client.post(
        f"{AGENT}/conversations/{conversation_id}/messages",
        json={"content": "hello again"},
        headers=headers,
    )
    assert retry.status_code == 202


async def test_the_database_refuses_a_second_live_turn_even_if_the_check_is_passed(
    client: AsyncClient, session_factory
) -> None:
    """The API's check is not atomic, so the index is what actually holds the invariant."""
    headers, org = await sign_in(client)
    location_id = await seed_location(session_factory, org, "Northstar", "locations/race")
    conversation_id = await start_chat(client, headers, location_id)
    await client.post(
        f"{AGENT}/conversations/{conversation_id}/messages",
        json={"content": "first"},
        headers=headers,
    )

    async with session_factory() as db:
        conversation = await db.scalar(select(AgentConversation))
        message = AgentMessage(
            conversation_id=conversation.id, role=AgentMessageRole.user, content="racing"
        )
        db.add(message)
        await db.flush()
        db.add(
            AgentTurn(
                conversation_id=conversation.id,
                organization_id=conversation.organization_id,
                user_message_id=message.id,
            )
        )
        with pytest.raises(IntegrityError):
            await db.commit()
