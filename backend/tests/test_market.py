"""Tracked keywords, weekly ranks and the competitors around them.

The recurring assertion here is that "not found" is not a rank. A week the location did
not appear carries a null, and the API must hand back a null rather than a zero, a
hundredth place, or last week's number.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

from conftest import register_router, sign_in
from httpx import AsyncClient

from app.models import (
    CompetitorObservation,
    KeywordRank,
    Location,
    SearchIntent,
    TrackedKeyword,
)

from app.api.market import router as market_router  # isort: skip

register_router(market_router)

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


async def seed_keyword(
    session_factory,
    organization_id: UUID,
    location_id: UUID,
    external_keyword_id: str,
    keyword: str,
    ranks: list[tuple[date, int | None, int | None, bool]],
) -> UUID:
    """One tracked keyword and its weekly checks: (week, rank, local pack, found)."""
    async with session_factory() as session:
        tracked = TrackedKeyword(
            organization_id=organization_id,
            location_id=location_id,
            external_keyword_id=external_keyword_id,
            keyword=keyword,
            search_intent=SearchIntent.general,
            device="mobile",
            tracking_started_on=date(2026, 6, 15),
        )
        session.add(tracked)
        await session.flush()
        session.add_all(
            KeywordRank(
                organization_id=organization_id,
                location_id=location_id,
                tracked_keyword_id=tracked.id,
                week_start=week,
                rank_absolute=rank,
                rank_in_local_pack=pack,
                found=found,
            )
            for week, rank, pack, found in ranks
        )
        await session.commit()
        return tracked.id


async def seed_competitors(
    session_factory,
    organization_id: UUID,
    tracked_keyword_id: UUID,
    rows: list[tuple[date, str, int | None]],
) -> None:
    async with session_factory() as session:
        session.add_all(
            CompetitorObservation(
                organization_id=organization_id,
                tracked_keyword_id=tracked_keyword_id,
                week_start=week,
                competitor_name=name,
                competitor_place_id=f"ChIJ-{name.replace(' ', '-')}",
                rank_absolute=rank,
                review_count=120,
                average_rating=4.4,
                photo_count=30,
                is_claimed=True,
            )
            for week, name, rank in rows
        )
        await session.commit()


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


async def test_market_requires_authentication(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/market/keywords")).status_code == 401
    assert (
        await client.get("/api/v1/market/rankings", params={"tracked_keyword_id": str(uuid4())})
    ).status_code == 401
    assert (
        await client.get("/api/v1/market/competitors", params={"tracked_keyword_id": str(uuid4())})
    ).status_code == 401


# ---------------------------------------------------------------------------
# Keywords
# ---------------------------------------------------------------------------


async def test_latest_rank_comes_from_the_most_recent_week(
    client: AsyncClient, session_factory
) -> None:
    headers, organization_id = await sign_in(client)
    mueller = await seed_location(session_factory, organization_id, "Mueller", MUELLER)
    await seed_keyword(
        session_factory,
        organization_id,
        mueller,
        "KW-0001",
        "dentist austin",
        [
            (date(2026, 6, 15), 12, None, True),
            (date(2026, 6, 29), 4, 2, True),
            # Deliberately out of insertion order: recency is decided by the week, not
            # by the order the rows happen to be written in.
            (date(2026, 6, 22), 8, None, True),
        ],
    )

    body = (await client.get("/api/v1/market/keywords", headers=headers)).json()
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["keyword"] == "dentist austin"
    assert item["latest_rank"] == 4
    assert item["search_intent"] == "general"
    assert item["device"] == "mobile"
    assert item["source"] == "locus"
    assert body["source"] == "locus"


async def test_latest_rank_is_null_when_the_last_check_did_not_find_the_location(
    client: AsyncClient, session_factory
) -> None:
    """Not found is not a bad rank. It must not fall back to the previous week's 3."""
    headers, organization_id = await sign_in(client)
    mueller = await seed_location(session_factory, organization_id, "Mueller", MUELLER)
    await seed_keyword(
        session_factory,
        organization_id,
        mueller,
        "KW-0001",
        "dentist austin",
        [
            (date(2026, 6, 15), 3, 1, True),
            (date(2026, 6, 22), None, None, False),
        ],
    )

    body = (await client.get("/api/v1/market/keywords", headers=headers)).json()
    assert body["items"][0]["latest_rank"] is None


async def test_keywords_with_no_ranks_yet_report_no_latest_rank(
    client: AsyncClient, session_factory
) -> None:
    headers, organization_id = await sign_in(client)
    mueller = await seed_location(session_factory, organization_id, "Mueller", MUELLER)
    await seed_keyword(session_factory, organization_id, mueller, "KW-0001", "dentist austin", [])

    body = (await client.get("/api/v1/market/keywords", headers=headers)).json()
    assert body["items"][0]["latest_rank"] is None


async def test_keywords_filter_by_location(client: AsyncClient, session_factory) -> None:
    headers, organization_id = await sign_in(client)
    mueller = await seed_location(session_factory, organization_id, "Mueller", MUELLER)
    lamar = await seed_location(session_factory, organization_id, "South Lamar", SOUTH_LAMAR)
    await seed_keyword(
        session_factory,
        organization_id,
        mueller,
        "KW-0001",
        "dentist austin",
        [(date(2026, 6, 15), 12, None, True)],
    )
    await seed_keyword(
        session_factory,
        organization_id,
        lamar,
        "KW-0002",
        "dentist south lamar",
        [(date(2026, 6, 15), 2, 2, True)],
    )

    everything = (await client.get("/api/v1/market/keywords", headers=headers)).json()
    assert everything["total"] == 2

    one = (
        await client.get(
            "/api/v1/market/keywords", headers=headers, params={"location_id": str(lamar)}
        )
    ).json()
    assert [item["keyword"] for item in one["items"]] == ["dentist south lamar"]


async def test_keywords_reject_another_organizations_location(
    client: AsyncClient, session_factory
) -> None:
    headers, _ = await sign_in(client)
    _, other_organization = await sign_in(client, "rival@example.com", "Rival Dental")
    theirs = await seed_location(session_factory, other_organization, "Rival", SOUTH_LAMAR)
    await seed_keyword(
        session_factory,
        other_organization,
        theirs,
        "KW-0009",
        "rival dentist",
        [(date(2026, 6, 15), 1, 1, True)],
    )

    assert (
        await client.get(
            "/api/v1/market/keywords", headers=headers, params={"location_id": str(theirs)}
        )
    ).status_code == 404
    # And their keywords never appear in our unfiltered list.
    assert (await client.get("/api/v1/market/keywords", headers=headers)).json()["total"] == 0


# ---------------------------------------------------------------------------
# Rankings
# ---------------------------------------------------------------------------


async def test_rankings_return_the_weekly_series_and_honour_a_date_range(
    client: AsyncClient, session_factory
) -> None:
    headers, organization_id = await sign_in(client)
    mueller = await seed_location(session_factory, organization_id, "Mueller", MUELLER)
    keyword_id = await seed_keyword(
        session_factory,
        organization_id,
        mueller,
        "KW-0001",
        "dentist austin",
        [
            (date(2026, 6, 15), 12, None, True),
            (date(2026, 6, 22), None, None, False),
            (date(2026, 6, 29), 3, 1, True),
        ],
    )

    body = (
        await client.get(
            "/api/v1/market/rankings",
            headers=headers,
            params={"tracked_keyword_id": str(keyword_id)},
        )
    ).json()
    assert [point["week_start"] for point in body["points"]] == [
        "2026-06-15",
        "2026-06-22",
        "2026-06-29",
    ]
    # The missed week is a gap in the line, and `found` says why.
    assert [point["rank_absolute"] for point in body["points"]] == [12, None, 3]
    assert [point["found"] for point in body["points"]] == [True, False, True]
    assert body["weeks_checked"] == 3
    assert body["weeks_in_local_pack"] == 1
    assert body["source"] == "locus"

    windowed = (
        await client.get(
            "/api/v1/market/rankings",
            headers=headers,
            params={
                "tracked_keyword_id": str(keyword_id),
                "from": "2026-06-22",
                "to": "2026-06-22",
            },
        )
    ).json()
    assert [point["week_start"] for point in windowed["points"]] == ["2026-06-22"]
    assert windowed["weeks_checked"] == 1


async def test_rankings_reject_another_organizations_keyword(
    client: AsyncClient, session_factory
) -> None:
    headers, _ = await sign_in(client)
    _, other_organization = await sign_in(client, "rival@example.com", "Rival Dental")
    theirs = await seed_location(session_factory, other_organization, "Rival", SOUTH_LAMAR)
    keyword_id = await seed_keyword(
        session_factory,
        other_organization,
        theirs,
        "KW-0009",
        "rival dentist",
        [(date(2026, 6, 15), 1, 1, True)],
    )

    response = await client.get(
        "/api/v1/market/rankings",
        headers=headers,
        params={"tracked_keyword_id": str(keyword_id)},
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Competitors
# ---------------------------------------------------------------------------


async def test_competitors_default_to_the_most_recent_week(
    client: AsyncClient, session_factory
) -> None:
    headers, organization_id = await sign_in(client)
    mueller = await seed_location(session_factory, organization_id, "Mueller", MUELLER)
    keyword_id = await seed_keyword(
        session_factory,
        organization_id,
        mueller,
        "KW-0001",
        "dentist austin",
        [(date(2026, 6, 15), 12, None, True), (date(2026, 6, 22), 8, None, True)],
    )
    await seed_competitors(
        session_factory,
        organization_id,
        keyword_id,
        [
            (date(2026, 6, 15), "Park Dental Center", 10),
            (date(2026, 6, 15), "Cedar Ridge Dental Care", 11),
            # Several rivals share one keyword-week; the latest week has its own set.
            (date(2026, 6, 22), "Park Dental Center", 9),
            (date(2026, 6, 22), "Lakeline Smiles", 4),
            (date(2026, 6, 22), "Unranked Dental", None),
        ],
    )

    latest = (
        await client.get(
            "/api/v1/market/competitors",
            headers=headers,
            params={"tracked_keyword_id": str(keyword_id)},
        )
    ).json()
    assert latest["week_start"] == "2026-06-22"
    # Ranked first, and the rival with no position sorts last instead of ahead of it.
    assert [item["competitor_name"] for item in latest["items"]] == [
        "Lakeline Smiles",
        "Park Dental Center",
        "Unranked Dental",
    ]
    assert latest["items"][-1]["rank_absolute"] is None
    assert latest["items"][0]["review_count"] == 120
    assert latest["items"][0]["is_claimed"] is True
    assert latest["source"] == "locus"

    earlier = (
        await client.get(
            "/api/v1/market/competitors",
            headers=headers,
            params={"tracked_keyword_id": str(keyword_id), "week_start": "2026-06-15"},
        )
    ).json()
    assert earlier["total"] == 2
    assert [item["competitor_name"] for item in earlier["items"]] == [
        "Park Dental Center",
        "Cedar Ridge Dental Care",
    ]


async def test_competitors_for_a_keyword_with_no_observations(
    client: AsyncClient, session_factory
) -> None:
    headers, organization_id = await sign_in(client)
    mueller = await seed_location(session_factory, organization_id, "Mueller", MUELLER)
    keyword_id = await seed_keyword(
        session_factory, organization_id, mueller, "KW-0001", "dentist austin", []
    )

    body = (
        await client.get(
            "/api/v1/market/competitors",
            headers=headers,
            params={"tracked_keyword_id": str(keyword_id)},
        )
    ).json()
    assert body["items"] == []
    assert body["total"] == 0
    assert body["week_start"] is None


async def test_competitors_reject_another_organizations_keyword(
    client: AsyncClient, session_factory
) -> None:
    headers, _ = await sign_in(client)
    _, other_organization = await sign_in(client, "rival@example.com", "Rival Dental")
    theirs = await seed_location(session_factory, other_organization, "Rival", SOUTH_LAMAR)
    keyword_id = await seed_keyword(
        session_factory,
        other_organization,
        theirs,
        "KW-0009",
        "rival dentist",
        [(date(2026, 6, 15), 1, 1, True)],
    )
    await seed_competitors(
        session_factory,
        other_organization,
        keyword_id,
        [(date(2026, 6, 15), "Park Dental Center", 2)],
    )

    response = await client.get(
        "/api/v1/market/competitors",
        headers=headers,
        params={"tracked_keyword_id": str(keyword_id)},
    )
    assert response.status_code == 404
