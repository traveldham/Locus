"""Per-check and per-score history, so an audit can say fixed, new and trend."""

import sqlalchemy as sa

from alembic import op

revision = "20260913_0012"
down_revision = "20260913_0011"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "audit_check_history",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "organization_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "location_id",
            sa.Uuid(),
            sa.ForeignKey("locations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rule", sa.String(64), nullable=False),
        sa.Column("state", sa.String(24), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("issues", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index(
        "ix_audit_check_history_organization_id", "audit_check_history", ["organization_id"]
    )
    op.create_index("ix_audit_check_history_location_id", "audit_check_history", ["location_id"])
    op.create_index(
        "ix_audit_check_history_location_rule_time",
        "audit_check_history",
        ["location_id", "rule", "created_at"],
    )
    op.create_table(
        "audit_score_history",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "organization_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "location_id",
            sa.Uuid(),
            sa.ForeignKey("locations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("issues", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("coverage", sa.Float(), nullable=False, server_default="0"),
    )
    op.create_index(
        "ix_audit_score_history_organization_id", "audit_score_history", ["organization_id"]
    )
    op.create_index("ix_audit_score_history_location_id", "audit_score_history", ["location_id"])


def downgrade():
    op.drop_table("audit_score_history")
    op.drop_table("audit_check_history")
