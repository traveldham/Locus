"""Start audits: one job per profile, six workers per job, handed to Celery.

Used by the API and wherever profiles enter the product - a new project, locations
added to one - so a location is never left sitting there unaudited.
"""

from collections.abc import Iterable
from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import AuditJob, AuditJobStatus, AuditWorker
from app.services.recommendations.categories import WORKERS
from app.services.recommendations.types import EngineConfig

ACTIVE = (AuditJobStatus.pending, AuditJobStatus.running)


async def active_job(db: AsyncSession, organization_id: UUID, location_id: UUID) -> AuditJob | None:
    return await db.scalar(
        select(AuditJob)
        .options(selectinload(AuditJob.workers))
        .where(
            AuditJob.organization_id == organization_id,
            AuditJob.location_id == location_id,
            AuditJob.status.in_(ACTIVE),
        )
        .order_by(AuditJob.created_at.desc())
        .limit(1)
    )


def new_job(
    organization_id: UUID, location_id: UUID, as_of: date, config: EngineConfig
) -> AuditJob:
    """A job with its six workers, all queued. Every audit runs every worker."""
    return AuditJob(
        organization_id=organization_id,
        location_id=location_id,
        as_of=as_of,
        config=config.model_dump(),
        workers=[AuditWorker(category=worker.KEY) for worker in WORKERS],
    )


async def dispatch(db: AsyncSession, jobs: list[AuditJob]) -> None:
    """Hand committed jobs to the worker pool and remember the task ids."""
    # Imported here so this helper can be used without a broker import cycle
    # through the API module.
    from app.tasks.audit import generate_audit

    for job in jobs:
        job.task_id = generate_audit.delay(str(job.id)).id
    await db.commit()


async def start_audit(
    db: AsyncSession, organization_id: UUID, location_id: UUID, as_of: date, config: EngineConfig
) -> AuditJob:
    """Queue one audit, or join the one already working on this profile.

    One audit at a time per profile: two concurrent pipelines would race to become
    that profile's current audit.
    """
    running = await active_job(db, organization_id, location_id)
    if running is not None:
        return running
    job = new_job(organization_id, location_id, as_of, config)
    db.add(job)
    await db.commit()
    await dispatch(db, [job])
    return job


async def enqueue_audits(
    db: AsyncSession, organization_id: UUID, location_ids: Iterable[UUID]
) -> list[AuditJob]:
    """Queue one audit per profile, skipping any already being audited."""
    wanted = list(dict.fromkeys(location_ids))
    if not wanted:
        return []
    busy = set(
        (
            await db.scalars(
                select(AuditJob.location_id).where(
                    AuditJob.organization_id == organization_id,
                    AuditJob.location_id.in_(wanted),
                    AuditJob.status.in_(ACTIVE),
                )
            )
        ).all()
    )
    today = datetime.now(UTC).date()
    jobs = [
        new_job(organization_id, location_id, today, EngineConfig())
        for location_id in wanted
        if location_id not in busy
    ]
    if not jobs:
        return []
    db.add_all(jobs)
    await db.commit()
    await dispatch(db, jobs)
    return jobs
