"""Business details on existing projects."""

import sqlalchemy as sa

from alembic import op

revision = "20260913_0011"
down_revision = "20260913_0010"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("projects", sa.Column("website_url", sa.String(2083), nullable=True))
    op.add_column("projects", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("projects", sa.Column("services", sa.JSON(), nullable=False, server_default="[]"))


def downgrade():
    op.drop_column("projects", "services")
    op.drop_column("projects", "description")
    op.drop_column("projects", "website_url")
