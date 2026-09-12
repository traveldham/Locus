"""Create performance, content, SEO and bookings tables.

Every table here carries a `source` column holding the permanent provenance mark. The
four tables that can never be fed by Google — tracked keywords, their ranks, competitor
observations and individual bookings — default to 'locus' at the database level, so a
row is marked correctly even when a loader forgets to say so.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260913_0004"
down_revision = "20260913_0003"
branch_labels = None
depends_on = None

data_source = postgresql.ENUM("google", "locus", name="data_source", create_type=False)
post_type = postgresql.ENUM(
    "standard", "event", "offer", "alert", name="post_type", create_type=False
)
post_cta_type = postgresql.ENUM(
    "book", "call", "learn_more", "sign_up", "get_offer", name="post_cta_type", create_type=False
)
search_intent = postgresql.ENUM(
    "general",
    "emergency",
    "cosmetic",
    "pediatric",
    "implants",
    "orthodontics",
    "insurance",
    name="search_intent",
    create_type=False,
)
booking_status = postgresql.ENUM(
    "new",
    "confirmed",
    "completed",
    "cancelled",
    "no_show",
    name="booking_status",
    create_type=False,
)
booking_channel = postgresql.ENUM(
    "website", "google_profile", "phone", "walk_in", name="booking_channel", create_type=False
)

ENUMS = (
    data_source,
    post_type,
    post_cta_type,
    search_intent,
    booking_status,
    booking_channel,
)


def upgrade() -> None:
    bind = op.get_bind()
    for enum in ENUMS:
        enum.create(bind, checkfirst=True)

    op.create_table(
        "performance_daily",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("location_id", sa.Uuid(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        # Nullable throughout: Google omits a metric it has no data for, and an omitted
        # metric is not a zero.
        sa.Column("impressions_maps_desktop", sa.Integer(), nullable=True),
        sa.Column("impressions_maps_mobile", sa.Integer(), nullable=True),
        sa.Column("impressions_search_desktop", sa.Integer(), nullable=True),
        sa.Column("impressions_search_mobile", sa.Integer(), nullable=True),
        sa.Column("website_clicks", sa.Integer(), nullable=True),
        sa.Column("call_clicks", sa.Integer(), nullable=True),
        sa.Column("direction_requests", sa.Integer(), nullable=True),
        sa.Column("conversations", sa.Integer(), nullable=True),
        sa.Column("bookings", sa.Integer(), nullable=True),
        sa.Column("source", data_source, nullable=False, server_default="google"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("location_id", "date"),
    )
    op.create_index(
        "ix_performance_daily_organization_id_date",
        "performance_daily",
        ["organization_id", "date"],
    )

    op.create_table(
        "search_terms_monthly",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("location_id", sa.Uuid(), nullable=False),
        sa.Column("year_month", sa.String(7), nullable=False),
        sa.Column("search_term", sa.String(512), nullable=False),
        sa.Column("impressions", sa.Integer(), nullable=True),
        sa.Column("is_threshold", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("source", data_source, nullable=False, server_default="google"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("location_id", "year_month", "search_term"),
    )
    op.create_index(
        "ix_search_terms_monthly_location_id_year_month",
        "search_terms_monthly",
        ["location_id", "year_month"],
    )

    op.create_table(
        "media_summary",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("location_id", sa.Uuid(), nullable=False),
        sa.Column("photo_count", sa.Integer(), nullable=True),
        sa.Column("interior_photo_count", sa.Integer(), nullable=True),
        sa.Column("exterior_photo_count", sa.Integer(), nullable=True),
        sa.Column("team_photo_count", sa.Integer(), nullable=True),
        sa.Column("video_count", sa.Integer(), nullable=True),
        sa.Column("has_profile_photo", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("has_cover_photo", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("last_photo_uploaded_on", sa.Date(), nullable=True),
        sa.Column("source", data_source, nullable=False, server_default="google"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("location_id"),
    )
    op.create_index("ix_media_summary_organization_id", "media_summary", ["organization_id"])

    op.create_table(
        "posts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("location_id", sa.Uuid(), nullable=False),
        sa.Column("google_post_id", sa.String(255), nullable=False),
        sa.Column("post_type", post_type, nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("cta_type", post_cta_type, nullable=True),
        sa.Column("published_on", sa.Date(), nullable=True),
        sa.Column("source", data_source, nullable=False, server_default="google"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("location_id", "google_post_id"),
    )
    op.create_index("ix_posts_organization_id", "posts", ["organization_id"])
    op.create_index("ix_posts_location_id", "posts", ["location_id"])

    op.create_table(
        "bookings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("location_id", sa.Uuid(), nullable=False),
        sa.Column("external_booking_id", sa.String(64), nullable=False),
        sa.Column("customer_name", sa.String(320), nullable=True),
        sa.Column("service", sa.String(255), nullable=True),
        sa.Column("requested_for_date", sa.Date(), nullable=True),
        sa.Column("status", booking_status, nullable=False),
        sa.Column("booking_source", booking_channel, nullable=True),
        sa.Column("booking_created_at", sa.DateTime(timezone=True), nullable=True),
        # Individual bookings never come from Google — only an aggregate count does.
        sa.Column("source", data_source, nullable=False, server_default="locus"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("location_id", "external_booking_id"),
    )
    op.create_index("ix_bookings_organization_id", "bookings", ["organization_id"])
    op.create_index(
        "ix_bookings_location_id_requested_for_date",
        "bookings",
        ["location_id", "requested_for_date"],
    )

    op.create_table(
        "tracked_keywords",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("location_id", sa.Uuid(), nullable=False),
        sa.Column("external_keyword_id", sa.String(64), nullable=False),
        sa.Column("keyword", sa.String(512), nullable=False),
        sa.Column("search_intent", search_intent, nullable=True),
        sa.Column("device", sa.String(32), nullable=True),
        sa.Column("tracking_started_on", sa.Date(), nullable=True),
        # Our own configuration, not something Google hands back.
        sa.Column("source", data_source, nullable=False, server_default="locus"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("location_id", "external_keyword_id"),
    )
    op.create_index("ix_tracked_keywords_organization_id", "tracked_keywords", ["organization_id"])
    op.create_index("ix_tracked_keywords_location_id", "tracked_keywords", ["location_id"])

    op.create_table(
        "keyword_ranks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("location_id", sa.Uuid(), nullable=False),
        sa.Column("tracked_keyword_id", sa.Uuid(), nullable=False),
        sa.Column("week_start", sa.Date(), nullable=False),
        # NULL means "not found", not rank zero.
        sa.Column("rank_absolute", sa.Integer(), nullable=True),
        sa.Column("rank_in_local_pack", sa.Integer(), nullable=True),
        sa.Column("found", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("result_url", sa.String(1024), nullable=True),
        # No ranking API exists, so this can only ever be ours.
        sa.Column("source", data_source, nullable=False, server_default="locus"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tracked_keyword_id"], ["tracked_keywords.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tracked_keyword_id", "week_start"),
    )
    op.create_index("ix_keyword_ranks_organization_id", "keyword_ranks", ["organization_id"])
    op.create_index("ix_keyword_ranks_location_id", "keyword_ranks", ["location_id"])

    op.create_table(
        "competitor_observations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("tracked_keyword_id", sa.Uuid(), nullable=False),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("competitor_name", sa.String(320), nullable=False),
        sa.Column("competitor_place_id", sa.String(255), nullable=True),
        sa.Column("rank_absolute", sa.Integer(), nullable=True),
        sa.Column("review_count", sa.Integer(), nullable=True),
        sa.Column("average_rating", sa.Float(), nullable=True),
        sa.Column("photo_count", sa.Integer(), nullable=True),
        sa.Column("is_claimed", sa.Boolean(), nullable=True),
        # Google never exposes a rival's profile data.
        sa.Column("source", data_source, nullable=False, server_default="locus"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tracked_keyword_id"], ["tracked_keywords.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        # Deliberately no unique constraint: several competitors share a keyword-week.
    )
    op.create_index(
        "ix_competitor_observations_organization_id",
        "competitor_observations",
        ["organization_id"],
    )
    op.create_index(
        "ix_competitor_observations_tracked_keyword_id_week_start",
        "competitor_observations",
        ["tracked_keyword_id", "week_start"],
    )
    op.create_index(
        "ix_competitor_observations_competitor_place_id",
        "competitor_observations",
        ["competitor_place_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_competitor_observations_competitor_place_id", table_name="competitor_observations"
    )
    op.drop_index(
        "ix_competitor_observations_tracked_keyword_id_week_start",
        table_name="competitor_observations",
    )
    op.drop_index(
        "ix_competitor_observations_organization_id", table_name="competitor_observations"
    )
    op.drop_table("competitor_observations")

    op.drop_index("ix_keyword_ranks_location_id", table_name="keyword_ranks")
    op.drop_index("ix_keyword_ranks_organization_id", table_name="keyword_ranks")
    op.drop_table("keyword_ranks")

    op.drop_index("ix_tracked_keywords_location_id", table_name="tracked_keywords")
    op.drop_index("ix_tracked_keywords_organization_id", table_name="tracked_keywords")
    op.drop_table("tracked_keywords")

    op.drop_index("ix_bookings_location_id_requested_for_date", table_name="bookings")
    op.drop_index("ix_bookings_organization_id", table_name="bookings")
    op.drop_table("bookings")

    op.drop_index("ix_posts_location_id", table_name="posts")
    op.drop_index("ix_posts_organization_id", table_name="posts")
    op.drop_table("posts")

    op.drop_index("ix_media_summary_organization_id", table_name="media_summary")
    op.drop_table("media_summary")

    op.drop_index(
        "ix_search_terms_monthly_location_id_year_month", table_name="search_terms_monthly"
    )
    op.drop_table("search_terms_monthly")

    op.drop_index("ix_performance_daily_organization_id_date", table_name="performance_daily")
    op.drop_table("performance_daily")

    bind = op.get_bind()
    for enum in reversed(ENUMS):
        enum.drop(bind, checkfirst=True)
