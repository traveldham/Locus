"""Queue audit generation instead of running it inside the request."""

import sqlalchemy as sa

from alembic import op

revision = "20260913_0008"
down_revision = "20260913_0007"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "audit_jobs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "organization_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("pending", "running", "succeeded", "failed", name="audit_job_status"),
            nullable=False,
        ),
        sa.Column("as_of", sa.Date(), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("task_id", sa.String(64), nullable=True),
        sa.Column("stage", sa.String(80), nullable=False, server_default="Queued"),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "run_id",
            sa.Uuid(),
            sa.ForeignKey("recommendation_runs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_audit_jobs_organization_id", "audit_jobs", ["organization_id"])


def downgrade():
    op.drop_table("audit_jobs")
    sa.Enum(name="audit_job_status").drop(op.get_bind(), checkfirst=True)
