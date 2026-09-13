"""Local-search position: tracked keywords, their weekly ranks, and the rivals around them.

None of this comes from Google and none of it ever can — there is no ranking API, Google
never discloses a competitor's profile, and the keyword list is our own configuration.
Every row is stored `source = locus` and every response repeats that, so the screen can
say where the numbers came from instead of letting a user assume their Google dashboard
should agree with them.

The other thing this module refuses to do is treat "not found" as a bad rank. A week the
location did not appear has `rank_absolute = NULL`; it is a gap in the line, never a
plotted zero and never a hundredth place.
"""

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import and_, func, select

from app.api.dependencies import DbSession
from app.api.scoping import OrganizationId, project_locations
from app.models import (
    CompetitorObservation,
    DataSource,
    KeywordRank,
    Location,
    TrackedKeyword,
)
from app.schemas import (
    CompetitorListResponse,
    CompetitorObservationResponse,
    KeywordRankPoint,
    KeywordRankSeriesResponse,
    TrackedKeywordListResponse,
    TrackedKeywordResponse,
)

router = APIRouter(prefix="/market", tags=["Market"])


async def owned_location(db: DbSession, organization_id: UUID, location_id: UUID) -> None:
    owns = await db.scalar(
        select(Location.id).where(
            Location.id == location_id, Location.organization_id == organization_id
        )
    )
    if owns is None:
        raise HTTPException(status_code=404, detail="Location not found")


async def owned_keyword(
    db: DbSession, organization_id: UUID, tracked_keyword_id: UUID
) -> TrackedKeyword:
    keyword = await db.scalar(
        select(TrackedKeyword).where(
            TrackedKeyword.id == tracked_keyword_id,
            TrackedKeyword.organization_id == organization_id,
        )
    )
    if keyword is None:
        raise HTTPException(status_code=404, detail="Tracked keyword not found")
    return keyword


@router.get("/keywords", response_model=TrackedKeywordListResponse)
async def list_keywords(
    organization_id: OrganizationId,
    db: DbSession,
    location_id: UUID | None = None,
    project_id: UUID | None = None,
) -> TrackedKeywordListResponse:
    """Every tracked keyword with where it stood at the last check.

    The latest rank is picked in SQL with a window function rather than by fetching each
    keyword's history and taking the last row — a hundred keywords would otherwise be a
    hundred round trips.
    """
    latest = (
        select(
            KeywordRank.tracked_keyword_id.label("tracked_keyword_id"),
            KeywordRank.rank_absolute.label("rank_absolute"),
            func.row_number()
            .over(
                partition_by=KeywordRank.tracked_keyword_id,
                order_by=(KeywordRank.week_start.desc(), KeywordRank.id),
            )
            .label("recency"),
        )
        .where(KeywordRank.organization_id == organization_id)
        .subquery()
    )

    statement = (
        select(TrackedKeyword, latest.c.rank_absolute)
        .outerjoin(
            latest,
            and_(latest.c.tracked_keyword_id == TrackedKeyword.id, latest.c.recency == 1),
        )
        .where(TrackedKeyword.organization_id == organization_id)
    )
    if project_id is not None:
        statement = statement.where(
            TrackedKeyword.location_id.in_(await project_locations(db, organization_id, project_id))
        )
    if location_id is not None:
        await owned_location(db, organization_id, location_id)
        statement = statement.where(TrackedKeyword.location_id == location_id)

    result = await db.execute(statement.order_by(TrackedKeyword.keyword, TrackedKeyword.id))
    items = []
    for keyword, latest_rank in result.all():
        item = TrackedKeywordResponse.model_validate(keyword)
        # None here means the most recent check did not find the location — the row
        # exists, the position does not.
        item.latest_rank = latest_rank
        items.append(item)
    return TrackedKeywordListResponse(items=items, total=len(items), source=DataSource.locus)


@router.get("/rankings", response_model=KeywordRankSeriesResponse)
async def read_rankings(
    tracked_keyword_id: UUID,
    organization_id: OrganizationId,
    db: DbSession,
    start: Annotated[date | None, Query(alias="from")] = None,
    end: Annotated[date | None, Query(alias="to")] = None,
) -> KeywordRankSeriesResponse:
    """One keyword's weekly position, oldest week first."""
    keyword = await owned_keyword(db, organization_id, tracked_keyword_id)

    conditions = [
        KeywordRank.organization_id == organization_id,
        KeywordRank.tracked_keyword_id == tracked_keyword_id,
    ]
    if start is not None:
        conditions.append(KeywordRank.week_start >= start)
    if end is not None:
        conditions.append(KeywordRank.week_start <= end)

    result = await db.execute(
        select(KeywordRank).where(*conditions).order_by(KeywordRank.week_start, KeywordRank.id)
    )
    ranks = list(result.scalars())
    points = [KeywordRankPoint.model_validate(rank) for rank in ranks]

    summary = TrackedKeywordResponse.model_validate(keyword)
    summary.latest_rank = points[-1].rank_absolute if points else None
    return KeywordRankSeriesResponse(
        keyword=summary,
        points=points,
        weeks_in_local_pack=sum(1 for rank in ranks if rank.rank_in_local_pack is not None),
        weeks_checked=len(ranks),
        source=DataSource.locus,
    )


@router.get("/competitors", response_model=CompetitorListResponse)
async def read_competitors(
    tracked_keyword_id: UUID,
    organization_id: OrganizationId,
    db: DbSession,
    week_start: date | None = None,
) -> CompetitorListResponse:
    """The businesses that ranked around us on one keyword, for one week.

    With no week given this answers for the most recent one observed, which is what the
    screen opens on.
    """
    await owned_keyword(db, organization_id, tracked_keyword_id)

    if week_start is None:
        week_start = await db.scalar(
            select(func.max(CompetitorObservation.week_start)).where(
                CompetitorObservation.organization_id == organization_id,
                CompetitorObservation.tracked_keyword_id == tracked_keyword_id,
            )
        )
    if week_start is None:
        # The keyword exists but nothing has been observed for it yet.
        return CompetitorListResponse(items=[], total=0, source=DataSource.locus)

    result = await db.execute(
        select(CompetitorObservation)
        .where(
            CompetitorObservation.organization_id == organization_id,
            CompetitorObservation.tracked_keyword_id == tracked_keyword_id,
            CompetitorObservation.week_start == week_start,
        )
        # An unranked rival sorts after the ranked ones instead of ahead of first place.
        .order_by(
            CompetitorObservation.rank_absolute.asc().nulls_last(),
            CompetitorObservation.competitor_name,
        )
    )
    items = [CompetitorObservationResponse.model_validate(row) for row in result.scalars()]
    return CompetitorListResponse(
        items=items, total=len(items), week_start=week_start, source=DataSource.locus
    )
