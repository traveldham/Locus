"""What `get_latest_audit` does with a report the engine actually wrote.

This is the regression test for a defect a fixture hid. `_audit_summary` read
`location.summary` as a paragraph of text, and `suggestions.overall.overall_summary` has
never returned one: it returns a payload - `text` plus `strengths` and `attention` - on
both the model path and the deterministic fallback. `_truncate` then called `.strip()` on
a dict, the tool came back as `{"error": "AttributeError: ..."}`, and the user was told
"the audit completed, but the result data format returned an error when accessed".

The old tests passed because their report was written by hand with `summary` as a string.
So the fixture here is not written by hand at all: it is `engine.analyze` plus the real
`overall_summary`, which is exactly what an audit stores, and a change to either shape
lands on this test rather than on a user.
"""

from collections.abc import AsyncIterator
from datetime import date
from uuid import UUID

import pytest_asyncio
from langchain_core.tools import BaseTool
from sqlalchemy import select
from test_profile_worker import AS_OF, complete

from app.models import (
    ConnectionStatus,
    GoogleConnection,
    Location,
    OpenStatus,
    Organization,
    RecommendationRun,
    User,
)
from app.services.agent.tools import MAX_AUDIT_CHARS, AgentToolContext, build_tools
from app.services.recommendations.engine import analyze
from app.services.recommendations.suggestions.overall import overall_summary
from stubs import RIVERSIDE, resource_name

TITLE = "Riverside Studio"


def tool(tools: list[BaseTool], name: str) -> BaseTool:
    return next(item for item in tools if item.name == name)


async def stored_report() -> dict:
    """A report in the shape an audit really stores it, engine and summary included.

    `app.tasks.audit` assembles the six workers with `analyze` and then writes
    `report["location"]["summary"] = await overall_summary(report)`, so that is what this
    does. The autouse `no_llm` fixture keeps the summary on its deterministic path, which
    returns the same payload shape a model answer does.
    """
    snapshot = complete()
    # One thing missing, so the summary has a priority to name and a point to make.
    snapshot["locations"][0]["phone_primary"] = None
    report = analyze(snapshot, AS_OF)
    report["location"]["summary"] = await overall_summary(report)
    return report


@pytest_asyncio.fixture
async def ctx(session_factory) -> AsyncIterator[AgentToolContext]:
    """One location whose current audit is a real engine report."""
    async with session_factory() as db:
        organization = Organization(name="Northstar Dental", slug="northstar-dental")
        user = User(email="owner@example.com", full_name="Locus Owner")
        db.add_all([organization, user])
        await db.flush()
        connection = GoogleConnection(
            organization_id=organization.id,
            google_account_email="owner@example.com",
            google_subject=f"demo-connection:{organization.id}",
            refresh_token_encrypted="demo-connection",
            scopes="https://www.googleapis.com/auth/business.manage",
            status=ConnectionStatus.active,
        )
        db.add(connection)
        await db.flush()
        location = Location(
            organization_id=organization.id,
            connection_id=connection.id,
            google_location_name=RIVERSIDE,
            google_resource_name=resource_name(RIVERSIDE),
            title=TITLE,
            open_status=OpenStatus.open,
        )
        db.add(location)
        await db.flush()
        report = await stored_report()
        db.add(
            RecommendationRun(
                organization_id=organization.id,
                location_id=location.id,
                as_of=date(2026, 9, 11),
                engine_version=report["engine_version"],
                fingerprint=report["fingerprint"],
                report=report,
                snapshot={},
            )
        )
        await db.commit()
        yield AgentToolContext(
            session_factory=session_factory,
            organization_id=organization.id,
            location_id=location.id,
            user_id=user.id,
        )


async def test_the_summary_the_engine_writes_is_a_payload_not_a_paragraph():
    """The premise of the defect, asserted directly so it cannot drift back."""
    summary = (await stored_report())["location"]["summary"]
    assert isinstance(summary, dict)
    assert set(summary) >= {"text", "strengths", "attention"}
    assert isinstance(summary["text"], str)


async def test_get_latest_audit_reads_a_real_report_without_failing(ctx):
    """The exact call that failed in production: a real report, read end to end."""
    result = await tool(build_tools(ctx), "get_latest_audit").ainvoke({})

    assert "error" not in result
    assert result["status"] == "ready"
    assert isinstance(result["health_score"], int)
    assert result["grade"]


async def test_the_summarys_text_and_its_points_all_reach_the_model(ctx):
    """`strengths` and `attention` are the half of the payload worth reading out."""
    result = await tool(build_tools(ctx), "get_latest_audit").ainvoke({})

    assert isinstance(result["overall_summary"], str)
    assert "Start with: Add a phone number" in result["overall_summary"]
    assert result["needs_attention"], "the audit found something; the model should see it"
    assert all(point["text"] for point in result["needs_attention"])
    assert all(point["category"] for point in result["needs_attention"])
    assert "phone" in result["needs_attention"][0]["text"].lower()
    assert all(point["text"] for point in result["strengths"])
    # Still a summary, not the report: an engine report runs to tens of thousands of
    # characters and none of the evidence rows belong in a prompt.
    assert len(str(result)) < MAX_AUDIT_CHARS
    assert "evidence" not in str(result)


async def test_a_summary_shape_nobody_expected_degrades_instead_of_killing_the_tool(
    ctx, session_factory
):
    """The class of failure, not just the one instance of it.

    A field whose shape changed under this code must cost the answer some detail, never
    the whole tool: `{"error": "AttributeError: 'dict' object has no attribute 'strip'"}`
    is what the user was shown last time, and nothing about the audit reached them.
    """
    async with session_factory() as db:
        run = await db.scalar(select(RecommendationRun))
        report = dict(run.report)
        report["location"] = {**report["location"], "summary": ["not", "a", "dict"]}
        run.report = report
        await db.commit()

    result = await tool(build_tools(ctx), "get_latest_audit").ainvoke({})
    assert "error" not in result
    assert result["status"] == "ready"
    assert result["overall_summary"] is None
    assert result["health_score"] is not None
    assert UUID(result["audit_id"])
