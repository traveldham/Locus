"""Chat conversations, messages and turns for the GBP operator agent."""

import sqlalchemy as sa

from alembic import op

revision = "20260914_0013"
down_revision = "20260913_0012"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "agent_conversations",
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
        sa.Column(
            "user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("title", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_agent_conversations_organization_id", "agent_conversations", ["organization_id"]
    )
    op.create_index("ix_agent_conversations_location_id", "agent_conversations", ["location_id"])

    agent_message_role = sa.Enum("user", "assistant", "tool", name="agent_message_role")
    op.create_table(
        "agent_messages",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "conversation_id",
            sa.Uuid(),
            sa.ForeignKey("agent_conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", agent_message_role, nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("tool_calls", sa.JSON(), nullable=True),
        sa.Column("tool_call_id", sa.String(64), nullable=True),
        sa.Column("tool_name", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_agent_messages_conversation_id", "agent_messages", ["conversation_id"])

    agent_turn_status = sa.Enum(
        "pending", "running", "succeeded", "failed", name="agent_turn_status"
    )
    op.create_table(
        "agent_turns",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "conversation_id",
            sa.Uuid(),
            sa.ForeignKey("agent_conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "organization_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", agent_turn_status, nullable=False, server_default="pending"),
        sa.Column(
            "user_message_id",
            sa.Uuid(),
            sa.ForeignKey("agent_messages.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("current_tool", sa.String(64), nullable=True),
        sa.Column("task_id", sa.String(64), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_agent_turns_conversation_id", "agent_turns", ["conversation_id"])
    op.create_index("ix_agent_turns_organization_id", "agent_turns", ["organization_id"])
    # One live turn per conversation. The API checks before inserting, but two requests
    # can pass that check at once, and two agents answering into one transcript would
    # interleave their messages into a sequence neither of them could replay.
    op.create_index(
        "uq_agent_turns_one_active_per_conversation",
        "agent_turns",
        ["conversation_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('pending', 'running')"),
        sqlite_where=sa.text("status IN ('pending', 'running')"),
    )


def downgrade():
    op.drop_table("agent_turns")
    sa.Enum(name="agent_turn_status").drop(op.get_bind(), checkfirst=True)
    op.drop_table("agent_messages")
    sa.Enum(name="agent_message_role").drop(op.get_bind(), checkfirst=True)
    op.drop_table("agent_conversations")
