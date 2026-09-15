"""The demo-profile generator: catalogue, import, idempotence, scoping, and the audit.

The last test is the one that matters. Missing data does not produce a low score — the
scorer drops unevaluated checks from the denominator — so the only proof that the
generated profiles are bad in the way the engine measures is to run the six real workers
over them and assert the intended rules came back `triggered`, not `insufficient_data`.
"""

from datetime import date
from uuid import UUID, uuid4

import pytest
from conftest import sign_in
from sqlalchemy import func, select

from app.models import (
    Booking,
    CompetitorObservation,
    KeywordRank,
    Location,
    LocationCategory,
    LocationSource,
    MediaSummary,
    Organization,
    PerformanceDaily,
    Project,
    ProjectLocation,
    RecommendationRun,
    Review,
    SearchTermMonthly,
    TrackedKeyword,
)
from app.services.recommendations.queue import new_job
from app.services.recommendations.types import EngineConfig
from app.tasks.audit import run_job
from generator_data import ARCHETYPES, catalogue, generate, import_archetypes, snapshot_of
from generator_data.importer import NAME_PREFIX

# Fixed so the generated series — and therefore every score below — are reproducible.
REFERENCE = date(2026, 9, 14)
KEYS = [a.key for a in ARCHETYPES]


async def make_organization(session_factory, name="Demo Co", slug="demo-co") -> UUID:
    async with session_factory() as db:
        organization = Organization(name=name, slug=slug)
        db.add(organization)
        await db.commit()
        return organization.id


async def import_keys(session_factory, organization_id: UUID, keys: list[str], **kwargs):
    async with session_factory() as db:
        result = await import_archetypes(
            db, organization_id, keys, reference=REFERENCE, **kwargs
        )
        await db.commit()
        return result


def test_catalogue_declares_ten_distinct_businesses():
    assert len(ARCHETYPES) == 10
    assert len({a.key for a in ARCHETYPES}) == 10
    assert len({a.industry for a in ARCHETYPES}) == 10
    assert len({a.primary_category for a in ARCHETYPES}) == 10
    # None of them claims the sample dataset's category, so the twelve seeded clinics'
    # attribute catalog — and their coverage scores — are left untouched.
    assert "Dentist" not in {a.primary_category for a in ARCHETYPES}
    for a in ARCHETYPES:
        assert a.expected_grade in ("poor", "fair")
        assert a.failing and set(a.failing) <= {
            "profile",
            "reputation",
            "visibility",
            "operations",
            "performance",
            "content",
        }


def test_generation_is_deterministic():
    first, second = (generate(ARCHETYPES[0], REFERENCE) for _ in range(2))
    assert snapshot_of(first) == snapshot_of(second)
    assert first.total_rows > 400


async def test_catalogue_reports_what_this_organization_already_has(session_factory):
    organization_id = await make_organization(session_factory)
    async with session_factory() as db:
        rows = await catalogue(db, organization_id)
    assert [row["key"] for row in rows] == KEYS
    assert all(row["imported"] is False and row["location_id"] is None for row in rows)
    assert all(row["industry"] and row["city"] and row["headline_problem"] for row in rows)

    await import_keys(session_factory, organization_id, ["bluebird-coffee"])
    async with session_factory() as db:
        rows = {row["key"]: row for row in await catalogue(db, organization_id)}
    assert rows["bluebird-coffee"]["imported"] is True
    assert UUID(rows["bluebird-coffee"]["location_id"])
    assert rows["riverside-grill"]["imported"] is False


async def test_import_writes_the_profile_and_every_related_table(session_factory):
    organization_id = await make_organization(session_factory)
    result = await import_keys(session_factory, organization_id, ["carter-auto-works"])
    assert [row["key"] for row in result.imported] == ["carter-auto-works"]
    location_id = UUID(result.imported[0]["location_id"])

    async with session_factory() as db:
        location = await db.get(Location, location_id)
        assert location.organization_id == organization_id
        # How an imported row is marked: the fixture source plus a natural key that
        # names the archetype and carries the idempotence constraint.
        assert location.source is LocationSource.fixture
        assert location.google_location_name == f"{NAME_PREFIX}carter-auto-works"
        assert location.title == "Carter Auto Works"
        assert location.locality == "Phoenix"

        async def count(model, column="location_id"):
            return await db.scalar(
                select(func.count()).select_from(model).where(getattr(model, column) == location_id)
            )

        assert await count(Review) > 50
        assert await count(PerformanceDaily) > 100
        assert await count(SearchTermMonthly) > 20
        assert await count(Booking) > 30
        assert await count(TrackedKeyword) >= 6
        assert await count(KeywordRank) >= 48
        assert await count(LocationCategory) >= 1
        assert await count(MediaSummary) == 1
        # Competitor observations hang off the keyword, not the location.
        keywords = select(TrackedKeyword.id).where(TrackedKeyword.location_id == location_id)
        keyword_ids = (await db.scalars(keywords)).all()
        rivals = await db.scalar(
            select(func.count())
            .select_from(CompetitorObservation)
            .where(CompetitorObservation.tracked_keyword_id.in_(keyword_ids))
        )
        assert rivals > 100

        # The dashboard is project-scoped, so an imported profile always joins one.
        project_id = await db.scalar(
            select(ProjectLocation.project_id).where(ProjectLocation.location_id == location_id)
        )
        project = await db.get(Project, project_id)
        assert project.organization_id == organization_id
        assert project.services  # the service list the relevance checks read


async def test_importing_the_same_key_twice_is_a_no_op(session_factory):
    organization_id = await make_organization(session_factory)
    first = await import_keys(session_factory, organization_id, ["bluebird-coffee", "hartley-law"])
    assert len(first.imported) == 2 and first.skipped == []

    second = await import_keys(
        session_factory, organization_id, ["bluebird-coffee", "hartley-law", "greenleaf-pharmacy"]
    )
    assert [row["key"] for row in second.imported] == ["greenleaf-pharmacy"]
    assert second.skipped == ["bluebird-coffee", "hartley-law"]

    async with session_factory() as db:
        locations = await db.scalar(
            select(func.count())
            .select_from(Location)
            .where(Location.organization_id == organization_id)
        )
        reviews = await db.scalar(
            select(func.count())
            .select_from(Review)
            .where(Review.organization_id == organization_id)
        )
        projects = await db.scalar(
            select(func.count())
            .select_from(Project)
            .where(Project.organization_id == organization_id)
        )
    assert locations == 3 and projects == 3
    # The re-imported pair did not double their reviews.
    expected = sum(
        len(generate(a, REFERENCE).reviews)
        for a in ARCHETYPES
        if a.key in {"bluebird-coffee", "hartley-law", "greenleaf-pharmacy"}
    )
    assert reviews == expected


async def test_an_unknown_key_is_reported_without_stopping_the_batch(session_factory):
    organization_id = await make_organization(session_factory)
    result = await import_keys(
        session_factory, organization_id, ["bluebird-coffee", "not-a-real-profile"]
    )
    assert [row["key"] for row in result.imported] == ["bluebird-coffee"]
    assert result.unknown == ["not-a-real-profile"]
    with pytest.raises(KeyError):
        generate.__globals__["by_key"]("not-a-real-profile")


async def test_another_organization_sees_none_of_it(session_factory):
    mine = await make_organization(session_factory, "Mine", "mine")
    theirs = await make_organization(session_factory, "Theirs", "theirs")
    await import_keys(session_factory, mine, ["bluebird-coffee"])

    async with session_factory() as db:
        rows = await catalogue(db, theirs)
        assert all(row["imported"] is False for row in rows)
        visible = await db.scalar(
            select(func.count()).select_from(Location).where(Location.organization_id == theirs)
        )
    assert visible == 0

    # The same key imports cleanly for the other tenant: idempotence is per organization.
    result = await import_keys(session_factory, theirs, ["bluebird-coffee"])
    assert len(result.imported) == 1 and result.skipped == []


# The rules each archetype exists to fail. Every one of these must come back `triggered`:
# an `insufficient_data` here would mean the generated data is thin rather than bad.
INTENDED = {
    "riverside-grill": (
        "poor",
        (
            "rating_low",
            "one_star_share_high",
            "rating_trend_falling",
            "reply_rate_low",
            "critical_reply_rate_low",
            "critical_review_unanswered",
            "reply_delay_high",
            "reviews_few_vs_competitors",
            "photos_few",
            "photo_type_empty",
            "photos_stale",
            "posts_none_recent",
            "hours_missing",
            "unverified",
            "impressions_decline",
            "calls_decline",
        ),
    ),
    "ironclad-strength": (
        "poor",
        (
            "pack_share_low",
            "pack_lost",
            "not_found_persistent",
            "rank_dropped",
            "branded_not_first",
            "search_term_losing",
            "near_pack_opportunity",
            "name_keyword_stuffed",
            "phone_missing",
            "website_not_https",
            "unverified",
            "description_missing",
            "attributes_sparse",
            "accessibility_unanswered",
        ),
    ),
    "carter-auto-works": (
        "fair",
        (
            "requests_unanswered",
            "requests_expired",
            "confirmation_rate_low",
            "cancellation_rate_high",
            "no_show_rate_high",
            "service_not_listed",
            "weekend_demand_without_hours",
            "lead_time_shrinking",
            "channel_concentrated",
            "google_bookings_untracked",
            "high_intent_lagging",
            "rating_low",
        ),
    ),
    "paws-and-claws-vet": (
        "fair",
        (
            "impressions_decline",
            "calls_decline",
            "directions_decline",
            "website_clicks_decline",
            "action_rate_decline",
            "zero_action_days",
            "data_gaps",
            "surface_split_shift",
            "requests_unanswered",
            "no_show_rate_high",
        ),
    ),
    "greenleaf-pharmacy": (
        "poor",
        (
            "phone_missing",
            "website_missing",
            "unverified",
            "description_missing",
            "address_incomplete",
            "logo_missing",
            "cover_photo_missing",
            "attributes_sparse",
            "accessibility_unanswered",
            "photos_few",
            "posts_none_recent",
            "video_missing",
        ),
    ),
}

BANDS = {"poor": (0, 49), "fair": (50, 74)}


async def audit_imported(session_factory, organization_id: UUID, location_id: UUID) -> dict:
    """The real pipeline: prepare the snapshot, run all six workers, publish the run."""
    async with session_factory() as db:
        job = new_job(organization_id, location_id, REFERENCE, EngineConfig())
        db.add(job)
        await db.commit()
        job_id = job.id
    await run_job(job_id, session_factory)
    async with session_factory() as db:
        run = await db.scalar(
            select(RecommendationRun).where(RecommendationRun.location_id == location_id)
        )
        assert run is not None, "the pipeline published no run"
        return run.report


@pytest.mark.parametrize("key", sorted(INTENDED))
async def test_the_real_audit_scores_the_generated_profile_in_its_intended_band(
    session_factory, key
):
    organization_id = await make_organization(session_factory)
    result = await import_keys(session_factory, organization_id, [key])
    location_id = UUID(result.imported[0]["location_id"])
    report = await audit_imported(session_factory, organization_id, location_id)

    health = report["location"]["health"]
    grade, rules = INTENDED[key]
    low, high = BANDS[grade]
    assert health["score"] is not None, "a null score means the data was thin, not bad"
    assert health["grade"] == grade, f"{key} scored {health['score']} ({health['grade']})"
    assert low <= health["score"] <= high
    # Most checks were actually judged: a flattering score from low coverage is the
    # failure mode this whole package exists to avoid.
    assert health["coverage"] >= 0.8
    assert health["issues"] >= 50

    states = {row["rule"]: row["state"] for row in report["evaluations"]}
    abstained = sorted(r for r in rules if states.get(r) != "triggered")
    assert not abstained, f"{key}: expected these to fire, got {[states.get(r) for r in abstained]}"

    # Every worker reported, and the findings carry usable evidence.
    assert {row["category"] for row in report["evaluations"]} == {
        "profile",
        "reputation",
        "visibility",
        "operations",
        "performance",
        "content",
    }
    assert all(item["evidence"] for item in report["items"])
    assert report["location"]["priorities"]


async def test_every_archetype_is_scored_and_none_comes_back_unevaluated(session_factory):
    """No archetype may produce a `not_evaluated` grade, which demos worse than nothing."""
    organization_id = await make_organization(session_factory)
    result = await import_keys(session_factory, organization_id, KEYS)
    assert len(result.imported) == 10

    scores = {}
    for row in result.imported:
        report = await audit_imported(session_factory, organization_id, UUID(row["location_id"]))
        health = report["location"]["health"]
        scores[row["key"]] = health["score"]
        assert health["grade"] in ("poor", "fair"), f"{row['key']} graded {health['grade']}"
        assert health["coverage"] >= 0.8
        # The category the archetype says it fails must actually be its weak spot.
        by_category = {c["category"]: c["score"] for c in health["categories"]}
        for category in next(a for a in ARCHETYPES if a.key == row["key"]).failing:
            assert by_category[category] is not None
            assert by_category[category] <= 75, f"{row['key']}/{category}={by_category[category]}"
    assert max(scores.values()) - min(scores.values()) >= 15, "the scores should spread"


async def test_import_can_join_an_existing_project(session_factory):
    organization_id = await make_organization(session_factory)
    async with session_factory() as db:
        project = Project(organization_id=organization_id, name="Demo fleet", slug="demo-fleet")
        db.add(project)
        await db.commit()
        project_id = project.id

    result = await import_keys(
        session_factory, organization_id, ["bluebird-coffee"], project_id=project_id
    )
    location_id = UUID(result.imported[0]["location_id"])
    async with session_factory() as db:
        linked = (
            await db.scalars(
                select(ProjectLocation.project_id).where(
                    ProjectLocation.location_id == location_id
                )
            )
        ).all()
    assert linked == [project_id]


async def test_a_missing_location_is_not_invented(session_factory):
    organization_id = await make_organization(session_factory)
    async with session_factory() as db:
        assert await db.get(Location, uuid4()) is None
        rows = await catalogue(db, organization_id)
    assert all(row["location_id"] is None for row in rows)


# ---- the HTTP layer ------------------------------------------------------------------


async def test_the_catalogue_endpoint_is_scoped_to_the_caller(client):
    assert (await client.get("/api/v1/demo-profiles")).status_code == 401

    headers, _ = await sign_in(client)
    body = (await client.get("/api/v1/demo-profiles", headers=headers)).json()
    assert [row["key"] for row in body["items"]] == KEYS
    first = body["items"][0]
    assert set(first) == {
        "key",
        "name",
        "industry",
        "city",
        "headline_problem",
        "expected_grade",
        "imported",
        "location_id",
    }
    assert first["imported"] is False and first["location_id"] is None


async def test_import_endpoint_creates_profiles_and_skips_what_is_already_there(client):
    headers, _ = await sign_in(client)
    response = await client.post(
        "/api/v1/demo-profiles/import",
        headers=headers,
        json={"keys": ["bluebird-coffee", "hartley-law"]},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert [row["key"] for row in body["imported"]] == ["bluebird-coffee", "hartley-law"]
    assert all(UUID(row["location_id"]) for row in body["imported"])
    assert body["skipped"] == [] and body["unknown"] == []

    # The catalogue now says so, and the profiles are listable.
    catalogue_rows = {
        row["key"]: row
        for row in (await client.get("/api/v1/demo-profiles", headers=headers)).json()["items"]
    }
    assert catalogue_rows["bluebird-coffee"]["imported"] is True
    locations = (await client.get("/api/v1/locations", headers=headers)).json()
    assert {row["title"] for row in locations} == {
        "Bluebird Coffee House",
        "Hartley & Boyd Law Offices",
    }

    # A second import of the same keys is a no-op.
    again = await client.post(
        "/api/v1/demo-profiles/import",
        headers=headers,
        json={"keys": ["bluebird-coffee", "hartley-law"]},
    )
    assert again.json() == {"imported": [], "skipped": ["bluebird-coffee", "hartley-law"],
                            "unknown": []}
    assert len((await client.get("/api/v1/locations", headers=headers)).json()) == 2


async def test_an_unknown_key_is_named_without_failing_the_batch(client):
    headers, _ = await sign_in(client)
    body = (
        await client.post(
            "/api/v1/demo-profiles/import",
            headers=headers,
            json={"keys": ["bluebird-coffee", "no-such-profile"]},
        )
    ).json()
    assert [row["key"] for row in body["imported"]] == ["bluebird-coffee"]
    assert body["unknown"] == ["no-such-profile"]

    # A structurally invalid request is still a 422.
    assert (
        await client.post("/api/v1/demo-profiles/import", headers=headers, json={"keys": []})
    ).status_code == 422


async def test_import_joins_the_named_project_and_refuses_another_tenants(client):
    headers, _ = await sign_in(client)
    project = (
        await client.post("/api/v1/projects", headers=headers, json={"name": "Demo fleet"})
    ).json()

    body = (
        await client.post(
            "/api/v1/demo-profiles/import",
            headers=headers,
            json={"keys": ["bluebird-coffee"], "project_id": project["id"]},
        )
    ).json()
    location_id = body["imported"][0]["location_id"]
    scoped = (
        await client.get(
            "/api/v1/locations", headers=headers, params={"project_id": project["id"]}
        )
    ).json()
    assert [row["id"] for row in scoped] == [location_id]

    other, _ = await sign_in(client, email="rival@example.com", organization="Rival Co")
    assert (
        await client.post(
            "/api/v1/demo-profiles/import",
            headers=other,
            json={"keys": ["riverside-grill"], "project_id": project["id"]},
        )
    ).status_code == 404
    # And the other tenant sees none of the first one's imports.
    rows = (await client.get("/api/v1/demo-profiles", headers=other)).json()["items"]
    assert all(row["imported"] is False for row in rows)
