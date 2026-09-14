"""Running one turn end to end: the graph's messages become the transcript.

This is the seam between the loop and the database. The model is scripted and the tools
are the real ones, so what is asserted here is the part that has to survive a worker
restart: every message the agent produced was written, in order, with the linkage a later
turn needs, and a turn that fails says why instead of vanishing.
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from conftest import sign_in
from httpx import AsyncClient
from langchain_core.messages import AIMessage
from sqlalchemy import select
from test_reviews import seed_location

from app.models import (
    AgentConversation,
    AgentMessage,
    AgentMessageRole,
    AgentTurn,
    AgentTurnStatus,
    Review,
)
from app.tasks.agent import run_turn
from stubs import StubChatModel


async def make_turn(
    client: AsyncClient, session_factory, content: str = "what is going on"
) -> tuple[UUID, UUID]:
    """A conversation with one user message and a pending turn, ready to run."""
    headers, org = await sign_in(client)
    location_id = await seed_location(session_factory, org, "Northstar Dental", "locations/turn")
    conversation_id = (
        await client.post(
            "/api/v1/agent/conversations", json={"location_id": location_id}, headers=headers
        )
    ).json()["id"]
    turn_id = (
        await client.post(
            f"/api/v1/agent/conversations/{conversation_id}/messages",
            json={"content": content},
            headers=headers,
        )
    ).json()["id"]
    return UUID(turn_id), UUID(location_id)


def use_model(monkeypatch: pytest.MonkeyPatch, model: StubChatModel) -> None:
    monkeypatch.setattr("app.tasks.agent.build_chat_model", lambda settings: model)


async def test_a_plain_answer_is_written_and_the_turn_succeeds(
    client: AsyncClient, session_factory, monkeypatch: pytest.MonkeyPatch
) -> None:
    turn_id, _ = await make_turn(client, session_factory)
    model = StubChatModel([AIMessage(content="Nothing needs attention today.")])
    use_model(monkeypatch, model)

    await run_turn(turn_id, session_factory)

    async with session_factory() as db:
        turn = await db.get(AgentTurn, turn_id)
        assert turn.status == AgentTurnStatus.succeeded
        assert turn.error is None
        assert turn.current_tool is None
        assert turn.started_at is not None and turn.finished_at is not None
        rows = (await db.scalars(select(AgentMessage).order_by(AgentMessage.created_at))).all()
        assert [row.role for row in rows] == [AgentMessageRole.user, AgentMessageRole.assistant]
        assert rows[-1].content == "Nothing needs attention today."

    # The user's message was replayed to the model, behind the system prompt.
    assert model.calls[0][0].type == "system"
    assert "Northstar Dental" in model.calls[0][0].content


async def test_a_tool_call_runs_and_every_message_lands_in_order(
    client: AsyncClient, session_factory, monkeypatch: pytest.MonkeyPatch, stub_providers
) -> None:
    turn_id, location_id = await make_turn(client, session_factory, "any reviews waiting?")
    async with session_factory() as db:
        conversation = await db.scalar(select(AgentConversation))
        db.add(
            Review(
                organization_id=conversation.organization_id,
                location_id=location_id,
                google_review_id="rev-1",
                reviewer_display_name="Jordan M.",
                star_rating=2,
                comment="Waited forty minutes.",
                create_time=datetime.now(UTC),
            )
        )
        await db.commit()

    model = StubChatModel(
        [
            AIMessage(
                content="",
                tool_calls=[{"id": "call-1", "name": "list_reviews", "args": {}}],
            ),
            AIMessage(content="One review from Jordan M. is unanswered."),
        ]
    )
    use_model(monkeypatch, model)

    await run_turn(turn_id, session_factory)

    async with session_factory() as db:
        turn = await db.get(AgentTurn, turn_id)
        assert turn.status == AgentTurnStatus.succeeded
        ordered = select(AgentMessage).order_by(AgentMessage.created_at, AgentMessage.id)
        rows = (await db.scalars(ordered)).all()
        assert [row.role for row in rows] == [
            AgentMessageRole.user,
            AgentMessageRole.assistant,
            AgentMessageRole.tool,
            AgentMessageRole.assistant,
        ]
        # The linkage a later turn replays: the call id on both sides.
        assert rows[1].tool_calls[0]["id"] == "call-1"
        assert rows[2].tool_call_id == "call-1"
        assert rows[2].tool_name == "list_reviews"
        assert "Jordan M." in rows[2].content
        assert rows[3].content == "One review from Jordan M. is unanswered."

    # The tool's result really did go back to the model on the second call.
    assert any(message.type == "tool" for message in model.calls[1])


async def test_a_model_that_cannot_be_reached_fails_the_turn_with_the_reason(
    client: AsyncClient, session_factory, monkeypatch: pytest.MonkeyPatch
) -> None:
    turn_id, _ = await make_turn(client, session_factory)

    def explode(settings):
        from app.services.agent.llm import AgentUnavailable

        raise AgentUnavailable("Set VERTEX_PROJECT to use the agent.")

    monkeypatch.setattr("app.tasks.agent.build_chat_model", explode)

    await run_turn(turn_id, session_factory)

    async with session_factory() as db:
        turn = await db.get(AgentTurn, turn_id)
        assert turn.status == AgentTurnStatus.failed
        assert "VERTEX_PROJECT" in turn.error
        assert turn.finished_at is not None


async def test_a_model_that_raises_mid_turn_fails_the_turn_rather_than_the_worker(
    client: AsyncClient, session_factory, monkeypatch: pytest.MonkeyPatch
) -> None:
    turn_id, _ = await make_turn(client, session_factory)

    class Exploding(StubChatModel):
        async def ainvoke(self, messages, **kwargs):
            raise RuntimeError("Vertex said no")

    use_model(monkeypatch, Exploding([]))

    # The worker must come back, not propagate.
    await run_turn(turn_id, session_factory)

    async with session_factory() as db:
        turn = await db.get(AgentTurn, turn_id)
        assert turn.status == AgentTurnStatus.failed
        assert "Vertex said no" in turn.error


async def test_a_turn_that_is_not_pending_is_left_alone(
    client: AsyncClient, session_factory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two workers must not both answer one message."""
    turn_id, _ = await make_turn(client, session_factory)
    async with session_factory() as db:
        turn = await db.get(AgentTurn, turn_id)
        turn.status = AgentTurnStatus.running
        await db.commit()

    model = StubChatModel([AIMessage(content="should never be asked")])
    use_model(monkeypatch, model)

    await run_turn(turn_id, session_factory)

    assert model.calls == []
    async with session_factory() as db:
        assert (await db.get(AgentTurn, turn_id)).status == AgentTurnStatus.running


async def test_a_missing_turn_is_a_no_op(session_factory) -> None:
    await run_turn(uuid4(), session_factory)


async def test_a_turn_that_produced_no_answer_fails_rather_than_succeeding_silently(
    client: AsyncClient, session_factory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Live models do return an empty message. Calling that a success leaves the reader
    with a re-enabled composer and no reply, which reads as the product being broken."""
    turn_id, _ = await make_turn(client, session_factory)
    use_model(monkeypatch, StubChatModel([AIMessage(content="")]))

    await run_turn(turn_id, session_factory)

    async with session_factory() as db:
        turn = await db.get(AgentTurn, turn_id)
        assert turn.status == AgentTurnStatus.failed
        assert "did not return an answer" in turn.error
        # The empty message is not kept: it would be a blank bubble, and it would be
        # replayed as noise on every later turn.
        rows = (await db.scalars(select(AgentMessage))).all()
        assert [row.role for row in rows] == [AgentMessageRole.user]


async def test_an_earlier_turn_is_replayed_to_the_model(
    client: AsyncClient, session_factory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The second turn has to see the first one, or the chat has no memory."""
    turn_id, _ = await make_turn(client, session_factory, "first question")
    use_model(monkeypatch, StubChatModel([AIMessage(content="first answer")]))
    await run_turn(turn_id, session_factory)

    # The follow-up is written straight to the database: the endpoint is covered
    # elsewhere, and this test is about what the second turn replays.
    async with session_factory() as db:
        conversation = await db.scalar(select(AgentConversation))
        message = AgentMessage(
            conversation_id=conversation.id,
            role=AgentMessageRole.user,
            content="second question",
        )
        db.add(message)
        await db.flush()
        second = AgentTurn(
            conversation_id=conversation.id,
            organization_id=conversation.organization_id,
            user_message_id=message.id,
        )
        db.add(second)
        await db.commit()
        second_id = second.id

    model = StubChatModel([AIMessage(content="second answer")])
    use_model(monkeypatch, model)
    await run_turn(second_id, session_factory)

    replayed = [m.content for m in model.calls[0] if m.type in ("human", "ai")]
    assert replayed == ["first question", "first answer", "second question"]
