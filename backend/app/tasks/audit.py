"""Run an audit off the request thread: one pipeline, six workers, one finish.

Three async steps do the work against whichever database they are handed, so tests
drive them in-process. The Celery tasks at the bottom are thin wrappers that chain
them: `generate_audit` prepares the job and fans out one `audit_worker` task per
category, and a chord runs `finish_audit` once all six have reported.
"""

import asyncio
from datetime import UTC, datetime
from uuid import UUID

from celery import chord
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.models import AuditJob, AuditJobStatus
from app.services.recommendations.categories import WORKERS
from app.services.recommendations.engine import assemble, run_worker
from app.services.recommendations.runs import save_run
from app.services.recommendations.snapshot import read_snapshot
from app.services.recommendations.types import EngineConfig
from app.worker import celery_app

SessionFactory = async_sessionmaker[AsyncSession]


def now() -> datetime:
    return datetime.now(UTC)


async def load_job(db: AsyncSession, job_id: UUID) -> AuditJob | None:
    return await db.scalar(
        select(AuditJob).where(AuditJob.id == job_id).options(selectinload(AuditJob.workers))
    )


async def prepare_job(job_id: UUID, session_factory: SessionFactory) -> bool:
    """Read the profile's records once, so every worker judges the same inputs."""
    async with session_factory() as db:
        job = await load_job(db, job_id)
        if job is None or job.status != AuditJobStatus.pending:
            return False
        job.status = AuditJobStatus.running
        job.started_at = now()
        try:
            job.snapshot = await read_snapshot(db, job.organization_id, job.location_id)
        except Exception as error:  # noqa: BLE001 - the job records every failure
            await db.rollback()
            await fail_job(db, job_id, f"{type(error).__name__}: {error}")
            return False
        await db.commit()
        return True


async def run_category(job_id: UUID, category: str, session_factory: SessionFactory) -> None:
    """One worker: its category's checks against the job's snapshot.

    Never raises. A failure is written on the worker row so the pipeline can still
    finish and name the category that did not report.
    """
    async with session_factory() as db:
        job = await load_job(db, job_id)
        if job is None or job.snapshot is None:
            return
        worker = next(w for w in job.workers if w.category == category)
        if worker.status != AuditJobStatus.pending:
            return
        worker.status = AuditJobStatus.running
        worker.stage = "Running checks"
        worker.started_at = now()
        await db.commit()
        try:
            worker.result = run_worker(
                job.snapshot, job.as_of, EngineConfig(**job.config), category
            )
        except Exception as error:  # noqa: BLE001 - recorded on the worker
            worker.status = AuditJobStatus.failed
            worker.stage = "Failed"
            worker.error = f"{type(error).__name__}: {error}"[:2000]
        else:
            worker.status = AuditJobStatus.succeeded
            worker.stage = "Done"
        worker.finished_at = now()
        await db.commit()


async def finish_job(job_id: UUID, session_factory: SessionFactory) -> None:
    """Assemble the six results into the report and publish it as the current audit."""
    async with session_factory() as db:
        job = await load_job(db, job_id)
        if job is None or job.status != AuditJobStatus.running:
            return
        if any(w.status in (AuditJobStatus.pending, AuditJobStatus.running) for w in job.workers):
            # Not every worker has reported. The pipeline stays running.
            return
        failed = [w for w in job.workers if w.status == AuditJobStatus.failed]
        if failed:
            names = ", ".join(f"{w.category} ({w.error})" for w in failed)
            await fail_job(db, job_id, f"Workers failed: {names}")
            return
        try:
            report = assemble(
                job.snapshot,
                job.as_of,
                EngineConfig(**job.config),
                [w.result for w in job.workers],
            )
            run = await save_run(db, job, report)
        except Exception as error:  # noqa: BLE001 - the job records every failure
            await db.rollback()
            await fail_job(db, job_id, f"{type(error).__name__}: {error}")
            return
        job.status = AuditJobStatus.succeeded
        job.run_id = run.id
        job.finished_at = now()
        # The inputs now live on the run; the job does not need its own copy.
        job.snapshot = None
        await db.commit()


async def fail_job(db: AsyncSession, job_id: UUID, error: str) -> None:
    job = await db.get(AuditJob, job_id)
    if job is None:
        return
    job.status = AuditJobStatus.failed
    job.error = error[:2000]
    job.finished_at = now()
    await db.commit()


async def run_job(job_id: UUID, session_factory: SessionFactory) -> None:
    """The whole pipeline in one process: prepare, every worker, finish."""
    if not await prepare_job(job_id, session_factory):
        return
    for worker in WORKERS:
        await run_category(job_id, worker.KEY, session_factory)
    await finish_job(job_id, session_factory)


def session_factory_for_task() -> tuple[SessionFactory, object]:
    # A task owns its own engine: an asyncpg pool cannot be shared across the event
    # loops that `asyncio.run` creates for each task.
    settings = get_settings()
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    return async_sessionmaker(engine, expire_on_commit=False), engine


async def _in_task(step, *args):
    factory, engine = session_factory_for_task()
    try:
        return await step(*args, factory)
    finally:
        await engine.dispose()


@celery_app.task(name="audit.generate", bind=True, max_retries=0)
def generate_audit(self, job_id: str) -> str:
    """Start one queued audit: prepare it, then fan out the six workers."""
    if not asyncio.run(_in_task(prepare_job, UUID(job_id))):
        return job_id
    chord(
        [audit_worker.s(job_id, worker.KEY) for worker in WORKERS],
        finish_audit.s(job_id),
    ).apply_async()
    return job_id


@celery_app.task(name="audit.worker", bind=True, max_retries=0)
def audit_worker(self, job_id: str, category: str) -> str:
    asyncio.run(_in_task(run_category, UUID(job_id), category))
    return category


@celery_app.task(name="audit.finish", bind=True, max_retries=0)
def finish_audit(self, _worker_results: list[str], job_id: str) -> str:
    asyncio.run(_in_task(finish_job, UUID(job_id)))
    return job_id


__all__ = [
    "audit_worker",
    "finish_audit",
    "finish_job",
    "generate_audit",
    "prepare_job",
    "run_category",
    "run_job",
]
