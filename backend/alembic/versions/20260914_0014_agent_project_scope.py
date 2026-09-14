"""An agent conversation covers one location or one whole project."""

import sqlalchemy as sa

from alembic import op

revision = "20260914_0014"
down_revision = "20260914_0013"
branch_labels = None
depends_on = None


def upgrade():
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
    # Either scope, never both and never neither: the scope is what binds every tool the
    # agent holds, so a row with none or two of them is an agent with no boundary.
    op.create_check_constraint(
        "ck_agent_conversations_one_scope",
        "agent_conversations",
        "(location_id IS NULL) <> (project_id IS NULL)",
    )


def downgrade():
    op.drop_constraint("ck_agent_conversations_one_scope", "agent_conversations", type_="check")
    # A project conversation has no location, and the old shape has nowhere to put it.
    # Its messages and turns go with it: they are a transcript of a chat about a scope
    # this schema cannot express.
    op.execute(sa.text("DELETE FROM agent_conversations WHERE location_id IS NULL"))
    op.alter_column("agent_conversations", "location_id", existing_type=sa.Uuid(), nullable=False)
    op.drop_index("ix_agent_conversations_project_id", table_name="agent_conversations")
    op.drop_column("agent_conversations", "project_id")
