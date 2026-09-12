"""Create the Google Business Profile platform foundation."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260913_0002"
down_revision = "20260912_0001"
branch_labels = None
depends_on = None

auth_provider = postgresql.ENUM("google", name="auth_provider", create_type=False)
connection_status = postgresql.ENUM(
    "active", "needs_reauth", "revoked", "error", name="connection_status", create_type=False
)
location_source = postgresql.ENUM(
    "google", "fixture", "manual", name="location_source", create_type=False
)
open_status = postgresql.ENUM(
    "open", "closed_temporarily", "closed_permanently", name="open_status", create_type=False
)
project_status = postgresql.ENUM("active", "archived", name="project_status", create_type=False)
sync_kind = postgresql.ENUM(
    "discovery",
    "location_profile",
    "reviews",
    "performance",
    "media",
    "posts",
    name="sync_kind",
    create_type=False,
)
sync_status = postgresql.ENUM(
    "pending", "running", "succeeded", "failed", name="sync_status", create_type=False
)
action_status = postgresql.ENUM(
    "pending",
    "approved",
    "executing",
    "succeeded",
    "failed",
    name="action_status",
    create_type=False,
)

ENUMS = (
    auth_provider,
    connection_status,
    location_source,
    open_status,
    project_status,
    sync_kind,
    sync_status,
    action_status,
)


def upgrade() -> None:
    bind = op.get_bind()
    for enum in ENUMS:
        enum.create(bind, checkfirst=True)

    op.alter_column("users", "password_hash", existing_type=sa.String(255), nullable=True)

    op.create_table(
        "user_identities",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("provider", auth_provider, nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "subject"),
    )
    op.create_index("ix_user_identities_user_id", "user_identities", ["user_id"])

    op.create_table(
        "google_connections",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("google_account_email", sa.String(320), nullable=False),
        sa.Column("google_subject", sa.String(255), nullable=False),
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=False),
        sa.Column("scopes", sa.Text(), nullable=False),
        sa.Column("status", connection_status, nullable=False),
        sa.Column("connected_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["connected_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "google_subject"),
    )
    op.create_index(
        "ix_google_connections_organization_id", "google_connections", ["organization_id"]
    )

    op.create_table(
        "external_accounts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("connection_id", sa.Uuid(), nullable=False),
        sa.Column("resource_name", sa.String(255), nullable=False),
        sa.Column("account_name", sa.String(255), nullable=False),
        sa.Column("account_type", sa.String(64), nullable=True),
        sa.Column("role", sa.String(64), nullable=True),
        sa.Column("verification_state", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["connection_id"], ["google_connections.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("connection_id", "resource_name"),
    )
    op.create_index("ix_external_accounts_connection_id", "external_accounts", ["connection_id"])

    op.create_table(
        "locations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("connection_id", sa.Uuid(), nullable=True),
        sa.Column("external_account_id", sa.Uuid(), nullable=True),
        sa.Column("google_location_name", sa.String(255), nullable=False),
        sa.Column("google_resource_name", sa.String(255), nullable=True),
        sa.Column("place_id", sa.String(255), nullable=True),
        sa.Column("store_code", sa.String(128), nullable=True),
        sa.Column("title", sa.String(320), nullable=False),
        sa.Column("primary_category_name", sa.String(255), nullable=True),
        sa.Column("primary_category_display", sa.String(255), nullable=True),
        sa.Column("address_lines", sa.JSON(), nullable=True),
        sa.Column("locality", sa.String(160), nullable=True),
        sa.Column("administrative_area", sa.String(160), nullable=True),
        sa.Column("postal_code", sa.String(32), nullable=True),
        sa.Column("region_code", sa.String(8), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("phone_primary", sa.String(64), nullable=True),
        sa.Column("website_uri", sa.String(1024), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("open_status", open_status, nullable=True),
        sa.Column("opening_date", sa.Date(), nullable=True),
        sa.Column("has_voice_of_merchant", sa.Boolean(), nullable=False),
        sa.Column("has_pending_edits", sa.Boolean(), nullable=False),
        sa.Column("has_google_updated", sa.Boolean(), nullable=False),
        sa.Column("is_duplicate", sa.Boolean(), nullable=False),
        sa.Column("maps_uri", sa.String(1024), nullable=True),
        sa.Column("new_review_uri", sa.String(1024), nullable=True),
        sa.Column("source", location_source, nullable=False),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["connection_id"], ["google_connections.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["external_account_id"], ["external_accounts.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "google_location_name"),
    )
    op.create_index("ix_locations_organization_id", "locations", ["organization_id"])

    op.create_table(
        "location_categories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("location_id", sa.Uuid(), nullable=False),
        sa.Column("category_name", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_location_categories_location_id", "location_categories", ["location_id"])

    op.create_table(
        "location_hours_periods",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("location_id", sa.Uuid(), nullable=False),
        sa.Column("hours_type", sa.String(32), nullable=False),
        sa.Column("open_day", sa.String(16), nullable=False),
        sa.Column("open_hour", sa.Integer(), nullable=False),
        sa.Column("open_minute", sa.Integer(), nullable=False),
        sa.Column("close_day", sa.String(16), nullable=False),
        sa.Column("close_hour", sa.Integer(), nullable=False),
        sa.Column("close_minute", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_location_hours_periods_location_id", "location_hours_periods", ["location_id"]
    )

    op.create_table(
        "location_attribute_values",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("location_id", sa.Uuid(), nullable=False),
        sa.Column("attribute_id", sa.String(255), nullable=False),
        sa.Column("value_type", sa.String(32), nullable=False),
        sa.Column("values", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("location_id", "attribute_id"),
    )
    op.create_index(
        "ix_location_attribute_values_location_id", "location_attribute_values", ["location_id"]
    )

    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("status", project_status, nullable=False),
        sa.Column("google_connection_id", sa.Uuid(), nullable=True),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["google_connection_id"], ["google_connections.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "slug"),
    )
    op.create_index("ix_projects_organization_id", "projects", ["organization_id"])

    op.create_table(
        "project_locations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("location_id", sa.Uuid(), nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "location_id"),
    )
    op.create_index("ix_project_locations_project_id", "project_locations", ["project_id"])
    op.create_index("ix_project_locations_location_id", "project_locations", ["location_id"])

    op.create_table(
        "sync_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("connection_id", sa.Uuid(), nullable=True),
        sa.Column("kind", sync_kind, nullable=False),
        sa.Column("status", sync_status, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("records_written", sa.Integer(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["connection_id"], ["google_connections.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sync_runs_organization_id", "sync_runs", ["organization_id"])

    op.create_table(
        "profile_actions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("location_id", sa.Uuid(), nullable=True),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("action_type", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", action_status, nullable=False),
        sa.Column("google_response", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_profile_actions_organization_id", "profile_actions", ["organization_id"])
    op.create_index("ix_profile_actions_location_id", "profile_actions", ["location_id"])


def downgrade() -> None:
    op.drop_table("profile_actions")
    op.drop_table("sync_runs")
    op.drop_table("project_locations")
    op.drop_table("projects")
    op.drop_table("location_attribute_values")
    op.drop_table("location_hours_periods")
    op.drop_table("location_categories")
    op.drop_table("locations")
    op.drop_table("external_accounts")
    op.drop_table("google_connections")
    op.drop_table("user_identities")

    op.execute("UPDATE users SET password_hash = '' WHERE password_hash IS NULL")
    op.alter_column("users", "password_hash", existing_type=sa.String(255), nullable=False)

    bind = op.get_bind()
    for enum in reversed(ENUMS):
        enum.drop(bind, checkfirst=True)
