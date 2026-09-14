"""What `list_audit_suggestions` shows the model, and what it refuses to point it at.

The audit drafts content of its own - a reply for each unanswered low review, a
description for a profile that has none - and the agent used to be unable to see any of
it. This is what it sees now, and the care is all in one place: which id a drafted reply
is applied with.

A finding's `subject` is not that id. `reputation.review_ref` prefers *Google's* review
id, so the subject of an unanswered-review finding is a Google id, and `reply_to_review`
takes our row UUID - the same mismatch that already shipped as a button that did nothing.
The row id lives only in the finding's `evidence` entry for `reviews`, so that is where
this reads it from, and a row id it cannot confirm is answered with `applies_to: null`
rather than a guess. A drafted attribute is the same problem in a different shape: the
draft is keyed by the catalog's bare attribute name, the stored id is that name behind
`attributes/`, and the value type is the catalog's - all resolved here, because the agent
has no tool that reads the catalog and would have to invent one.

The fixture is the real pipeline: the stored reviews go through `read_snapshot`, the six
workers run, and the drafts are attached by the suggestion modules' own `apply`. Nothing
here is a hand-written report - the last one of those hid a production bug in the shape
of the summary, and a shape this file invented would prove nothing about the shape an
audit really stores.
"""

from collections.abc import AsyncIterator
from copy import deepcopy
from datetime import date
from uuid import UUID, uuid4

import pytest_asyncio
from langchain_core.tools import BaseTool
from sqlalchemy import select

from app.models import (
    AttributeCatalogItem,
    ConnectionStatus,
    GoogleConnection,
    Location,
    LocationAttributeValue,
    OpenStatus,
    Organization,
    RecommendationRun,
    Review,
    User,
)
from app.services.agent.tools import (
    ADVISORY_FIELDS,
    ATTRIBUTES_FIELD,
    MAX_AUDIT_CHARS,
    PROFILE_TEXT_FIELDS,
    REVIEW_REPLY_FIELD,
    AgentToolContext,
    _application,
    _Targets,
    build_tools,
)
from app.services.recommendations.categories import WORKERS
from app.services.recommendations.engine import assemble, run_worker
from app.services.recommendations.snapshot import read_snapshot
from app.services.recommendations.suggestions import ENRICHERS
from app.services.recommendations.suggestions.overall import overall_summary
from app.services.recommendations.types import EngineConfig
from stubs import HARBOUR_POINT, RIVERSIDE, resource_name

TITLE = "Riverside Studio"
AS_OF = date(2026, 9, 11)

# The stub dataset's Riverside reviews: two low ones with no reply, at these Google ids.
# They are what the reputation worker puts in `subject`, and they are not row ids.
GOOGLE_ONE_STAR = "RVS-R3"
GOOGLE_THREE_STAR = "RVS-R5"

REPLY_DRAFT = (
    "Thank you for taking the time to tell us about the wait. We are sorry your "
    "appointment did not start on time, and we are looking at how we plan the day so it "
    "does not happen again. Please contact the practice directly and we will put it right."
)
SECOND_REPLY_DRAFT = (
    "Thank you for the feedback. We would like to hear what would have made the visit "
    "better, so please get in touch with the practice directly."
)
DESCRIPTION_DRAFT = (
    "Riverside Studio is a dental practice beside the harbour in Bristol, offering "
    "routine check-ups, hygienist appointments and cosmetic treatments for families and "
    "individuals. The team explains every option before treatment begins."
)
THEMES_DRAFT = ["long waits past the appointment time", "clear explanations from the team"]
POST_DRAFTS = [
    "Appointments are open this month for check-ups and hygienist visits.",
    "Our team is here to answer questions about treatment options before you book.",
]

# Two catalog attributes for this location's category, one of each value type. The
# suggestion layer drafts a yes or no for both; only the BOOL one can hold that answer.
WHEELCHAIR = "wheelchair_accessible_entrance"
SERVICE_KIND = "service_option_kind"

# One scripted model answer per suggestion module, in the shape each module's own schema
# describes. `apply` validates them exactly as it validates a real model's.
DRAFTS: dict[str, dict] = {
    "profile": {
        "summary": "The profile reads well but has no description.",
        "suggestions": [
            {
                "rule": "description_missing",
                "subject": "",
                "field": "description",
                "value_text": DESCRIPTION_DRAFT,
                "reason": "The project description names the services this draft lists.",
                "confidence": "high",
            },
            {
                "rule": "attributes_sparse",
                "subject": "",
                "field": "attributes",
                "value_map": [
                    {"name": WHEELCHAIR, "value": True},
                    {"name": SERVICE_KIND, "value": True},
                ],
                "reason": "The project description says the practice is step-free.",
                "confidence": "medium",
            },
        ],
    },
    "reputation": {
        "summary": "Two low reviews are waiting for an answer.",
        "suggestions": [
            {
                "rule": "critical_review_unanswered",
                "subject": GOOGLE_ONE_STAR,
                "field": REVIEW_REPLY_FIELD,
                "value_text": REPLY_DRAFT,
                "reason": "The reviewer names a forty-minute wait.",
                "confidence": "high",
            },
            {
                "rule": "critical_review_unanswered",
                "subject": GOOGLE_THREE_STAR,
                "field": REVIEW_REPLY_FIELD,
                "value_text": SECOND_REPLY_DRAFT,
                "reason": "The comment gives no specific concern to answer.",
                "confidence": "low",
            },
            {
                "rule": "one_star_share_high",
                "subject": "",
                "field": "themes",
                "value_list": THEMES_DRAFT,
                "reason": "Waiting is mentioned in more than one review.",
                "confidence": "medium",
            },
        ],
    },
    "content": {
        "summary": "Nothing has been posted recently.",
        "suggestions": [
            {
                "rule": "posts_none_recent",
                "subject": "",
                "field": "post_drafts",
                "value_list": POST_DRAFTS,
                "reason": "No post has been published inside the window.",
                "confidence": "medium",
            }
        ],
    },
}


def tool(tools: list[BaseTool], name: str) -> BaseTool:
    return next(item for item in tools if item.name == name)


class Profiles:
    """Two of one organization's locations, and no session held open across them."""

    def __init__(self, ctx: AgentToolContext, other_location_id: UUID, other_review_id: UUID):
        self.ctx = ctx
        self.other_location_id = other_location_id
        self.other_review_id = other_review_id

    @property
    def session_factory(self):
        return self.ctx.session_factory


async def build_report(session_factory, organization_id: UUID, location_id: UUID) -> dict:
    """A report in the shape an audit really stores, drafts included.

    `app.tasks.audit` runs each worker, hands the result to the suggestion layer, and
    assembles the six into a report with the overall summary written on it. This does the
    same, with a scripted model answer standing in for the provider call, so the drafts
    that come out have been through the same validation a real one's would.
    """
    async with session_factory() as db:
        snapshot = await read_snapshot(db, organization_id, location_id)
    config = EngineConfig()
    results = []
    for worker in WORKERS:
        result = run_worker(snapshot, AS_OF, config, worker.KEY)
        module = ENRICHERS.get(worker.KEY)
        response = DRAFTS.get(worker.KEY)
        if module is not None and response is not None:
            module.apply(
                result, response, "fake", "fake-model", module.business_context(snapshot)
            )
        results.append(result)
    report = assemble(snapshot, AS_OF, config, results)
    report["location"]["summary"] = await overall_summary(report)
    return report


async def store(session_factory, organization_id: UUID, location_id: UUID, report: dict) -> None:
    async with session_factory() as db:
        await db.execute(
            RecommendationRun.__table__.delete().where(
                RecommendationRun.location_id == location_id
            )
        )
        db.add(
            RecommendationRun(
                organization_id=organization_id,
                location_id=location_id,
                as_of=AS_OF,
                engine_version=report["engine_version"],
                fingerprint=report["fingerprint"],
                report=report,
                snapshot={},
            )
        )
        await db.commit()


@pytest_asyncio.fixture
async def profiles(session_factory) -> AsyncIterator[Profiles]:
    """Riverside with a stored audit full of drafts, and a sibling location beside it."""
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
            open_status=OpenStatus.open,
        )
        elsewhere = Location(
            organization_id=organization.id,
            connection_id=connection.id,
            google_location_name=HARBOUR_POINT,
            google_resource_name=resource_name(HARBOUR_POINT),
            title="Harbour Point Dental",
            primary_category_name="categories/gcid:dentist",
            primary_category_display="Dentist",
            locality="Bristol",
            open_status=OpenStatus.open,
        )
        db.add_all([here, elsewhere])
        db.add_all(
            AttributeCatalogItem(
                organization_id=organization.id,
                external_attribute_id=external_id,
                attribute_name=name,
                attribute_group="accessibility",
                applies_to_category="Dentist",
                # Stored in the case the import gave it, which is not the case every
                # writer downstream compares in.
                value_type=value_type,
            )
            for external_id, name, value_type in (
                ("attr_01", WHEELCHAIR, "bool"),
                ("attr_02", SERVICE_KIND, "enum"),
            )
        )
        await db.commit()
        organization_id, location_id = organization.id, here.id
        other_location_id, user_id = elsewhere.id, user.id

    ctx = AgentToolContext(
        session_factory=session_factory,
        organization_id=organization_id,
        location_id=location_id,
        user_id=user_id,
    )
    # Both locations' reviews, so the sibling has a real row id of its own to borrow.
    await tool(build_tools(ctx), "sync_reviews").ainvoke({})
    await tool(
        build_tools(
            AgentToolContext(
                session_factory=session_factory,
                organization_id=organization_id,
                location_id=other_location_id,
                user_id=user_id,
            )
        ),
        "sync_reviews",
    ).ainvoke({})

    await store(
        session_factory,
        organization_id,
        location_id,
        await build_report(session_factory, organization_id, location_id),
    )
    async with session_factory() as db:
        other_review_id = await db.scalar(
            select(Review.id).where(Review.location_id == other_location_id)
        )
    yield Profiles(ctx, other_location_id, other_review_id)


async def row_id_of(session_factory, google_review_id: str) -> str:
    async with session_factory() as db:
        return str(
            await db.scalar(
                select(Review.id).where(Review.google_review_id == google_review_id)
            )
        )


async def suggestions(ctx: AgentToolContext) -> dict:
    return await tool(build_tools(ctx), "list_audit_suggestions").ainvoke({})


def by_field(result: dict, field: str) -> list[dict]:
    return [row for row in result["suggestions"] if row["field"] == field]


def one_star_draft(result: dict) -> dict:
    """The drafted reply to the one-star review, found by its text rather than its id."""
    return next(row for row in by_field(result, REVIEW_REPLY_FIELD) if row["value"] == REPLY_DRAFT)


async def edit_stored_report(session_factory, location_id: UUID, change) -> None:
    """Rewrite the stored run's report, the way a differently-shaped audit would have."""
    async with session_factory() as db:
        run = await db.scalar(
            select(RecommendationRun).where(RecommendationRun.location_id == location_id)
        )
        report = deepcopy(run.report)
        change(report)
        run.report = report
        await db.commit()


def unanswered_findings(report: dict) -> list[dict]:
    return [
        item
        for item in report["items"]
        if isinstance(item.get("suggestion"), dict)
        and item["suggestion"]["field"] == REVIEW_REPLY_FIELD
    ]


async def test_a_drafted_reply_carries_our_row_id_and_never_googles(profiles):
    """The defect this tool exists not to repeat: the subject is not the review id."""
    result = await suggestions(profiles.ctx)
    drafted = by_field(result, REVIEW_REPLY_FIELD)
    assert len(drafted) == 2

    one_star = one_star_draft(result)
    row_id = await row_id_of(profiles.session_factory, GOOGLE_ONE_STAR)
    assert one_star["applies_to"] == {"kind": "review", "review_id": row_id}
    assert UUID(one_star["applies_to"]["review_id"])
    assert one_star["rule"] == "critical_review_unanswered"
    assert one_star["category"] == "reputation"
    assert one_star["confidence"] == "high"
    assert "reply_to_review" in one_star["how_to_apply"]
    # Google's id is what the finding's subject holds, and it must not reach the model
    # anywhere an id is asked for.
    assert GOOGLE_ONE_STAR not in str(result)


async def test_the_id_the_tool_hands_over_is_one_reply_to_review_accepts(profiles):
    """Proof the resolution is right, rather than merely well-formed: the write lands."""
    result = await suggestions(profiles.ctx)
    drafted = one_star_draft(result)

    published = await tool(build_tools(profiles.ctx), "reply_to_review").ainvoke(
        {"review_id": drafted["applies_to"]["review_id"], "comment": drafted["value"]}
    )
    assert published["status"] == "published"
    assert published["star_rating"] == 1
    assert published["reply_comment"] == REPLY_DRAFT


async def test_a_draft_whose_evidence_is_gone_says_so_instead_of_guessing(profiles):
    """No evidence row, no target. The neighbouring draft is unaffected."""

    def strip(report: dict) -> None:
        for item in unanswered_findings(report):
            if item["subject"] == GOOGLE_ONE_STAR:
                for entry in item["evidence"]:
                    entry["row_ids"] = []

    await edit_stored_report(profiles.session_factory, profiles.ctx.location_id, strip)

    result = await suggestions(profiles.ctx)
    orphan = one_star_draft(result)
    assert orphan["applies_to"] is None
    assert "cannot be identified" in orphan["how_to_apply"]
    assert "list_reviews" in orphan["how_to_apply"]
    assert orphan["value"] == REPLY_DRAFT, "the draft is still worth showing the user"

    sibling = next(
        row for row in by_field(result, REVIEW_REPLY_FIELD) if row["value"] == SECOND_REPLY_DRAFT
    )
    assert sibling["applies_to"]["kind"] == "review"


async def test_a_row_id_belonging_to_another_location_is_not_a_target(profiles):
    """The scope rule, held in the same shape here as in the write tools.

    A report is not a warrant: the id it names still has to be a review of the location
    this conversation is about, or the reply would land on a profile nobody chose.
    """

    def borrow(report: dict) -> None:
        for item in unanswered_findings(report):
            if item["subject"] == GOOGLE_ONE_STAR:
                for entry in item["evidence"]:
                    entry["row_ids"] = [str(profiles.other_review_id)]

    await edit_stored_report(profiles.session_factory, profiles.ctx.location_id, borrow)

    result = await suggestions(profiles.ctx)
    orphan = one_star_draft(result)
    assert orphan["applies_to"] is None
    assert str(profiles.other_review_id) not in str(result)


async def test_a_draft_built_from_several_reviews_names_none_of_them(profiles):
    """One reply, one review. Several candidates is not a target, it is a coin toss."""

    def widen(report: dict) -> None:
        for item in unanswered_findings(report):
            if item["subject"] == GOOGLE_ONE_STAR:
                for entry in item["evidence"]:
                    entry["row_ids"] = [str(uuid4()), *entry["row_ids"]]

    await edit_stored_report(profiles.session_factory, profiles.ctx.location_id, widen)
    result = await suggestions(profiles.ctx)

    # The invented id is not a review of this location, so one real candidate remains.
    orphan = one_star_draft(result)
    assert orphan["applies_to"]["review_id"] == await row_id_of(
        profiles.session_factory, GOOGLE_ONE_STAR
    )

    def duplicate(report: dict) -> None:
        for item in unanswered_findings(report):
            if item["subject"] == GOOGLE_ONE_STAR:
                other = next(
                    row["evidence"][0]["row_ids"][0]
                    for row in unanswered_findings(report)
                    if row["subject"] == GOOGLE_THREE_STAR
                )
                item["evidence"][0]["row_ids"] = [other, *item["evidence"][0]["row_ids"]]

    await edit_stored_report(profiles.session_factory, profiles.ctx.location_id, duplicate)
    assert one_star_draft(await suggestions(profiles.ctx))["applies_to"] is None


async def test_a_drafted_description_points_at_the_tool_that_writes_it(profiles):
    result = await suggestions(profiles.ctx)
    drafted = by_field(result, "description")
    assert len(drafted) == 1
    assert drafted[0]["applies_to"] == {"kind": "location_field", "field": "description"}
    assert drafted[0]["value"] == DESCRIPTION_DRAFT
    assert "update_location_profile" in drafted[0]["how_to_apply"]
    assert drafted[0]["category"] == "profile"
    assert drafted[0]["title"]
    assert drafted[0]["reason"]


async def test_advice_is_shown_as_advice_and_never_as_something_to_write(profiles):
    """Posts and review themes have no write path. The model must not be led into one."""
    result = await suggestions(profiles.ctx)

    themes = by_field(result, "themes")[0]
    assert themes["applies_to"] is None
    assert "no field to write it to" in themes["how_to_apply"]

    posts = by_field(result, "post_drafts")[0]
    assert posts["applies_to"] is None
    assert "read-only" in posts["how_to_apply"]

    for row in result["suggestions"]:
        if row["applies_to"] is None:
            assert "reply_to_review" not in row["how_to_apply"]
            assert "update_location_profile" not in row["how_to_apply"]


async def test_every_field_the_audit_can_draft_is_classified_deliberately():
    """A new drafted field must be decided on, not fall through to a guess.

    `description`, `title` and `attributes` are the drafted fields
    `update_location_profile` can take; `additional_categories` is not, because secondary
    categories are not in `EDITABLE_FIELDS`. Everything else has no write path at all.
    """
    fields = {
        field
        for module in ENRICHERS.values()
        for field in getattr(module, "SUGGESTS", {}).values()
    }
    assert {"attributes", "additional_categories"} <= fields

    for field in fields:
        applies_to, how_to_apply = _application({}, {"field": field}, _Targets())
        if field in PROFILE_TEXT_FIELDS:
            assert applies_to == {"kind": "location_field", "field": field}
        elif field == REVIEW_REPLY_FIELD:
            assert applies_to is None and "cannot be identified" in how_to_apply
        elif field == ATTRIBUTES_FIELD:
            # Applicable, but only once the catalog has been read: with nothing resolved
            # there is no id to write under, and inventing one is the failure mode.
            assert applies_to is None and "attribute catalog" in how_to_apply
        else:
            assert applies_to is None
            assert field in ADVISORY_FIELDS, f"{field} has no reason written for it"
            assert how_to_apply == ADVISORY_FIELDS[field]


async def test_a_drafted_attribute_is_applied_with_the_id_and_type_the_editor_needs(profiles):
    """`attributes` is writable, and the conversion is a lookup rather than an invention.

    The draft is keyed by the catalog's bare attribute name; the stored id is that name
    behind `attributes/` and the value type is the catalog's own, so the tool resolves
    both and hands over a payload `update_location_profile` takes as it stands. The agent
    has no tool that reads the catalog, so telling it to look the type up itself would be
    telling it to guess.
    """
    result = await suggestions(profiles.ctx)
    drafted = by_field(result, ATTRIBUTES_FIELD)
    assert len(drafted) == 1
    assert drafted[0]["applies_to"]["kind"] == "location_field"
    assert drafted[0]["applies_to"]["field"] == ATTRIBUTES_FIELD
    assert drafted[0]["applies_to"]["attributes"] == [
        {
            "attribute_id": f"attributes/{WHEELCHAIR}",
            "value_type": "BOOL",
            "values": [True],
        }
    ]
    assert "update_location_profile" in drafted[0]["how_to_apply"]
    # The enum attribute was drafted too and is not in the payload: a yes/no answer does
    # not fit an enum container, and the tool says so rather than sending it anyway.
    assert f"attributes/{SERVICE_KIND}" not in str(result)
    assert "1 drafted answer(s) are left out" in drafted[0]["how_to_apply"]


async def test_a_drafted_attribute_is_one_update_location_profile_really_writes(profiles):
    """Proof the shape is right: the payload goes straight through the write path."""
    drafted = by_field(await suggestions(profiles.ctx), ATTRIBUTES_FIELD)[0]

    written = await tool(build_tools(profiles.ctx), "update_location_profile").ainvoke(
        {"attributes": drafted["applies_to"]["attributes"]}
    )
    assert written["fields_changed"] == ["attributes"]
    assert written["detail"]["update_mask"] == ["attributes"]

    async with profiles.session_factory() as db:
        stored = await db.scalar(
            select(LocationAttributeValue).where(
                LocationAttributeValue.location_id == profiles.ctx.location_id
            )
        )
    assert stored.attribute_id == f"attributes/{WHEELCHAIR}"
    assert stored.value_type == "BOOL"
    assert stored.values == [True]


async def test_an_attribute_the_catalog_does_not_know_is_not_written_under_a_guessed_id(
    profiles,
):
    """Nothing resolvable means nothing to apply - not a plausible id and a BOOL."""

    def rename(report: dict) -> None:
        for item in report["items"]:
            suggestion = item.get("suggestion")
            if isinstance(suggestion, dict) and suggestion["field"] == ATTRIBUTES_FIELD:
                suggestion["value"] = {"a_thing_no_catalog_lists": True}

    await edit_stored_report(profiles.session_factory, profiles.ctx.location_id, rename)

    drafted = by_field(await suggestions(profiles.ctx), ATTRIBUTES_FIELD)[0]
    assert drafted["applies_to"] is None
    assert "attribute catalog" in drafted["how_to_apply"]
    assert "a_thing_no_catalog_lists" not in drafted["how_to_apply"]


async def test_no_audit_at_all_is_said_plainly(session_factory, profiles):
    """A location whose audit has never run, answered without an error."""
    empty = AgentToolContext(
        session_factory=session_factory,
        organization_id=profiles.ctx.organization_id,
        location_id=profiles.other_location_id,
        user_id=profiles.ctx.user_id,
    )
    result = await suggestions(empty)
    assert result["status"] == "no_audit"
    assert "start_audit" in result["message"]
    assert "suggestions" not in result


async def test_an_audit_that_drafted_nothing_is_not_an_error(profiles):
    def undraft(report: dict) -> None:
        for item in report["items"]:
            item.pop("suggestion", None)

    await edit_stored_report(profiles.session_factory, profiles.ctx.location_id, undraft)
    result = await suggestions(profiles.ctx)
    assert result["status"] == "ready"
    assert result["suggestions"] == []
    assert "drafted nothing" in result["note"]


async def test_a_long_list_of_drafts_still_fits_the_prompt(profiles):
    """An audit can draft a reply for every unanswered low review; the budget holds.

    The applicable drafts are the ones worth the space, so they are what survives: an
    agent that cannot act on anything because a page of advice crowded it out has lost
    the only thing this tool is for.
    """

    def many(report: dict) -> None:
        template = unanswered_findings(report)[0]
        extra = []
        for index in range(12):
            copy = deepcopy(template)
            copy["key"] = f"{template['key']}-copy-{index}"
            copy["subject"] = f"{template['subject']}-copy-{index}"
            copy["suggestion"]["value"] = f"{REPLY_DRAFT} Reference {index}."
            extra.append(copy)
        for item in report["items"]:
            if isinstance(item.get("suggestion"), dict) and item["suggestion"]["field"] == "themes":
                item["suggestion"]["value"] = ["a recurring theme spelled out at length"] * 200
        report["items"].extend(extra)

    await edit_stored_report(profiles.session_factory, profiles.ctx.location_id, many)
    result = await suggestions(profiles.ctx)

    assert len(str(result)) < MAX_AUDIT_CHARS
    assert result["suggestions"], "trimming must not empty the list"
    assert by_field(result, "description"), "the applicable drafts are what earn the space"
    applicable = [row for row in result["suggestions"] if row["applies_to"] is not None]
    assert applicable == result["suggestions"][: len(applicable)]
    assert "left out" in result["note"]


async def test_another_locations_audit_is_not_readable_from_this_chat(profiles):
    """The conversation's location bounds what the tool can see, drafts included."""
    await store(
        profiles.session_factory,
        profiles.ctx.organization_id,
        profiles.other_location_id,
        await build_report(
            profiles.session_factory, profiles.ctx.organization_id, profiles.other_location_id
        ),
    )
    async with profiles.session_factory() as db:
        stored = await db.scalar(
            select(RecommendationRun).where(
                RecommendationRun.location_id == profiles.other_location_id
            )
        )
    assert stored is not None

    result = await suggestions(profiles.ctx)
    assert result["audit_id"] != str(stored.id)
    review_ids = {
        row["applies_to"]["review_id"]
        for row in result["suggestions"]
        if row["applies_to"] and row["applies_to"]["kind"] == "review"
    }
    async with profiles.session_factory() as db:
        theirs = {
            str(row)
            for row in await db.scalars(
                select(Review.id).where(Review.location_id == profiles.other_location_id)
            )
        }
    assert not (review_ids & theirs)


async def test_another_tenant_sees_no_audit_rather_than_this_one(session_factory, profiles):
    stranger = AgentToolContext(
        session_factory=session_factory,
        organization_id=uuid4(),
        location_id=profiles.ctx.location_id,
        user_id=profiles.ctx.user_id,
    )
    assert (await suggestions(stranger))["status"] == "no_audit"
