"""An audit is about one business profile, so runs and jobs belong to a location."""

import sqlalchemy as sa

from alembic import op

revision = "20260913_0009"
down_revision = "20260913_0008"
branch_labels = None
depends_on = None


def upgrade():
    # Existing rows audited a whole organization and cannot be attributed to one
    # location. They are regenerable, so they are discarded rather than guessed at.
    op.execute("delete from audit_jobs")
    op.execute("delete from recommendation_runs")
    for table in ("recommendation_runs", "audit_jobs"):
        op.add_column(table, sa.Column("location_id", sa.Uuid(), nullable=False))
        op.create_foreign_key(
            f"fk_{table}_location_id",
            table,
            "locations",
            ["location_id"],
            ["id"],
            ondelete="CASCADE",
        )
        op.create_index(f"ix_{table}_location_id", table, ["location_id"])


def downgrade():
    for table in ("recommendation_runs", "audit_jobs"):
        op.drop_index(f"ix_{table}_location_id", table_name=table)
        op.drop_constraint(f"fk_{table}_location_id", table, type_="foreignkey")
        op.drop_column(table, "location_id")
