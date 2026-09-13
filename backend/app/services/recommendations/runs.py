from collections.abc import Awaitable, Callable
from datetime import date
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Location, RecommendationRun
from app.services.recommendations.engine import analyze, compare
from app.services.recommendations.snapshot import read_snapshot
from app.services.recommendations.types import ENGINE_VERSION, EngineConfig

Progress = Callable[[str, int], Awaitable[None]]


async def latest_run(
    db: AsyncSession, organization_id: UUID, location_id: UUID
) -> RecommendationRun | None:
    """The current audit of one business profile."""
    return await db.scalar(
        select(RecommendationRun)
        .where(
            RecommendationRun.organization_id == organization_id,
            RecommendationRun.location_id == location_id,
        )
        .order_by(RecommendationRun.created_at.desc(), RecommendationRun.id.desc())
        .limit(1)
    )


async def latest_runs(db: AsyncSession, organization_id: UUID) -> list[RecommendationRun]:
    """Every profile's current audit. Each was generated on its own schedule."""
    runs = (
        await db.scalars(
            select(RecommendationRun)
            .where(RecommendationRun.organization_id == organization_id)
            .order_by(RecommendationRun.created_at.desc(), RecommendationRun.id.desc())
        )
    ).all()
    seen: dict[UUID, RecommendationRun] = {}
    for run in runs:
        seen.setdefault(run.location_id, run)
    return list(seen.values())


async def generate(
    db: AsyncSession,
    organization_id: UUID,
    location_id: UUID,
    as_of: date,
    config: EngineConfig | None = None,
    on_stage: Progress | None = None,
) -> RecommendationRun:
    async def stage(label: str, percent: int) -> None:
        if on_stage is not None:
            await on_stage(label, percent)

    owner = await db.scalar(
        select(Location.id).where(
            Location.id == location_id, Location.organization_id == organization_id
        )
    )
    if owner is None:
        raise LookupError("Location not found in this organization")

    await stage("Reading stored records", 10)
    snapshot = await read_snapshot(db, organization_id, location_id)
    await stage("Running checks", 45)
    report = analyze(snapshot, as_of, config)
    await stage("Comparing with the previous audit", 80)
    previous = await latest_run(db, organization_id, location_id)
    compare(report, previous.report if previous else None)
    await stage("Saving evidence", 90)
    run = RecommendationRun(
        organization_id=organization_id,
        location_id=location_id,
        as_of=as_of,
        engine_version=ENGINE_VERSION,
        fingerprint=report["fingerprint"],
        report=report,
        snapshot=snapshot,
    )
    db.add(run)
    await db.commit()
    # One audit per profile. The previous one is kept only long enough to compare
    # against, then replaced: there is no audit history to browse or store.
    await db.execute(
        delete(RecommendationRun).where(
            RecommendationRun.location_id == location_id,
            RecommendationRun.id != run.id,
        )
    )
    await db.commit()
    return run


def serialize(run: RecommendationRun) -> dict:
    return {
        **run.report,
        "id": str(run.id),
        "location_id": str(run.location_id),
        "created_at": run.created_at.isoformat(),
    }
