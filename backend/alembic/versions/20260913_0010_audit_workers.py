"""An audit is one pipeline of six category workers, each tracked on its own."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260913_0010"
down_revision = "20260913_0009"
branch_labels = None
depends_on = None


def upgrade():
    # Every earlier audit was produced by the rule set this migration retires. Runs are
    # regenerable, so they are discarded rather than kept as stale evidence.
    op.execute("delete from audit_jobs")
    op.execute("delete from recommendation_runs")

    op.drop_column("audit_jobs", "stage")
    op.drop_column("audit_jobs", "progress")
    op.add_column("audit_jobs", sa.Column("snapshot", sa.JSON(), nullable=True))

    op.create_table(
        "audit_workers",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "job_id",
            sa.Uuid(),
            sa.ForeignKey("audit_jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(name="audit_job_status", create_type=False),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("stage", sa.String(80), nullable=False, server_default="Queued"),
        sa.Column("task_id", sa.String(64), nullable=True),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_audit_workers_job_id", "audit_workers", ["job_id"])
    op.create_unique_constraint(
        "uq_audit_workers_job_category", "audit_workers", ["job_id", "category"]
    )


def downgrade():
    op.drop_table("audit_workers")
    op.drop_column("audit_jobs", "snapshot")
    op.add_column(
        "audit_jobs",
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "audit_jobs",
        sa.Column("stage", sa.String(80), nullable=False, server_default="Queued"),
    )
