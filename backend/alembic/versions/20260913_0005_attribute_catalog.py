"""Store the complete business-category attribute catalog."""

import sqlalchemy as sa

from alembic import op

revision = "20260913_0005"
down_revision = "20260913_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "attribute_catalog_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("external_attribute_id", sa.String(64), nullable=False),
        sa.Column("attribute_name", sa.String(255), nullable=False),
        sa.Column("attribute_group", sa.String(64), nullable=False),
        sa.Column("applies_to_category", sa.String(255), nullable=False),
        sa.Column("value_type", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "external_attribute_id"),
    )
    op.create_index(
        "ix_attribute_catalog_items_organization_id",
        "attribute_catalog_items",
        ["organization_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_attribute_catalog_items_organization_id", table_name="attribute_catalog_items"
    )
    op.drop_table("attribute_catalog_items")
