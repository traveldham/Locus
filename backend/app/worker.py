"""Celery application for work that must not block an HTTP request.

The audit reads every analytical row for the organization, so it is queued rather than
run inline. `celery_always_eager` runs tasks in the calling process instead, which is
what the tests and the CLI export use so neither needs a broker.
"""

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "locus",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.audit", "app.tasks.agent"],
)

celery_app.conf.update(
    task_always_eager=settings.celery_always_eager,
    task_eager_propagates=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    task_time_limit=settings.audit_job_timeout_seconds,
    task_soft_time_limit=settings.audit_job_timeout_seconds - 30,
    worker_max_tasks_per_child=50,
    result_expires=3600,
    timezone="UTC",
)
