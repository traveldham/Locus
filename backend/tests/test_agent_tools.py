"""The agent's hands: what each tool returns, and that a write is a real audited write."""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import date
from uuid import UUID, uuid4

import pytest_asyncio
from langchain_core.tools import BaseTool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    ActionStatus,
    AuditJob,
    AuditJobStatus,
    AuditWorker,
    ConnectionStatus,
    GoogleConnection,
    Location,
    OpenStatus,
    Organization,
    ProfileAction,
    RecommendationRun,
    User,
)
from app.services.agent.tools import MAX_AUDIT_CHARS, AgentToolContext, build_tools
from stubs import RIVERSIDE, resource_name

TITLE = "Riverside Studio"
DESCRIPTION = "A dental studio beside the harbour."
WEBSITE = "https://riverside.example.com"
PHONE = "+44 117 555 0101"
NEW_PHONE = "+44 117 555 0199"

REPORT = {
    "as_of": "2026-09-11",
    "engine_version": "4.0.0",
    "location": {
        "name": TITLE,
        "summary": "The profile is solid but the description is missing.",
        "health": {
            "score": 62,
            "grade": "fair",
            "coverage": 0.82,
            "checks_passed": 20,
            "checks_failed": 5,
            "checks_not_evaluated": 3,
            "issues": 7,
            "categories": [
                {"category": "profile", "score": 55, "issues": 3, "worst_severity": "critical"},
                {"category": "reputation", "score": 80, "issues": 1, "worst_severity": "notice"},
            ],
        },
        "priorities": ["profile:description_missing", "reputation:unanswered"],
    },
    "items": [
        {
            "key": "profile:description_missing",
            "rule": "description_missing",
            "category": "profile",
            "category_label": "Profile",
            "title": "Add a business description",
            "severity": "critical",
            "action": "Write a description of at least 250 characters.",
            "why": "A profile with no description gives searchers nothing to read.",
            # The real report carries evidence rows an order of magnitude larger than this.
            "evidence": [{"source": "locations", "row_ids": ["1"], "values": {"chars": 0}}],
        },
        {
            "key": "reputation:unanswered",
            "rule": "unanswered",
            "category": "reputation",
            "category_label": "Reputation",
            "title": "Two reviews are waiting for a reply",
            "severity": "warning",
            "action": "Reply to the two unanswered reviews.",
            "why": "Unanswered reviews read as an inattentive business.",
        },
    ],
}


def tool(tools: list[BaseTool], name: str) -> BaseTool:
    return next(item for item in tools if item.name == name)


async def seed(session_factory) -> tuple[UUID, UUID, UUID]:
    """One organization, one signed-in owner, one connected location."""
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
            primary_category_name="categories/gcid:dentist",
            primary_category_display="Dentist",
            address_lines=["12 Riverside Walk"],
            locality="Bristol",
            phone_primary=PHONE,
            website_uri=WEBSITE,
            description=DESCRIPTION,
            open_status=OpenStatus.open,
        )
        db.add(location)
        await db.commit()
        return organization.id, user.id, location.id


@dataclass(frozen=True, slots=True)
class ToolContext(AgentToolContext):
    """The context the tools get, plus a session of the test's own to assert through.

    Tools open their own session per call now, so `db` here is the *observer's* session:
    it reads what a tool committed, and nothing a tool does depends on it.
    """

    db: AsyncSession | None = None


@pytest_asyncio.fixture
async def ctx(session_factory) -> AsyncIterator[AgentToolContext]:
    organization_id, user_id, location_id = await seed(session_factory)
    async with session_factory() as db:
        yield ToolContext(
            session_factory=session_factory,
            organization_id=organization_id,
            location_id=location_id,
            user_id=user_id,
            db=db,
        )


async def store_run(ctx: AgentToolContext) -> None:
    ctx.db.add(
        RecommendationRun(
            organization_id=ctx.organization_id,
            location_id=ctx.location_id,
            as_of=date(2026, 9, 11),
            engine_version="4.0.0",
            fingerprint="abc123",
            report=REPORT,
            snapshot={},
        )
    )
    await ctx.db.commit()


async def synced_reviews(ctx: AgentToolContext) -> list[dict]:
    tools = build_tools(ctx)
    await tool(tools, "sync_reviews").ainvoke({})
    listed = await tool(tools, "list_reviews").ainvoke({})
    return listed["reviews"]


async def test_get_latest_audit_says_plainly_when_none_has_run(ctx):
    result = await tool(build_tools(ctx), "get_latest_audit").ainvoke({})
    assert result["status"] == "no_audit"
    assert "start_audit" in result["message"]


async def test_get_latest_audit_returns_a_compact_summary(ctx):
    await store_run(ctx)
    result = await tool(build_tools(ctx), "get_latest_audit").ainvoke({})

    assert result["status"] == "ready"
    assert (result["health_score"], result["grade"], result["coverage"]) == (62, "fair", 0.82)
    assert result["issues"] == 7
    assert [row["category"] for row in result["categories"]] == ["profile", "reputation"]
    assert [item["key"] for item in result["top_priorities"]] == [
        "profile:description_missing",
        "reputation:unanswered",
    ]
    first = result["top_priorities"][0]
    assert first["title"] == "Add a business description"
    assert first["severity"] == "critical"
    assert first["action"].startswith("Write a description")
    # The whole report is not dumped: no evidence, and small enough to sit in a prompt.
    assert "evidence" not in first
    assert len(str(result)) < MAX_AUDIT_CHARS


async def test_list_reviews_returns_ids_and_filters_to_unreplied(ctx):
    tools = build_tools(ctx)
    synced = await tool(tools, "sync_reviews").ainvoke({})
    assert synced["created"] == 5

    everything = await tool(tools, "list_reviews").ainvoke({})
    assert everything["total_matching"] == 5
    assert len(everything["reviews"]) == 5
    assert all(UUID(row["id"]) for row in everything["reviews"])
    assert {row["star_rating"] for row in everything["reviews"]} == {1, 3, 4, 5}

    unreplied = await tool(tools, "list_reviews").ainvoke({"unreplied_only": True})
    assert unreplied["total_matching"] == 2
    assert all(row["has_reply"] is False for row in unreplied["reviews"])
    assert all(row["reply_comment"] is None for row in unreplied["reviews"])


async def test_list_reviews_caps_the_limit_it_was_given(ctx):
    tools = build_tools(ctx)
    await tool(tools, "sync_reviews").ainvoke({})
    result = await tool(tools, "list_reviews").ainvoke({"limit": 5000})
    assert result["returned"] == 5


async def test_reply_to_review_publishes_and_leaves_an_audit_row(ctx):
    reviews = await synced_reviews(ctx)
    waiting = next(row for row in reviews if not row["has_reply"])

    result = await tool(build_tools(ctx), "reply_to_review").ainvoke(
        {"review_id": waiting["id"], "comment": "Sorry about the wait - we have added staff."}
    )
    assert result["status"] == "published"
    assert result["reply_comment"] == "Sorry about the wait - we have added staff."

    action = await ctx.db.scalar(
        select(ProfileAction).where(ProfileAction.action_type == "reply_to_review")
    )
    assert action is not None
    assert action.status == ActionStatus.succeeded
    assert action.user_id == ctx.user_id
    assert action.payload["review_id"] == waiting["id"]


async def test_update_location_profile_leaves_every_unsupplied_field_alone(ctx):
    """The regression test for `model_fields_set`: an omitted field is not a clear."""
    result = await tool(build_tools(ctx), "update_location_profile").ainvoke(
        {"phone_primary": NEW_PHONE}
    )
    assert result["status"] == ActionStatus.succeeded.value
    assert result["fields_changed"] == ["phone_primary"]
    assert result["detail"]["update_mask"] == ["phoneNumbers"]

    location = await ctx.db.get(Location, ctx.location_id)
    await ctx.db.refresh(location)
    assert location.phone_primary == NEW_PHONE
    assert location.title == TITLE
    assert location.description == DESCRIPTION
    assert location.website_uri == WEBSITE


async def test_update_location_profile_rejects_an_empty_edit(ctx):
    result = await tool(build_tools(ctx), "update_location_profile").ainvoke({})
    assert "No fields were supplied" in result["error"]
    location = await ctx.db.get(Location, ctx.location_id)
    assert location.title == TITLE


async def test_a_bad_id_comes_back_as_an_error_not_an_exception(ctx):
    reply = tool(build_tools(ctx), "reply_to_review")

    malformed = await reply.ainvoke({"review_id": "the second one", "comment": "Thanks."})
    assert "not a valid id" in malformed["error"]

    missing = await reply.ainvoke({"review_id": str(uuid4()), "comment": "Thanks."})
    assert missing["error"].startswith("HTTP 404")


async def test_a_write_without_a_user_refuses_rather_than_writing_unattributed(
    session_factory, ctx
):
    anonymous = AgentToolContext(
        session_factory=ctx.session_factory,
        organization_id=ctx.organization_id,
        location_id=ctx.location_id,
        user_id=None,
    )
    result = await tool(build_tools(anonymous), "update_location_profile").ainvoke(
        {"phone_primary": NEW_PHONE}
    )
    assert "signed-in user" in result["error"]

    location = await ctx.db.get(Location, ctx.location_id)
    assert location.phone_primary == PHONE
    assert await ctx.db.scalar(select(ProfileAction)) is None


async def test_get_location_profile_returns_the_fields_an_edit_would_touch(ctx):
    result = await tool(build_tools(ctx), "get_location_profile").ainvoke({})
    assert result["title"] == TITLE
    assert result["phone_primary"] == PHONE
    assert result["website_uri"] == WEBSITE
    assert result["description"] == DESCRIPTION
    assert result["open_status"] == "open"
    assert result["primary_category"]["display_name"] == "Dentist"
    assert result["address"] == "12 Riverside Walk, Bristol"


async def test_list_recent_actions_reports_what_the_agent_changed(ctx):
    tools = build_tools(ctx)
    await tool(tools, "update_location_profile").ainvoke({"phone_primary": NEW_PHONE})

    result = await tool(tools, "list_recent_actions").ainvoke({})
    assert result["returned"] == 1
    action = result["actions"][0]
    assert action["action_type"] == "location_update"
    assert action["status"] == "succeeded"
    assert action["by"] == "owner@example.com"


async def test_start_audit_queues_a_job_and_poll_reports_a_finished_one(ctx, stub_queue):
    tools = build_tools(ctx)
    started = await tool(tools, "start_audit").ainvoke({})
    assert started["status"] == AuditJobStatus.pending.value
    assert stub_queue == [started["job_id"]]

    job = await ctx.db.get(AuditJob, UUID(started["job_id"]))
    job.status = AuditJobStatus.succeeded
    for worker in await ctx.db.scalars(select(AuditWorker).where(AuditWorker.job_id == job.id)):
        worker.status = AuditJobStatus.succeeded
        worker.stage = "Done"
    await ctx.db.commit()

    polled = await tool(tools, "poll_audit_job").ainvoke({"job_id": started["job_id"]})
    assert polled["status"] == "succeeded"
    assert len(polled["workers"]) == 6
    assert {row["stage"] for row in polled["workers"]} == {"Done"}


async def test_poll_audit_job_refuses_a_job_from_another_organization(ctx):
    result = await tool(build_tools(ctx), "poll_audit_job").ainvoke({"job_id": str(uuid4())})
    assert "belongs to this organization" in result["error"]
