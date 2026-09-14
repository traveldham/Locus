"""Gemini's thought signatures have to survive a round trip through the transcript.

A thinking model issues a signature with every function call it asks for, and refuses to
accept that call back on a later turn without it: the request fails outright with
"Function call is missing a thought_signature in functionCall parts". Because a turn only
ever replays what was stored, dropping the signature does not degrade an answer - it means
every conversation that has ever used a tool is dead from its second turn onwards.

No stub model reproduces this; it was found by a live conversation failing on its second
turn, which is why these tests pin the exact `additional_kwargs` key the provider uses.
"""

from langchain_core.messages import AIMessage

from app.models import AgentMessage, AgentMessageRole
from app.services.agent.graph import (
    THOUGHT_SIGNATURES,
    from_langchain_message,
    to_langchain_messages,
)

SIGNATURE = "AY89a19YOFsF7XP0HWi41p1M7146VAX/l1JW5Fh6hbHDjDR2wCn6KfmzfqPNs4Ssn4rVfthy"
OTHER = "Bz90b2aZPGtG8YQ1IXj52q2N8257WBY0m2KX6Gi7icEEkES3xDo7LgnaguQOt5Tto5sWguiz"


def answered(call_id: str, name: str = "get_latest_audit") -> AgentMessage:
    return AgentMessage(
        role=AgentMessageRole.tool, content="{}", tool_call_id=call_id, tool_name=name
    )


def test_a_signature_is_stored_with_the_call_it_belongs_to() -> None:
    message = AIMessage(
        content="",
        tool_calls=[{"id": "c1", "name": "get_latest_audit", "args": {}, "type": "tool_call"}],
        additional_kwargs={THOUGHT_SIGNATURES: {"c1": SIGNATURE}},
    )

    row = from_langchain_message(message)

    assert row["tool_calls"] == [
        {
            "id": "c1",
            "name": "get_latest_audit",
            "args": {},
            "thought_signature": SIGNATURE,
        }
    ]


def test_a_stored_signature_is_replayed_where_the_provider_expects_it() -> None:
    rows = [
        AgentMessage(role=AgentMessageRole.user, content="how is it scoring?"),
        AgentMessage(
            role=AgentMessageRole.assistant,
            content="",
            tool_calls=[
                {
                    "id": "c1",
                    "name": "get_latest_audit",
                    "args": {},
                    "thought_signature": SIGNATURE,
                }
            ],
        ),
        answered("c1"),
    ]

    replayed = to_langchain_messages(rows)

    call = replayed[1]
    assert call.tool_calls[0]["id"] == "c1"
    assert call.additional_kwargs[THOUGHT_SIGNATURES] == {"c1": SIGNATURE}


def test_every_call_of_a_parallel_request_keeps_its_own_signature() -> None:
    message = AIMessage(
        content="",
        tool_calls=[
            {"id": "c1", "name": "list_reviews", "args": {}, "type": "tool_call"},
            {"id": "c2", "name": "get_latest_audit", "args": {}, "type": "tool_call"},
        ],
        additional_kwargs={THOUGHT_SIGNATURES: {"c1": SIGNATURE, "c2": OTHER}},
    )

    row = from_langchain_message(message)
    replayed = to_langchain_messages(
        [
            AgentMessage(
                role=AgentMessageRole.assistant, content="", tool_calls=row["tool_calls"]
            ),
            answered("c1", "list_reviews"),
            answered("c2"),
        ]
    )

    assert replayed[0].additional_kwargs[THOUGHT_SIGNATURES] == {"c1": SIGNATURE, "c2": OTHER}


def test_a_call_stored_before_signatures_were_kept_still_replays() -> None:
    """Rows written by the version that dropped them must not start failing."""
    rows = [
        AgentMessage(
            role=AgentMessageRole.assistant,
            content="",
            tool_calls=[{"id": "c1", "name": "list_reviews", "args": {}}],
        ),
        answered("c1", "list_reviews"),
    ]

    replayed = to_langchain_messages(rows)

    assert replayed[0].tool_calls[0]["id"] == "c1"
    # No signature to replay, so the key is absent rather than present and empty.
    assert THOUGHT_SIGNATURES not in replayed[0].additional_kwargs


def test_an_assistant_message_with_no_tool_calls_carries_no_signatures() -> None:
    row = from_langchain_message(AIMessage(content="Nothing needs attention."))

    assert row["tool_calls"] is None
