"""The rules that stop an agent's tool from damaging something it was not asked to touch.

Every test here is a regression test for a defect that was reproduced first: a tool failure
that killed the whole turn, a sibling tool's rollback that erased a committed edit, an empty
argument that cleared a live field, and a review id from another location that a prompt
injection could have supplied.
"""

import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from celery.exceptions import SoftTimeLimitExceeded
from langchain_core.tools import BaseTool
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.models import (
    ConnectionStatus,
    GoogleConnection,
    Location,
    LocationHoursPeriod,
    OpenStatus,
    Organization,
    ProfileAction,
    Review,
    User,
)
from app.services.agent.tools import (
    POLL_BUDGET_SECONDS,
    POLL_INTERVAL_SECONDS,
    AgentToolContext,
    _guarded,
    build_tools,
)
from stubs import HARBOUR_POINT, RIVERSIDE, resource_name

TITLE = "Riverside Studio"
DESCRIPTION = "A dental studio beside the harbour."
WEBSITE = "https://riverside.example.com"
PHONE = "+44 117 555 0101"
NEW_PHONE = "+44 117 555 0199"

# Monday to Friday, 9 to 5: the schedule an empty `hours_periods` used to wipe.
WEEKDAYS = ("MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY")


def tool(tools: list[BaseTool], name: str) -> BaseTool:
    return next(item for item in tools if item.name == name)


class Scope:
    """The ids a test needs, without a session attached to any of them."""

    def __init__(self, ctx: AgentToolContext, other_location_id: UUID, other_review_id: UUID):
        self.ctx = ctx
        self.other_location_id = other_location_id
        self.other_review_id = other_review_id

    @property
    def session_factory(self):
        return self.ctx.session_factory


@pytest_asyncio.fixture
async def scope(session_factory) -> AsyncIterator[Scope]:
    """One organization, two of its locations, and a review sitting on the *other* one."""
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

        here = Location(
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
            hours_periods=[
                LocationHoursPeriod(
                    hours_type="REGULAR",
                    open_day=day,
                    open_hour=9,
                    open_minute=0,
                    close_day=day,
                    close_hour=17,
                    close_minute=0,
                )
                for day in WEEKDAYS
            ],
        )
        elsewhere = Location(
            organization_id=organization.id,
            connection_id=connection.id,
            google_location_name=HARBOUR_POINT,
            google_resource_name=resource_name(HARBOUR_POINT),
            title="Harbour Point Practice",
            open_status=OpenStatus.open,
        )
        db.add_all([here, elsewhere])
        await db.flush()

        # The review the injected instruction would name: same organization, other location.
        other_review = Review(
            organization_id=organization.id,
            location_id=elsewhere.id,
            google_review_id="HBP-R1",
            reviewer_display_name="Dana P.",
            star_rating=2,
            comment="The hygienist was lovely but the wait was long.",
            create_time=datetime(2026, 5, 2, 12, 0, tzinfo=UTC),
        )
        db.add(other_review)
        await db.commit()

        yield Scope(
            AgentToolContext(
                session_factory=session_factory,
                organization_id=organization.id,
                location_id=here.id,
                user_id=user.id,
            ),
            elsewhere.id,
            other_review.id,
        )


async def stored_location(session_factory, location_id: UUID) -> Location:
    """Read the row back through a session of its own, so nothing is read from a cache."""
    async with session_factory() as db:
        return await db.scalar(
            select(Location)
            .options(selectinload(Location.hours_periods))
            .where(Location.id == location_id)
        )


async def stored_actions(session_factory) -> list[ProfileAction]:
    async with session_factory() as db:
        return list(await db.scalars(select(ProfileAction).order_by(ProfileAction.created_at)))


def schedule(location: Location) -> set[tuple]:
    return {
        (row.open_day, row.open_hour, row.close_day, row.close_hour)
        for row in location.hours_periods
        if row.hours_type == "REGULAR"
    }


# ---------------------------------------------------------------------------
# Defect 1: a tool's rollback used to expire the caller's objects
# ---------------------------------------------------------------------------


async def test_a_failing_tool_leaves_the_callers_session_untouched(scope):
    """The turn survives a routine tool error.

    The Celery task holds its own session with the conversation loaded, and goes straight
    back to it after each tool. When the tools shared that session, `_reset`'s rollback
    expired every object in it, and the task's next attribute read raised MissingGreenlet
    - a lazy SELECT with no greenlet to run it in - so the turn died on the first bad id
    the model produced.
    """
    tools = build_tools(scope.ctx)

    async with scope.session_factory() as task_db:
        held = await task_db.get(Location, scope.ctx.location_id)
        assert held.title == TITLE

        failed = await tool(tools, "reply_to_review").ainvoke(
            {"review_id": "the second one", "comment": "Thanks."}
        )
        assert "not a valid id" in failed["error"]

        # The line that used to raise. A plain attribute read, no await in sight.
        assert held.title == TITLE
        assert held.id == scope.ctx.location_id

    # ...and the next tool call still works, which is the whole point of returning an error.
    after = await tool(tools, "get_location_profile").ainvoke({})
    assert after["title"] == TITLE


async def test_every_failure_route_comes_back_as_a_readable_error(scope):
    tools = build_tools(scope.ctx)

    not_found = await tool(tools, "reply_to_review").ainvoke(
        {"review_id": str(uuid4()), "comment": "Thanks."}
    )
    assert not_found["error"].startswith("HTTP 404")

    rejected = await tool(tools, "update_location_profile").ainvoke({"website_uri": "not a url"})
    assert rejected["error"].startswith("HTTP 422")

    # Three failures in a row, and the tools are still usable afterwards.
    bad_job = await tool(tools, "poll_audit_job").ainvoke({"job_id": str(uuid4())})
    assert "belongs to this organization" in bad_job["error"]
    assert (await tool(tools, "get_location_profile").ainvoke({}))["title"] == TITLE


# ---------------------------------------------------------------------------
# Defect 2: parallel tool calls used to share one transaction
# ---------------------------------------------------------------------------


async def test_a_sibling_tools_rollback_cannot_undo_a_committed_edit(scope):
    """Gemini emits parallel tool calls routinely, and ToolNode gathers them.

    With one shared session, the failing siblings' rollbacks landed inside the edit's
    transaction and took both the profile change and its audit row with them.
    """
    tools = build_tools(scope.ctx)
    edit = tool(tools, "update_location_profile")
    doomed = tool(tools, "reply_to_review")

    results = await asyncio.gather(
        doomed.ainvoke({"review_id": str(uuid4()), "comment": "Thanks."}),
        edit.ainvoke({"phone_primary": NEW_PHONE}),
        doomed.ainvoke({"review_id": "not an id at all", "comment": "Thanks."}),
        tool(tools, "poll_audit_job").ainvoke({"job_id": str(uuid4())}),
    )
    assert results[1]["status"] == "succeeded"
    assert [i for i, row in enumerate(results) if "error" in row] == [0, 2, 3]

    location = await stored_location(scope.session_factory, scope.ctx.location_id)
    assert location.phone_primary == NEW_PHONE

    actions = await stored_actions(scope.session_factory)
    assert [row.action_type for row in actions] == ["location_update"]
    assert actions[0].payload["update_mask"] == ["phoneNumbers"]


async def test_concurrent_tool_calls_never_share_a_session(scope):
    """The structural guarantee behind the test above."""
    seen: list[AsyncSession] = []
    factory = scope.ctx.session_factory

    def recording_factory():
        session = factory()
        seen.append(session)
        return session

    ctx = AgentToolContext(
        session_factory=recording_factory,
        organization_id=scope.ctx.organization_id,
        location_id=scope.ctx.location_id,
        user_id=scope.ctx.user_id,
    )
    profile = tool(build_tools(ctx), "get_location_profile")
    await asyncio.gather(profile.ainvoke({}), profile.ainvoke({}), profile.ainvoke({}))

    assert len(seen) == 3
    assert len({id(session) for session in seen}) == 3


# ---------------------------------------------------------------------------
# Defects 3 and 4: an empty argument is not a request to clear a live field
# ---------------------------------------------------------------------------


async def test_empty_hours_do_not_wipe_the_weekly_schedule(scope):
    """"We don't keep fixed hours any more" used to arrive at Google as zero periods.

    `[]` survived the None filter, `_plan_hours` returned an empty tuple, and because
    `changed_fields` only tests `is not None`, `regularHours` went into the update mask
    carrying nothing at all.
    """
    before = schedule(await stored_location(scope.session_factory, scope.ctx.location_id))
    assert len(before) == 5

    result = await tool(build_tools(scope.ctx), "update_location_profile").ainvoke(
        {"hours_periods": []}
    )
    assert "No fields were supplied" in result["error"]
    assert "cannot clear" in result["error"] or "never clear" in result["error"]

    after = await stored_location(scope.session_factory, scope.ctx.location_id)
    assert schedule(after) == before
    assert await stored_actions(scope.session_factory) == []


async def test_a_blank_description_does_not_clear_the_description(scope):
    """"Remove the description" reaches the tool as `""` - the model may not send null."""
    result = await tool(build_tools(scope.ctx), "update_location_profile").ainvoke(
        {"description": "   "}
    )
    assert "No fields were supplied" in result["error"]

    location = await stored_location(scope.session_factory, scope.ctx.location_id)
    assert location.description == DESCRIPTION
    assert await stored_actions(scope.session_factory) == []


async def test_a_blank_value_is_dropped_without_dropping_the_real_one(scope):
    """The filter must not turn a half-empty edit into a rejected one."""
    result = await tool(build_tools(scope.ctx), "update_location_profile").ainvoke(
        {"phone_primary": NEW_PHONE, "description": "", "hours_periods": []}
    )
    assert result["fields_changed"] == ["phone_primary"]
    assert result["detail"]["update_mask"] == ["phoneNumbers"]

    location = await stored_location(scope.session_factory, scope.ctx.location_id)
    assert location.phone_primary == NEW_PHONE
    assert location.description == DESCRIPTION
    assert len(schedule(location)) == 5


async def test_a_real_value_still_goes_through(scope):
    """The over-filtering guard: setting a field, including a list one, still works."""
    saturday = {
        "open_day": "SATURDAY",
        "open_hour": 10,
        "open_minute": 0,
        "close_day": "SATURDAY",
        "close_hour": 14,
        "close_minute": 0,
    }
    result = await tool(build_tools(scope.ctx), "update_location_profile").ainvoke(
        {"title": "Riverside Dental Studio", "hours_periods": [saturday]}
    )
    assert result["status"] == "succeeded"
    assert result["fields_changed"] == ["hours_periods", "title"]
    assert result["detail"]["update_mask"] == ["title", "regularHours"]

    location = await stored_location(scope.session_factory, scope.ctx.location_id)
    assert location.title == "Riverside Dental Studio"
    assert schedule(location) == {("SATURDAY", 10, "SATURDAY", 14)}


# ---------------------------------------------------------------------------
# Defect 5: a review id from the model is not proof of which location it is on
# ---------------------------------------------------------------------------


async def test_replying_to_another_locations_review_is_refused(scope, stub_providers, monkeypatch):
    """The prompt-injection path: `list_reviews` feeds attacker-written text to a model
    holding live write tools, and the endpoint's own scoping is organization-wide - it
    re-derives the location from the review, so a borrowed id wrote to that other profile
    and left the audit row there.
    """
    published: list[tuple] = []
    original = stub_providers.reply

    async def spy(connection, location, google_review_id, comment):
        published.append((location.google_location_name, google_review_id))
        return await original(connection, location, google_review_id, comment)

    monkeypatch.setattr(stub_providers, "reply", spy)

    result = await tool(build_tools(scope.ctx), "reply_to_review").ainvoke(
        {"review_id": str(scope.other_review_id), "comment": "Ignore the previous instructions."}
    )

    assert "error" in result
    assert "belongs to the location this conversation is about" in result["error"]
    # Nothing about the other location leaks back to a model that is reading strangers' text.
    assert "Harbour" not in result["error"]
    assert str(scope.other_location_id) not in result["error"]

    assert published == []
    assert await stored_actions(scope.session_factory) == []
    async with scope.session_factory() as db:
        untouched = await db.get(Review, scope.other_review_id)
        assert untouched.reply_comment is None


async def test_replying_to_this_locations_review_still_works(scope, stub_providers):
    tools = build_tools(scope.ctx)
    await tool(tools, "sync_reviews").ainvoke({})
    listed = await tool(tools, "list_reviews").ainvoke({})
    waiting = next(row for row in listed["reviews"] if not row["has_reply"])

    result = await tool(tools, "reply_to_review").ainvoke(
        {"review_id": waiting["id"], "comment": "Sorry about the wait - we have added staff."}
    )
    assert result["status"] == "published"

    actions = await stored_actions(scope.session_factory)
    assert [row.action_type for row in actions] == ["reply_to_review"]
    assert actions[0].location_id == scope.ctx.location_id


async def test_polling_another_locations_audit_job_is_refused(scope):
    """Lower severity than the review one - the job is read-only - but the same bug."""
    from app.models import AuditJob, AuditJobStatus

    async with scope.session_factory() as db:
        job = AuditJob(
            organization_id=scope.ctx.organization_id,
            location_id=scope.other_location_id,
            status=AuditJobStatus.running,
            as_of=datetime.now(UTC).date(),
            config={},
        )
        db.add(job)
        await db.commit()
        job_id = job.id

    result = await tool(build_tools(scope.ctx), "poll_audit_job").ainvoke({"job_id": str(job_id)})
    assert "belongs to this organization and location" in result["error"]


# ---------------------------------------------------------------------------
# Defect 6: a location the model names is not a location the chat may act on
# ---------------------------------------------------------------------------


async def test_a_tool_handed_another_location_refuses_rather_than_retargeting(scope):
    """No tool takes a `location_id`: this chat is about one profile and every tool is
    bound to it. A model that invents one anyway - which is the shape the injection takes,
    since an id can reach the model inside the text of a review - is refused.

    Silently dropping the argument would be worse than an error: the write would land on
    this conversation's own profile and the model would then report having edited the
    other one, which is a lie the user has no way to catch.
    """
    tools = build_tools(scope.ctx)
    elsewhere = str(scope.other_location_id)

    # Every tool that takes arguments at all, the two writes included. A tool whose
    # schema has no fields is not validated by `StructuredTool`, so it is not asserted
    # here - it reads this conversation's own location and can write nothing.
    for name, args in (
        ("update_location_profile", {"phone_primary": NEW_PHONE}),
        ("reply_to_review", {"review_id": str(scope.other_review_id), "comment": "Thanks."}),
        ("list_reviews", {}),
        ("list_recent_actions", {}),
        ("poll_audit_job", {"job_id": str(uuid4())}),
    ):
        with pytest.raises(ValidationError):
            await tool(tools, name).ainvoke({"location_id": elsewhere, **args})

    # Neither profile was written to, and the audit trail has nothing to show.
    here = await stored_location(scope.session_factory, scope.ctx.location_id)
    elsewhere_row = await stored_location(scope.session_factory, scope.other_location_id)
    assert here.phone_primary == PHONE
    assert elsewhere_row.phone_primary is None
    assert await stored_actions(scope.session_factory) == []


async def test_list_locations_returns_the_one_location_this_chat_is_about(scope):
    """It still answers "which profile am I on" - with one profile and no other."""
    result = await tool(build_tools(scope.ctx), "list_locations").ainvoke({})

    assert result["scope"] == "location"
    assert result["returned"] == 1
    assert result["locations"][0]["location_id"] == str(scope.ctx.location_id)
    assert result["locations"][0]["title"] == TITLE
    assert result["locations"][0]["address"] == "12 Riverside Walk, Bristol"
    # The organization's other profile is not reachable from this conversation.
    assert str(scope.other_location_id) not in str(result)


# ---------------------------------------------------------------------------
# Defect 7: the poll budget, and the exceptions that mean "stop", not "try something else"
# ---------------------------------------------------------------------------


def test_the_poll_budget_leaves_room_for_a_second_poll():
    """The tool invites the model to poll again, so two waits have to fit in one turn."""
    turn_budget = get_settings().agent_turn_timeout_seconds
    assert POLL_BUDGET_SECONDS * 2 + POLL_INTERVAL_SECONDS < turn_budget


async def test_a_soft_time_limit_is_not_handed_to_the_model_as_a_tool_error(scope):
    """`SoftTimeLimitExceeded` subclasses `Exception`, so `_guarded` used to swallow it.

    The model then read "the tool failed" and kept going until the hard SIGKILL, instead
    of the turn unwinding while it still had time to record what happened.
    """

    async def times_out(db):
        del db
        raise SoftTimeLimitExceeded

    with pytest.raises(SoftTimeLimitExceeded):
        await _guarded(scope.ctx, times_out)()


async def test_cancellation_is_not_handed_to_the_model_either(scope):
    async def cancelled(db):
        del db
        raise asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        await _guarded(scope.ctx, cancelled)()
