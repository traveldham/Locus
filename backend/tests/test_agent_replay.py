"""Replaying a transcript that was stored in a shape the protocol rejects.

A turn can die between asking for a tool and recording what it returned - a crash, the
recursion limit, a worker killed at its time limit. What is left behind is an assistant
message whose tool calls nothing answers, and sending that to the model is not a degraded
request but an invalid one. Untreated, a single interrupted turn would end the conversation
permanently, so these are the cases that have to come back replayable.
"""

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.models import AgentMessage, AgentMessageRole
from app.services.agent.graph import (
    MAX_REPLAYED_MESSAGES,
    UNFINISHED,
    to_langchain_messages,
)


def row(role: AgentMessageRole, content: str = "", **kwargs) -> AgentMessage:
    return AgentMessage(role=role, content=content, **kwargs)


def call(call_id: str, name: str = "list_reviews") -> dict:
    return {"id": call_id, "name": name, "args": {}}


def test_an_unanswered_tool_call_is_given_a_result_so_the_chat_survives() -> None:
    """The transcript a crashed turn leaves behind."""
    replayed = to_langchain_messages(
        [
            row(AgentMessageRole.user, "any reviews waiting?"),
            row(AgentMessageRole.assistant, "", tool_calls=[call("c1")]),
            # The turn died here: no tool row was ever written.
            row(AgentMessageRole.user, "are you there?"),
        ]
    )

    assert [type(m).__name__ for m in replayed] == [
        "HumanMessage",
        "AIMessage",
        "ToolMessage",
        "HumanMessage",
    ]
    answer = replayed[2]
    assert answer.tool_call_id == "c1"
    assert answer.content == UNFINISHED
    assert replayed[3].content == "are you there?"


def test_every_call_in_a_parallel_request_is_answered() -> None:
    replayed = to_langchain_messages(
        [
            row(AgentMessageRole.user, "check everything"),
            row(
                AgentMessageRole.assistant,
                "",
                tool_calls=[call("c1", "list_reviews"), call("c2", "get_latest_audit")],
            ),
            row(
                AgentMessageRole.tool,
                '{"items": []}',
                tool_call_id="c1",
                tool_name="list_reviews",
            ),
        ]
    )

    assert [m.tool_call_id for m in replayed if isinstance(m, ToolMessage)] == ["c1", "c2"]
    assert replayed[-1].content == UNFINISHED


def test_a_result_whose_call_is_missing_is_dropped() -> None:
    """The inverse orphan: a call id that never made it onto the assistant row."""
    replayed = to_langchain_messages(
        [
            row(AgentMessageRole.user, "hello"),
            row(AgentMessageRole.tool, "stray", tool_call_id="ghost", tool_name="list_reviews"),
            row(AgentMessageRole.assistant, "Nothing to report."),
        ]
    )

    assert [type(m).__name__ for m in replayed] == ["HumanMessage", "AIMessage"]
    assert not any(isinstance(m, ToolMessage) for m in replayed)


def test_a_healthy_exchange_is_replayed_unchanged() -> None:
    replayed = to_langchain_messages(
        [
            row(AgentMessageRole.user, "any reviews?"),
            row(AgentMessageRole.assistant, "", tool_calls=[call("c1")]),
            row(
                AgentMessageRole.tool,
                '{"items": []}',
                tool_call_id="c1",
                tool_name="list_reviews",
            ),
            row(AgentMessageRole.assistant, "None waiting."),
        ]
    )

    assert [type(m).__name__ for m in replayed] == [
        "HumanMessage",
        "AIMessage",
        "ToolMessage",
        "AIMessage",
    ]
    assert replayed[2].content == '{"items": []}'
    assert UNFINISHED not in str(replayed[2].content)


def test_only_the_most_recent_messages_are_replayed() -> None:
    total = MAX_REPLAYED_MESSAGES * 2
    rows = [row(AgentMessageRole.user, f"message {index}") for index in range(total)]

    replayed = to_langchain_messages(rows)

    assert len(replayed) == MAX_REPLAYED_MESSAGES
    assert isinstance(replayed[0], HumanMessage)
    # The tail is what survives, so the newest exchange is always present.
    assert replayed[-1].content == f"message {total - 1}"


def test_a_result_stranded_by_the_window_does_not_come_back_alone() -> None:
    """Cutting mid-exchange must not leave a result whose call is on the far side."""
    rows = [row(AgentMessageRole.user, f"filler {index}") for index in range(MAX_REPLAYED_MESSAGES)]
    rows += [
        row(AgentMessageRole.assistant, "", tool_calls=[call("c1")]),
        row(AgentMessageRole.tool, "result", tool_call_id="c1", tool_name="list_reviews"),
    ]

    replayed = to_langchain_messages(rows)

    assert len(replayed) == MAX_REPLAYED_MESSAGES
    tool_messages = [m for m in replayed if isinstance(m, ToolMessage)]
    # Either the call came along with it or neither did, but never the result on its own.
    for message in tool_messages:
        position = replayed.index(message)
        preceding = replayed[:position]
        assert any(
            isinstance(m, AIMessage) and any(c["id"] == message.tool_call_id for c in m.tool_calls)
            for m in preceding
        )
