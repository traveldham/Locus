from datetime import date, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import JSON, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
    """One audit of a single business profile: the pipeline that holds six workers.

    The job reads the profile's records once, so every worker judges the same inputs,
    and it owns the outcome so a finished audit stays findable after the broker has
    forgotten the tasks. Progress is not stored here; it is the workers' progress.
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
    # The inputs every worker reads. Filled once when the job starts.
    snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    run_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("recommendation_runs.id", ondelete="SET NULL"), nullable=True
    )
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    workers: Mapped[list["AuditWorker"]] = relationship(
        back_populates="job", cascade="all, delete-orphan", order_by="AuditWorker.category"
    )


class AuditWorker(Base):
    """One category's share of an audit, run and tracked on its own.

    Six of these make up a job. Each owns its status, stage and result, so the dashboard
    can show which category is still working and a failure in one names that category.
    """

    __tablename__ = "audit_workers"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    job_id: Mapped[UUID] = mapped_column(
        ForeignKey("audit_jobs.id", ondelete="CASCADE"), index=True
    )
    category: Mapped[str] = mapped_column(String(32))
    status: Mapped[AuditJobStatus] = mapped_column(
        Enum(AuditJobStatus, name="audit_job_status", create_constraint=False),
        default=AuditJobStatus.pending,
    )
    stage: Mapped[str] = mapped_column(String(80), default="Queued")
    task_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # The worker's findings and verdicts, assembled into the report once all six land.
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    job: Mapped[AuditJob] = relationship(back_populates="workers")


class AuditCheckHistory(Base):
    """One row per check per audit: enough to say fixed, new or unchanged, and to draw
    a trend, without keeping the audits themselves."""

    __tablename__ = "audit_check_history"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    location_id: Mapped[UUID] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE"), index=True
    )
    run_id: Mapped[UUID] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    rule: Mapped[str] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String(24))
    score: Mapped[int] = mapped_column(Integer, default=0)
    issues: Mapped[int] = mapped_column(Integer, default=0)


class AuditScoreHistory(Base):
    """The health score of every audit a location has had, oldest to newest."""

    __tablename__ = "audit_score_history"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    location_id: Mapped[UUID] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE"), index=True
    )
    run_id: Mapped[UUID] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    issues: Mapped[int] = mapped_column(Integer, default=0)
    coverage: Mapped[float] = mapped_column(Float, default=0.0)
