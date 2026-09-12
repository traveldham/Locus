"""Performance, search terms, media, bookings — and the sample dataset loader behind them.

The endpoint tests seed rows directly rather than going through the loader, so a change
to the CSVs can never quietly change what an endpoint is asserted to return. The loader
gets its own dataset, written to a temp directory, which is what makes it possible to
assert the thing that matters most about it: a blank cell becomes NULL, not 0.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from conftest import register_router, sign_in
from httpx import AsyncClient
from sqlalchemy import func, select

from app.models import (
    AttributeCatalogItem,
    Booking,
    BookingChannel,
    BookingStatus,
    CompetitorObservation,
    DataSource,
    KeywordRank,
    Location,
    MediaSummary,
    PerformanceDaily,
    Post,
    Project,
    ProjectLocation,
    SearchTermMonthly,
    SyncKind,
    SyncRun,
    SyncStatus,
    TrackedKeyword,
)
from app.services.sample_datasets import load_sample_datasets

from app.api.bookings import router as bookings_router  # isort: skip
from app.api.insights import router as insights_router  # isort: skip

register_router(insights_router)
register_router(bookings_router)

MUELLER = "locations/10293847561122334455"
SOUTH_LAMAR = "locations/10293847561122334456"


async def seed_location(
    session_factory, organization_id: UUID, title: str, google_location_name: str
) -> UUID:
    async with session_factory() as session:
        location = Location(
            organization_id=organization_id,
            google_location_name=google_location_name,
            title=title,
        )
        session.add(location)
        await session.commit()
        return location.id


async def seed_performance(session_factory, organization_id: UUID, rows: list[dict]) -> None:
    async with session_factory() as session:
        session.add_all(PerformanceDaily(organization_id=organization_id, **row) for row in rows)
        await session.commit()


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


async def test_insights_require_authentication(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/insights/performance")).status_code == 401
    assert (await client.get("/api/v1/insights/search-terms")).status_code == 401
    assert (await client.get("/api/v1/insights/media")).status_code == 401
    assert (await client.get("/api/v1/bookings")).status_code == 401
    assert (await client.post("/api/v1/insights/load-sample-data")).status_code == 401


# ---------------------------------------------------------------------------
# Performance
# ---------------------------------------------------------------------------


async def test_performance_filters_by_location_and_date_range(
    client: AsyncClient, session_factory
) -> None:
    headers, organization_id = await sign_in(client)
    mueller = await seed_location(session_factory, organization_id, "Mueller", MUELLER)
    lamar = await seed_location(session_factory, organization_id, "South Lamar", SOUTH_LAMAR)
    await seed_performance(
        session_factory,
        organization_id,
        [
            {"location_id": mueller, "date": date(2026, 6, 15), "website_clicks": 10},
            {"location_id": mueller, "date": date(2026, 6, 16), "website_clicks": 20},
            {"location_id": mueller, "date": date(2026, 6, 17), "website_clicks": 40},
            {"location_id": lamar, "date": date(2026, 6, 16), "website_clicks": 5},
        ],
    )

    everything = (await client.get("/api/v1/insights/performance", headers=headers)).json()
    # Three distinct days, with the two locations summed on the shared one.
    assert [point["date"] for point in everything["points"]] == [
        "2026-06-15",
        "2026-06-16",
        "2026-06-17",
    ]
    assert [point["website_clicks"] for point in everything["points"]] == [10, 25, 40]
    assert everything["totals"]["website_clicks"] == 75
    assert everything["source"] == "google"

    one_location = (
        await client.get(
            "/api/v1/insights/performance", headers=headers, params={"location_id": str(mueller)}
        )
    ).json()
    assert one_location["totals"]["website_clicks"] == 70

    windowed = (
        await client.get(
            "/api/v1/insights/performance",
            headers=headers,
            params={"location_id": str(mueller), "from": "2026-06-16", "to": "2026-06-16"},
        )
    ).json()
    assert [point["date"] for point in windowed["points"]] == ["2026-06-16"]
    assert windowed["totals"]["website_clicks"] == 20


async def test_performance_totals_skip_nulls_instead_of_counting_them_as_zero(
    client: AsyncClient, session_factory
) -> None:
    """The whole point of the nullable metrics: a day Google said nothing about is left
    out of the total and out of the day count, rather than reported as a day of zero."""
    headers, organization_id = await sign_in(client)
    mueller = await seed_location(session_factory, organization_id, "Mueller", MUELLER)
    await seed_performance(
        session_factory,
        organization_id,
        [
            {"location_id": mueller, "date": date(2026, 6, 15), "call_clicks": 9},
            # Google reported nothing for this day at all.
            {"location_id": mueller, "date": date(2026, 6, 16)},
            {"location_id": mueller, "date": date(2026, 6, 17), "call_clicks": 3},
        ],
    )

    body = (
        await client.get(
            "/api/v1/insights/performance", headers=headers, params={"location_id": str(mueller)}
        )
    ).json()

    # The gap is a gap: plotted as null, so the chart draws a break rather than a dip to 0.
    assert [point["call_clicks"] for point in body["points"]] == [9, None, 3]
    assert body["totals"]["call_clicks"] == 12
    # Three rows exist, but only two days actually reported.
    assert len(body["points"]) == 3
    assert body["totals"]["days_with_data"] == 2
    # A metric nobody reported is not invented, and does not inflate the impression split.
    assert body["totals"]["impressions_total"] == 0
    assert body["totals"]["conversations"] == 0


async def test_performance_filters_by_project(client: AsyncClient, session_factory) -> None:
    headers, organization_id = await sign_in(client)
    mueller = await seed_location(session_factory, organization_id, "Mueller", MUELLER)
    lamar = await seed_location(session_factory, organization_id, "South Lamar", SOUTH_LAMAR)
    async with session_factory() as session:
        project = Project(organization_id=organization_id, name="Austin", slug="austin")
        session.add(project)
        await session.flush()
        session.add(ProjectLocation(project_id=project.id, location_id=mueller))
        await session.commit()
        project_id = project.id

    await seed_performance(
        session_factory,
        organization_id,
        [
            {"location_id": mueller, "date": date(2026, 6, 15), "bookings": 4},
            {"location_id": lamar, "date": date(2026, 6, 15), "bookings": 11},
        ],
    )

    body = (
        await client.get(
            "/api/v1/insights/performance", headers=headers, params={"project_id": str(project_id)}
        )
    ).json()
    assert body["totals"]["bookings"] == 4

    missing = await client.get(
        "/api/v1/insights/performance", headers=headers, params={"project_id": str(uuid4())}
    )
    assert missing.status_code == 404


async def test_performance_rejects_another_organizations_location(
    client: AsyncClient, session_factory
) -> None:
    headers, organization_id = await sign_in(client)
    _, other_organization = await sign_in(client, "rival@example.com", "Rival Dental")
    theirs = await seed_location(session_factory, other_organization, "Rival", SOUTH_LAMAR)
    await seed_performance(
        session_factory,
        other_organization,
        [{"location_id": theirs, "date": date(2026, 6, 15), "website_clicks": 99}],
    )
    assert organization_id != other_organization

    response = await client.get(
        "/api/v1/insights/performance", headers=headers, params={"location_id": str(theirs)}
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Search terms
# ---------------------------------------------------------------------------


async def test_search_terms_order_by_impressions_and_keep_the_threshold_flag(
    client: AsyncClient, session_factory
) -> None:
    headers, organization_id = await sign_in(client)
    mueller = await seed_location(session_factory, organization_id, "Mueller", MUELLER)
    async with session_factory() as session:
        session.add_all(
            SearchTermMonthly(
                organization_id=organization_id,
                location_id=mueller,
                year_month=year_month,
                search_term=term,
                impressions=impressions,
                is_threshold=is_threshold,
            )
            for term, year_month, impressions, is_threshold in (
                ("dentist austin", "2026-04", 500, False),
                ("emergency dentist", "2026-04", 900, False),
                ("teeth whitening", "2026-04", 15, True),
                ("root canal austin", "2026-05", 700, False),
            )
        )
        await session.commit()

    body = (
        await client.get(
            "/api/v1/insights/search-terms", headers=headers, params={"year_month": "2026-04"}
        )
    ).json()
    assert [item["search_term"] for item in body["items"]] == [
        "emergency dentist",
        "dentist austin",
        "teeth whitening",
    ]
    assert body["total"] == 3
    assert body["limit"] == 50
    assert body["offset"] == 0
    # "fewer than 15" must never reach the UI looking like a measured 15.
    assert body["items"][-1]["is_threshold"] is True
    assert all(item["source"] == "google" for item in body["items"])

    paged = (
        await client.get(
            "/api/v1/insights/search-terms",
            headers=headers,
            params={"year_month": "2026-04", "limit": 1, "offset": 1},
        )
    ).json()
    assert [item["search_term"] for item in paged["items"]] == ["dentist austin"]
    assert paged["total"] == 3
    assert paged["offset"] == 1


async def test_search_terms_reject_another_organizations_location(
    client: AsyncClient, session_factory
) -> None:
    headers, _ = await sign_in(client)
    _, other_organization = await sign_in(client, "rival@example.com", "Rival Dental")
    theirs = await seed_location(session_factory, other_organization, "Rival", SOUTH_LAMAR)

    response = await client.get(
        "/api/v1/insights/search-terms", headers=headers, params={"location_id": str(theirs)}
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Media
# ---------------------------------------------------------------------------


async def test_media_lists_rollups_with_their_location_title(
    client: AsyncClient, session_factory
) -> None:
    headers, organization_id = await sign_in(client)
    mueller = await seed_location(session_factory, organization_id, "Mueller", MUELLER)
    async with session_factory() as session:
        session.add(
            MediaSummary(
                organization_id=organization_id,
                location_id=mueller,
                photo_count=44,
                interior_photo_count=15,
                video_count=None,
                has_profile_photo=True,
                last_photo_uploaded_on=date(2026, 8, 29),
            )
        )
        await session.commit()

    body = (await client.get("/api/v1/insights/media", headers=headers)).json()
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["location_title"] == "Mueller"
    assert item["photo_count"] == 44
    # No videos counted is not "zero videos" — the rollup never said.
    assert item["video_count"] is None
    assert item["source"] == "google"


# ---------------------------------------------------------------------------
# Bookings
# ---------------------------------------------------------------------------


async def seed_bookings(session_factory, organization_id: UUID, location_id: UUID) -> None:
    async with session_factory() as session:
        session.add_all(
            Booking(
                organization_id=organization_id,
                location_id=location_id,
                external_booking_id=external_id,
                customer_name=customer,
                service="Cleaning",
                requested_for_date=requested,
                status=status,
                booking_source=channel,
                booking_created_at=created,
            )
            for external_id, customer, requested, status, channel, created in (
                (
                    "BK-1",
                    "Matthew P.",
                    date(2026, 7, 20),
                    BookingStatus.confirmed,
                    BookingChannel.google_profile,
                    datetime(2026, 7, 8, tzinfo=UTC),
                ),
                (
                    "BK-2",
                    "Mark B.",
                    date(2026, 8, 8),
                    BookingStatus.cancelled,
                    BookingChannel.walk_in,
                    datetime(2026, 7, 29, tzinfo=UTC),
                ),
                (
                    "BK-3",
                    "Ana R.",
                    date(2026, 9, 1),
                    BookingStatus.confirmed,
                    BookingChannel.phone,
                    datetime(2026, 8, 30, tzinfo=UTC),
                ),
            )
        )
        await session.commit()


async def test_bookings_filter_and_paginate(client: AsyncClient, session_factory) -> None:
    headers, organization_id = await sign_in(client)
    mueller = await seed_location(session_factory, organization_id, "Mueller", MUELLER)
    await seed_bookings(session_factory, organization_id, mueller)

    body = (await client.get("/api/v1/bookings", headers=headers)).json()
    assert body["total"] == 3
    assert body["limit"] == 50
    assert [item["customer_name"] for item in body["items"]] == ["Ana R.", "Mark B.", "Matthew P."]
    assert body["items"][0]["location_title"] == "Mueller"
    assert body["status_counts"] == {"confirmed": 2, "cancelled": 1}
    assert body["source"] == "locus"

    by_status = (
        await client.get("/api/v1/bookings", headers=headers, params={"status": "confirmed"})
    ).json()
    assert by_status["total"] == 2
    # The strip still offers every status, so the filter can be switched back.
    assert by_status["status_counts"] == {"confirmed": 2, "cancelled": 1}

    by_channel = (
        await client.get("/api/v1/bookings", headers=headers, params={"booking_source": "walk_in"})
    ).json()
    assert [item["customer_name"] for item in by_channel["items"]] == ["Mark B."]

    paged = (
        await client.get("/api/v1/bookings", headers=headers, params={"limit": 2, "offset": 2})
    ).json()
    assert paged["total"] == 3
    assert [item["customer_name"] for item in paged["items"]] == ["Matthew P."]


async def test_booking_created_at_is_the_booking_systems_timestamp(
    client: AsyncClient, session_factory
) -> None:
    """`created_at` on the wire is when the request was made, not when we wrote the row —
    the two are days apart and only one of them is what a booking list means."""
    headers, organization_id = await sign_in(client)
    mueller = await seed_location(session_factory, organization_id, "Mueller", MUELLER)
    await seed_bookings(session_factory, organization_id, mueller)

    body = (
        await client.get("/api/v1/bookings", headers=headers, params={"status": "cancelled"})
    ).json()
    item = body["items"][0]
    assert item["created_at"].startswith("2026-07-29")
    assert item["created_at"] == item["booking_created_at"]


async def test_bookings_reject_another_organizations_location(
    client: AsyncClient, session_factory
) -> None:
    headers, _ = await sign_in(client)
    _, other_organization = await sign_in(client, "rival@example.com", "Rival Dental")
    theirs = await seed_location(session_factory, other_organization, "Rival", SOUTH_LAMAR)
    await seed_bookings(session_factory, other_organization, theirs)

    assert (
        await client.get("/api/v1/bookings", headers=headers, params={"location_id": str(theirs)})
    ).status_code == 404
    # And without the filter, their bookings are simply not ours.
    assert (await client.get("/api/v1/bookings", headers=headers)).json()["total"] == 0


# ---------------------------------------------------------------------------
# The sample dataset loader
# ---------------------------------------------------------------------------


def csv_text(columns: list[str], rows: list[str]) -> str:
    """Assemble a CSV from a column list, so the wide headers stay inside 100 columns."""
    return "\n".join([",".join(columns), *rows]) + "\n"


KPI_COLUMNS = [
    "location_id",
    "date",
    "impressions_maps_desktop",
    "impressions_maps_mobile",
    "impressions_search_desktop",
    "impressions_search_mobile",
    "website_clicks",
    "call_clicks",
    "direction_requests",
    "conversations",
    "bookings",
]

MEDIA_COLUMNS = [
    "location_id",
    "photo_count",
    "interior_photo_count",
    "exterior_photo_count",
    "team_photo_count",
    "video_count",
    "has_profile_photo",
    "has_cover_photo",
    "last_photo_uploaded_on",
]

COMPETITOR_COLUMNS = [
    "keyword_id",
    "week_start",
    "competitor_name",
    "competitor_place_id",
    "rank_absolute",
    "review_count",
    "average_rating",
    "photo_count",
    "is_claimed",
]

SAMPLE_CSVS = {
    "attribute_catalog.csv": csv_text(
        [
            "attribute_id",
            "attribute_name",
            "attribute_group",
            "applies_to_category",
            "value_type",
        ],
        ["attr_01,wheelchair_accessible_entrance,accessibility,Dentist,bool"],
    ),
    "locations.csv": csv_text(
        ["location_id", "gbp_location_id"],
        [f"LOC-001,{MUELLER}", f"LOC-002,{SOUTH_LAMAR}"],
    ),
    # LOC-001 day two reports nothing at all; day three reports impressions but no calls.
    # LOC-002 is not imported by the organization under test and must be skipped.
    "location_daily_kpis.csv": csv_text(
        KPI_COLUMNS,
        [
            "LOC-001,2026-06-15,114,455,124,496,46,53,43,8,13",
            "LOC-001,2026-06-16,,,,,,,,,",
            "LOC-001,2026-06-17,10,20,30,40,5,,2,1,0",
            "LOC-002,2026-06-15,1,2,3,4,5,6,7,8,9",
        ],
    ),
    "location_search_terms_monthly.csv": csv_text(
        ["location_id", "year_month", "search_term", "impressions"],
        [
            "LOC-001,2026-04,dentist austin,3888",
            "LOC-001,2026-04,teeth whitening,",
            "LOC-002,2026-04,dentist south lamar,120",
        ],
    ),
    "location_media_summary.csv": csv_text(
        MEDIA_COLUMNS,
        [
            "LOC-001,44,15,14,10,,TRUE,FALSE,2026-08-29",
            "LOC-002,3,1,1,1,0,TRUE,FALSE,2026-08-11",
        ],
    ),
    "posts.csv": csv_text(
        ["post_id", "location_id", "post_type", "summary", "cta_type", "published_on"],
        [
            "POST-00001,LOC-001,OFFER,Smile with confidence.,BOOK,2026-04-02",
            "POST-00002,LOC-001,STANDARD,Open late on Thursdays.,,2026-04-10",
        ],
    ),
    "booking_requests.csv": csv_text(
        [
            "booking_id",
            "location_id",
            "customer_name",
            "service",
            "requested_for_date",
            "status",
            "source",
            "created_at",
        ],
        [
            "BK-00001,LOC-001,Matthew P.,Root canal,2026-07-20,confirmed,google_profile,2026-07-08",
            "BK-00002,LOC-001,Mark B.,Emergency visit,2026-08-08,cancelled,walk_in,2026-07-29",
        ],
    ),
    "tracked_keywords.csv": csv_text(
        ["keyword_id", "location_id", "keyword", "search_intent", "device", "tracking_started_on"],
        [
            "KW-0001,LOC-001,dentist austin,general,mobile,2026-06-15",
            "KW-0002,LOC-002,dentist south lamar,general,desktop,2026-06-15",
        ],
    ),
    # Week two did not find the location: rank_absolute is empty and found is FALSE.
    "keyword_rank_weekly.csv": csv_text(
        [
            "keyword_id",
            "location_id",
            "week_start",
            "rank_absolute",
            "rank_in_local_pack",
            "found",
            "result_url",
        ],
        [
            "KW-0001,LOC-001,2026-06-15,12,,TRUE,https://example.com/austin-mueller",
            "KW-0001,LOC-001,2026-06-22,,,FALSE,",
            "KW-0002,LOC-002,2026-06-15,4,2,TRUE,https://example.com",
        ],
    ),
    "competitor_ranks_weekly.csv": csv_text(
        COMPETITOR_COLUMNS,
        [
            "KW-0001,2026-06-15,Park Dental Center,ChIJ-1,10,315,4.2,25,TRUE",
            "KW-0001,2026-06-15,Cedar Ridge Dental Care,ChIJ-2,12,300,4.8,97,FALSE",
            "KW-0001,2026-06-22,Park Dental Center,ChIJ-1,9,318,4.2,26,TRUE",
            "KW-0002,2026-06-15,Someone Else,ChIJ-3,2,10,3.9,4,TRUE",
        ],
    ),
}


@pytest.fixture
def sample_dataset(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A miniature dataset with the shapes that matter: blanks, an unimported location,
    a keyword-week with several competitors, and a week the location was not found."""
    directory = tmp_path / "sample-data"
    directory.mkdir()
    for name, content in SAMPLE_CSVS.items():
        (directory / name).write_text(content, encoding="utf-8")
    monkeypatch.setattr("app.services.providers.sample_data.data_dir", lambda: directory)
    return directory


EXPECTED_COUNTS = {
    "attribute_catalog_items": 1,
    "performance_daily": 3,
    "search_terms_monthly": 2,
    "media_summary": 1,
    "posts": 2,
    "bookings": 2,
    "tracked_keywords": 1,
    "keyword_ranks": 2,
    "competitor_observations": 3,
}


async def test_loader_reports_a_missing_dataset_as_an_upstream_failure(
    client: AsyncClient, session_factory, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A dataset that is not on disk is a deployment problem, not our 500 — and the
    `SyncRun` records the attempt so it is visible rather than silent."""
    headers, organization_id = await sign_in(client)
    await seed_location(session_factory, organization_id, "Mueller", MUELLER)
    missing = tmp_path / "no-such-dataset"
    monkeypatch.setattr("app.services.providers.sample_data.data_dir", lambda: missing)

    response = await client.post("/api/v1/insights/load-sample-data", headers=headers)
    assert response.status_code == 503
    assert "SAMPLE_DATA_DIR" in response.json()["detail"]

    async with session_factory() as session:
        run = await session.scalar(select(SyncRun))
        assert run is not None
        assert run.status is SyncStatus.failed
        assert run.records_written == 0
        assert run.error


async def test_loader_parses_skips_unimported_locations_and_is_idempotent(
    client: AsyncClient, session_factory, sample_dataset: Path
) -> None:
    headers, organization_id = await sign_in(client)
    await seed_location(session_factory, organization_id, "Mueller", MUELLER)

    first = await client.post("/api/v1/insights/load-sample-data", headers=headers)
    assert first.status_code == 200
    body = first.json()
    assert body["locations_matched"] == 1
    assert body["counts"] == EXPECTED_COUNTS
    assert body["total"] == sum(EXPECTED_COUNTS.values())

    async def table_counts() -> dict[str, int]:
        async with session_factory() as session:
            return {
                "performance_daily": await session.scalar(select(func.count(PerformanceDaily.id))),
                "search_terms_monthly": await session.scalar(
                    select(func.count(SearchTermMonthly.id))
                ),
                "media_summary": await session.scalar(select(func.count(MediaSummary.id))),
                "posts": await session.scalar(select(func.count(Post.id))),
                "attribute_catalog_items": await session.scalar(
                    select(func.count(AttributeCatalogItem.id))
                ),
                "bookings": await session.scalar(select(func.count(Booking.id))),
                "tracked_keywords": await session.scalar(select(func.count(TrackedKeyword.id))),
                "keyword_ranks": await session.scalar(select(func.count(KeywordRank.id))),
                "competitor_observations": await session.scalar(
                    select(func.count(CompetitorObservation.id))
                ),
            }

    assert await table_counts() == EXPECTED_COUNTS

    # Running it again updates in place. Competitors have no unique constraint, so this
    # is the run that would have doubled them.
    second = await client.post("/api/v1/insights/load-sample-data", headers=headers)
    assert second.status_code == 200
    assert second.json()["counts"] == EXPECTED_COUNTS
    assert await table_counts() == EXPECTED_COUNTS

    async with session_factory() as session:
        runs = (
            (await session.execute(select(SyncRun).where(SyncRun.kind == SyncKind.performance)))
            .scalars()
            .all()
        )
        assert len(runs) == 2
        assert all(run.status is SyncStatus.succeeded for run in runs)
        assert all(run.records_written == sum(EXPECTED_COUNTS.values()) for run in runs)


async def test_loader_writes_null_for_empty_metrics_rather_than_zero(
    session_factory, sample_dataset: Path
) -> None:
    """The single most consequential parsing rule in the loader."""
    async with session_factory() as session:
        location = Location(organization_id=uuid4(), google_location_name=MUELLER, title="Mueller")
        # An organization row is not needed for SQLite's foreign keys here; the scoping is
        # what is under test.
        session.add(location)
        await session.commit()
        organization_id = location.organization_id

    async with session_factory() as session:
        result = await load_sample_datasets(session, organization_id)
        await session.commit()
    assert result.locations_matched == 1

    async with session_factory() as session:
        blank_day = await session.scalar(
            select(PerformanceDaily).where(PerformanceDaily.date == date(2026, 6, 16))
        )
        assert blank_day is not None
        assert blank_day.website_clicks is None
        assert blank_day.call_clicks is None
        assert blank_day.impressions_maps_desktop is None

        partial_day = await session.scalar(
            select(PerformanceDaily).where(PerformanceDaily.date == date(2026, 6, 17))
        )
        assert partial_day is not None
        # A genuine zero survives as a zero; only the blank becomes NULL.
        assert partial_day.bookings == 0
        assert partial_day.call_clicks is None

        term = await session.scalar(
            select(SearchTermMonthly).where(SearchTermMonthly.search_term == "teeth whitening")
        )
        assert term is not None and term.impressions is None

        media = await session.scalar(select(MediaSummary))
        assert media is not None and media.video_count is None

        # Not found: no rank, but `found` is its own fact and both are preserved.
        missed = await session.scalar(
            select(KeywordRank).where(KeywordRank.week_start == date(2026, 6, 22))
        )
        assert missed is not None
        assert missed.rank_absolute is None
        assert missed.rank_in_local_pack is None
        assert missed.found is False

        untagged = await session.scalar(select(Post).where(Post.google_post_id == "POST-00002"))
        assert untagged is not None and untagged.cta_type is None


async def test_loader_marks_provenance_per_table(session_factory, sample_dataset: Path) -> None:
    """Four of the eight tables can never come from Google, and say so permanently."""
    async with session_factory() as session:
        location = Location(organization_id=uuid4(), google_location_name=MUELLER, title="Mueller")
        session.add(location)
        await session.commit()
        organization_id = location.organization_id

    async with session_factory() as session:
        await load_sample_datasets(session, organization_id)
        await session.commit()

    async with session_factory() as session:
        for model in (PerformanceDaily, SearchTermMonthly, MediaSummary, Post):
            rows = (await session.execute(select(model))).scalars().all()
            assert rows and all(row.source is DataSource.google for row in rows), model

        for model in (TrackedKeyword, KeywordRank, CompetitorObservation, Booking):
            rows = (await session.execute(select(model))).scalars().all()
            assert rows and all(row.source is DataSource.locus for row in rows), model
