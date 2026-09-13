"""Generate an audit off the request thread and record the outcome on the job row."""

import asyncio
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models import AuditJob, AuditJobStatus
from app.services.recommendations.runs import generate
from app.services.recommendations.types import EngineConfig
from app.worker import celery_app


async def run_job(job_id: UUID, session_factory: async_sessionmaker[AsyncSession]) -> None:
    """The whole job, against whichever database the caller hands it.

    Kept separate from the Celery entry point so tests drive it against their own
    session factory instead of the configured one.
    """
    async with session_factory() as db:
        job = await db.get(AuditJob, job_id)
        if job is None or job.status != AuditJobStatus.pending:
            return
        job.status = AuditJobStatus.running
        job.started_at = datetime.now(UTC)
        job.stage = "Starting"
        job.progress = 5
        await db.commit()

        async def report(stage: str, percent: int) -> None:
            # Committed as it goes so a poll of the job sees the current phase.
            job.stage = stage
            job.progress = percent
            await db.commit()

        try:
            run = await generate(
                db,
                job.organization_id,
                job.location_id,
                job.as_of,
                EngineConfig(**job.config),
                report,
            )
        except Exception as error:  # noqa: BLE001 - the job records every failure
            await db.rollback()
            job = await db.get(AuditJob, job_id)
            if job is not None:
                job.status = AuditJobStatus.failed
                job.error = f"{type(error).__name__}: {error}"[:2000]
                job.stage = "Failed"
                job.finished_at = datetime.now(UTC)
                await db.commit()
            raise
        job.status = AuditJobStatus.succeeded
        job.run_id = run.id
        job.stage = "Done"
        job.progress = 100
        job.finished_at = datetime.now(UTC)
        await db.commit()


async def _run(job_id: UUID) -> None:
    # A worker process owns its own engine: an asyncpg pool cannot be shared across
    # the event loops that `asyncio.run` creates for each task.
    settings = get_settings()
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    try:
        await run_job(job_id, async_sessionmaker(engine, expire_on_commit=False))
    finally:
        await engine.dispose()


@celery_app.task(name="audit.generate", bind=True, max_retries=0)
def generate_audit(self, job_id: str) -> str:
    """Run one queued audit. Retries are off: a rerun is an explicit user action."""
    asyncio.run(_run(UUID(job_id)))
    return job_id
