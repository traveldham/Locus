from datetime import date, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import JSON, Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utcnow


class RecommendationRun(Base):
    """The current audit of one business profile."""

    __tablename__ = "recommendation_runs"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    location_id: Mapped[UUID] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    as_of: Mapped[date] = mapped_column(Date)
    engine_version: Mapped[str] = mapped_column(String(32))
    fingerprint: Mapped[str] = mapped_column(String(64))
    report: Mapped[dict] = mapped_column(JSON)
    snapshot: Mapped[dict] = mapped_column(JSON)


class AuditJobStatus(StrEnum):
    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


class AuditJob(Base):
    """One queued request to audit a single business profile.

    The job is the unit the API hands back and the UI polls. It owns the outcome so a
    finished audit stays findable after the broker has forgotten the task.
    """

    __tablename__ = "audit_jobs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    location_id: Mapped[UUID] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[AuditJobStatus] = mapped_column(
        Enum(AuditJobStatus, name="audit_job_status"), default=AuditJobStatus.pending
    )
    as_of: Mapped[date] = mapped_column(Date)
    config: Mapped[dict] = mapped_column(JSON)
    task_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # What the worker is doing right now, in words the dashboard can show directly.
    stage: Mapped[str] = mapped_column(String(80), default="Queued")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    run_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("recommendation_runs.id", ondelete="SET NULL"), nullable=True
    )
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
