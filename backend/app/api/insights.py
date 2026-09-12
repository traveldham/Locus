"""Performance, search terms and media — what the profile did, as Google reports it.

Everything here is read out of our own tables; Google's performance API is a daily pull,
not a per-page-load call. The one thing this module is careful about throughout is the
difference between *zero* and *absent*: Google omits a metric for a day it has no data
for, the loader stores that omission as NULL, and every aggregate below leaves it out
rather than adding a zero. A total over the forty days that reported is a different,
honest number; `days_with_data` is what lets the caller say so on screen.
"""

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import Select, func, or_, select

from app.api.dependencies import DbSession
from app.api.scoping import OrganizationId
from app.models import (
    DataSource,
    Location,
    MediaSummary,
    PerformanceDaily,
    Project,
    ProjectLocation,
    SearchTermMonthly,
    SyncKind,
    SyncRun,
    SyncStatus,
    utcnow,
)
from app.schemas import (
    MediaSummaryListResponse,
    MediaSummaryResponse,
    PerformancePoint,
    PerformanceSeriesResponse,
    PerformanceTotals,
    SampleDataLoadResponse,
    SearchTermListResponse,
    SearchTermResponse,
)
from app.services.sample_datasets import SampleDataError, load_sample_datasets

router = APIRouter(prefix="/insights", tags=["Insights"])

DEFAULT_LIMIT = 50
MAX_LIMIT = 200

# The nine daily metrics, in the order the chart reads them.
METRIC_COLUMNS = (
    PerformanceDaily.impressions_maps_desktop,
    PerformanceDaily.impressions_maps_mobile,
    PerformanceDaily.impressions_search_desktop,
    PerformanceDaily.impressions_search_mobile,
    PerformanceDaily.website_clicks,
    PerformanceDaily.call_clicks,
    PerformanceDaily.direction_requests,
    PerformanceDaily.conversations,
    PerformanceDaily.bookings,
)


async def owned_location(db: DbSession, organization_id: UUID, location_id: UUID) -> None:
    """A location belonging to another organization must be indistinguishable from one
    that does not exist."""
    owns = await db.scalar(
        select(Location.id).where(
            Location.id == location_id, Location.organization_id == organization_id
        )
    )
    if owns is None:
        raise HTTPException(status_code=404, detail="Location not found")


async def owned_project(db: DbSession, organization_id: UUID, project_id: UUID) -> None:
    owns = await db.scalar(
        select(Project.id).where(
            Project.id == project_id, Project.organization_id == organization_id
        )
    )
    if owns is None:
        raise HTTPException(status_code=404, detail="Project not found")


# ---------------------------------------------------------------------------
# Performance
# ---------------------------------------------------------------------------


def totals_from(row: tuple[int | None, ...]) -> PerformanceTotals:
    """Turn one row of SQL SUMs into the totals block.

    Each SUM already skipped the NULL days; a metric that reported on no day at all comes
    back as NULL and is rendered 0 here only because there is nothing to add — which is
    why `days_with_data` travels alongside and says how many days that was over.
    """
    values = [value or 0 for value in row]
    maps_desktop, maps_mobile, search_desktop, search_mobile = values[:4]
    website, calls, directions, conversations, bookings = values[4:]
    return PerformanceTotals(
        impressions_total=maps_desktop + maps_mobile + search_desktop + search_mobile,
        impressions_maps=maps_desktop + maps_mobile,
        impressions_search=search_desktop + search_mobile,
        impressions_desktop=maps_desktop + search_desktop,
        impressions_mobile=maps_mobile + search_mobile,
        website_clicks=website,
        call_clicks=calls,
        direction_requests=directions,
        conversations=conversations,
        bookings=bookings,
    )


@router.get("/performance", response_model=PerformanceSeriesResponse)
async def read_performance(
    organization_id: OrganizationId,
    db: DbSession,
    location_id: UUID | None = None,
    project_id: UUID | None = None,
    start: Annotated[date | None, Query(alias="from")] = None,
    end: Annotated[date | None, Query(alias="to")] = None,
) -> PerformanceSeriesResponse:
    """The daily series and its period totals, for one location or across many.

    Without `location_id` the points are the organization's locations summed per day,
    which is the portfolio view. The sum is done in SQL: a quarter of days across twelve
    locations is a thousand rows nobody needs in Python.
    """
    conditions = [PerformanceDaily.organization_id == organization_id]

    if location_id is not None:
        await owned_location(db, organization_id, location_id)
        conditions.append(PerformanceDaily.location_id == location_id)

    if project_id is not None:
        await owned_project(db, organization_id, project_id)
        conditions.append(
            PerformanceDaily.location_id.in_(
                select(ProjectLocation.location_id).where(ProjectLocation.project_id == project_id)
            )
        )

    if start is not None:
        conditions.append(PerformanceDaily.date >= start)
    if end is not None:
        conditions.append(PerformanceDaily.date <= end)

    # SUM ignores NULL, so a day a location reported nothing contributes nothing instead
    # of dragging the day's figure down with a zero.
    sums = [func.sum(column) for column in METRIC_COLUMNS]

    rows = (
        await db.execute(
            select(PerformanceDaily.date, *sums)
            .where(*conditions)
            .group_by(PerformanceDaily.date)
            .order_by(PerformanceDaily.date)
        )
    ).all()
    points = [
        PerformancePoint(
            date=row[0],
            **{column.key: row[index + 1] for index, column in enumerate(METRIC_COLUMNS)},
        )
        for row in rows
    ]

    totals_row = (await db.execute(select(*sums).where(*conditions))).one()
    totals = totals_from(tuple(totals_row))
    # A day counts as reported when *any* metric came back, which is exactly the
    # condition under which the row would otherwise look like a day of zeroes.
    reported = or_(*(column.is_not(None) for column in METRIC_COLUMNS))
    totals.days_with_data = (
        await db.scalar(
            select(func.count(func.distinct(PerformanceDaily.date))).where(*conditions, reported)
        )
        or 0
    )

    return PerformanceSeriesResponse(
        location_id=location_id,
        start_date=start,
        end_date=end,
        points=points,
        totals=totals,
        source=DataSource.google,
    )


# ---------------------------------------------------------------------------
# Search terms
# ---------------------------------------------------------------------------


@router.get("/search-terms", response_model=SearchTermListResponse)
async def read_search_terms(
    organization_id: OrganizationId,
    db: DbSession,
    location_id: UUID | None = None,
    year_month: Annotated[str | None, Query(pattern=r"^\d{4}-\d{2}$")] = None,
    limit: Annotated[int, Query(ge=1, le=MAX_LIMIT)] = DEFAULT_LIMIT,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> SearchTermListResponse:
    """The queries that surfaced a profile, biggest first.

    `is_threshold` rides along on every row: when Google withholds an exact count and
    reports "fewer than N", the number must be rendered as "<N" and never summed or
    ranked as if it were N.
    """
    statement: Select = (
        select(SearchTermMonthly, Location.title)
        .join(Location, Location.id == SearchTermMonthly.location_id)
        .where(SearchTermMonthly.organization_id == organization_id)
    )

    if location_id is not None:
        await owned_location(db, organization_id, location_id)
        statement = statement.where(SearchTermMonthly.location_id == location_id)

    if year_month is not None:
        statement = statement.where(SearchTermMonthly.year_month == year_month)

    total = await db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    result = await db.execute(
        statement.order_by(
            # A term with no measured volume sorts last rather than first; the id keeps
            # paging stable when several terms tie.
            SearchTermMonthly.impressions.desc().nulls_last(),
            SearchTermMonthly.id,
        )
        .limit(limit)
        .offset(offset)
    )
    return SearchTermListResponse(
        items=[
            SearchTermResponse.model_validate(row).model_copy(update={"location_title": title})
            for row, title in result.all()
        ],
        total=total,
        limit=limit,
        offset=offset,
        source=DataSource.google,
    )


# ---------------------------------------------------------------------------
# Media
# ---------------------------------------------------------------------------


@router.get("/media", response_model=MediaSummaryListResponse)
async def read_media(
    organization_id: OrganizationId,
    db: DbSession,
    location_id: UUID | None = None,
) -> MediaSummaryListResponse:
    """Photo and video counts, one rollup per location."""
    statement = (
        select(MediaSummary, Location.title)
        .join(Location, Location.id == MediaSummary.location_id)
        .where(MediaSummary.organization_id == organization_id)
    )
    if location_id is not None:
        await owned_location(db, organization_id, location_id)
        statement = statement.where(MediaSummary.location_id == location_id)

    result = await db.execute(statement.order_by(Location.title, MediaSummary.id))
    items = []
    for summary, title in result.all():
        item = MediaSummaryResponse.model_validate(summary)
        item.location_title = title
        items.append(item)
    return MediaSummaryListResponse(items=items, total=len(items), source=DataSource.google)


# ---------------------------------------------------------------------------
# Loading the sample dataset
# ---------------------------------------------------------------------------


@router.post("/load-sample-data", response_model=SampleDataLoadResponse)
async def load_sample_data(
    organization_id: OrganizationId, db: DbSession
) -> SampleDataLoadResponse:
    """Fill the analytics tables from the sample CSVs for the caller's organization.

    Safe to run repeatedly: every table is upserted on its natural key. Locations the
    organization has not imported are skipped, so importing more locations and running
    this again simply brings their history along.
    """
    run = SyncRun(
        organization_id=organization_id,
        kind=SyncKind.performance,
        status=SyncStatus.running,
        started_at=utcnow(),
    )
    db.add(run)
    await db.commit()

    try:
        result = await load_sample_datasets(db, organization_id)
    except SampleDataError as exc:
        await db.rollback()
        run.status = SyncStatus.failed
        run.finished_at = utcnow()
        run.error = str(exc)
        await db.commit()
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    run.status = SyncStatus.succeeded
    run.finished_at = utcnow()
    run.records_written = result.total
    await db.commit()

    return SampleDataLoadResponse(
        locations_matched=result.locations_matched,
        total=result.total,
        counts=result.counts,
    )
