"""Create the reviews inbox table."""

import sqlalchemy as sa

from alembic import op

revision = "20260913_0003"
down_revision = "20260913_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reviews",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("location_id", sa.Uuid(), nullable=False),
        sa.Column("google_review_id", sa.String(255), nullable=False),
        sa.Column("google_review_name", sa.String(512), nullable=True),
        sa.Column("reviewer_display_name", sa.String(255), nullable=True),
        sa.Column("reviewer_photo_url", sa.String(1024), nullable=True),
        sa.Column("is_anonymous", sa.Boolean(), nullable=False),
        sa.Column("star_rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("create_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("update_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reply_comment", sa.Text(), nullable=True),
        sa.Column("reply_update_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("location_id", "google_review_id"),
    )
    op.create_index("ix_reviews_organization_id", "reviews", ["organization_id"])
    op.create_index("ix_reviews_location_id_create_time", "reviews", ["location_id", "create_time"])


def downgrade() -> None:
    op.drop_index("ix_reviews_location_id_create_time", table_name="reviews")
    op.drop_index("ix_reviews_organization_id", table_name="reviews")
    op.drop_table("reviews")
