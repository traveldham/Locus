"""Preserve the synthetic dataset location join key."""

import sqlalchemy as sa

from alembic import op

revision = "20260913_0006"
down_revision = "20260913_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("locations", sa.Column("source_location_id", sa.String(64), nullable=True))


def downgrade() -> None:
    op.drop_column("locations", "source_location_id")
