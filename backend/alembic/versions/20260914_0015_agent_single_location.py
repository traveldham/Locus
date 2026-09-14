"""An agent conversation covers one location, and only ever one location."""

import sqlalchemy as sa

from alembic import op

revision = "20260914_0015"
down_revision = "20260914_0014"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("ck_agent_conversations_one_scope", "agent_conversations", type_="check")
    # A project conversation has no location, and the shape this restores has nowhere to
    # put one: the rows cannot satisfy NOT NULL and there is nothing to derive. Their
    # messages and turns go with them - they are the transcript of a chat about a scope
    # this schema no longer expresses.
    op.execute(sa.text("DELETE FROM agent_conversations WHERE location_id IS NULL"))
    op.alter_column("agent_conversations", "location_id", existing_type=sa.Uuid(), nullable=False)
    op.drop_index("ix_agent_conversations_project_id", table_name="agent_conversations")
    op.drop_column("agent_conversations", "project_id")


def downgrade():
    op.add_column(
        "agent_conversations",
        sa.Column(
            "project_id",
            sa.Uuid(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    op.create_index("ix_agent_conversations_project_id", "agent_conversations", ["project_id"])
    op.alter_column("agent_conversations", "location_id", existing_type=sa.Uuid(), nullable=True)
    op.create_check_constraint(
        "ck_agent_conversations_one_scope",
        "agent_conversations",
        "(location_id IS NULL) <> (project_id IS NULL)",
    )
