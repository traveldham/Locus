"""Queue audits for a set of profiles.

Used wherever profiles enter the product - a new project, locations added to one, or a
fresh seed - so a location is never left sitting there unaudited with an empty screen.
"""

from collections.abc import Iterable
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditJob, AuditJobStatus
from app.services.recommendations.types import EngineConfig

ACTIVE = (AuditJobStatus.pending, AuditJobStatus.running)


async def enqueue_audits(
    db: AsyncSession, organization_id: UUID, location_ids: Iterable[UUID]
) -> list[AuditJob]:
    """Queue one audit per profile.

    An audit describes the profile, not the project, so profiles are not duplicated per
    project. Joining a project still queues a fresh audit, so a project never opens onto
    a result someone else produced days ago. A profile already being audited is skipped:
    that job is about to produce exactly this.
    """
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
        AuditJob(
            organization_id=organization_id,
            location_id=location_id,
            as_of=today,
            config=EngineConfig().model_dump(),
        )
        for location_id in wanted
        if location_id not in busy
    ]
    if not jobs:
        return []
    db.add_all(jobs)
    await db.commit()

    # Imported here so the queue helper can be used in tests without a broker import
    # cycle through the API module.
    from app.tasks.audit import generate_audit

    for job in jobs:
        job.task_id = generate_audit.delay(str(job.id)).id
    await db.commit()
    return jobs
