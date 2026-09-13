"""Save recommendation runs and their immutable evidence inputs."""

import sqlalchemy as sa

from alembic import op

revision = "20260913_0007"
down_revision = "20260913_0006"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "recommendation_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "organization_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("as_of", sa.Date(), nullable=False),
        sa.Column("engine_version", sa.String(32), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("report", sa.JSON(), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
    )
    op.create_index(
        "ix_recommendation_runs_organization_id", "recommendation_runs", ["organization_id"]
    )


def downgrade():
    op.drop_table("recommendation_runs")
