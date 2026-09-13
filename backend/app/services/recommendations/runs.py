from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditJob, RecommendationRun
from app.services.recommendations.types import ENGINE_VERSION


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


async def save_run(db: AsyncSession, job: AuditJob, report: dict) -> RecommendationRun:
    """Publish a finished audit as the profile's current one, replacing the last.

    One audit per profile: the previous one is deleted, not archived.
    """
    run = RecommendationRun(
        organization_id=job.organization_id,
        location_id=job.location_id,
        as_of=job.as_of,
        engine_version=ENGINE_VERSION,
        fingerprint=report["fingerprint"],
        report=report,
        snapshot=job.snapshot,
    )
    db.add(run)
    await db.flush()
    await db.execute(
        delete(RecommendationRun).where(
            RecommendationRun.location_id == job.location_id,
            RecommendationRun.id != run.id,
        )
    )
    return run


def serialize(run: RecommendationRun) -> dict:
    return {
        **run.report,
        "id": str(run.id),
        "location_id": str(run.location_id),
        "created_at": run.created_at.isoformat(),
    }
