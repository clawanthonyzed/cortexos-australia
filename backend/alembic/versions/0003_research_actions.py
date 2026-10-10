"""Research loop Phase 2 — approval + outcome tracking.

Adds `research_actions` table: one row per insight posted to Mattermost.
Tracks approve/reject reaction status and schedules an outcome reminder.

Revision ID: 0003_research_actions
Revises: 0002_venture_workspaces
Create Date: 2026-07-14
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_research_actions"
down_revision: Union[str, None] = "0002_venture_workspaces"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "research_actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("venture_slug", sa.String(64), nullable=False),
        sa.Column("mm_post_id", sa.String(64), nullable=False),
        sa.Column("mm_channel_id", sa.String(64), nullable=False),
        sa.Column("insight", sa.Text, nullable=False),
        sa.Column("action", sa.Text, nullable=False),
        sa.Column("action_type", sa.String(64), nullable=False),
        sa.Column("confidence", sa.Float, nullable=False, server_default="0.5"),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reminder_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reminder_sent", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("outcome_notes", sa.Text, nullable=True),
        sa.Column("outcome_captured_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("ix_research_actions_venture_slug", "research_actions", ["venture_slug"])
    op.create_index("ix_research_actions_mm_post_id", "research_actions", ["mm_post_id"])
    op.create_index("ix_research_actions_status", "research_actions", ["status"])


def downgrade() -> None:
    op.drop_index("ix_research_actions_status", table_name="research_actions")
    op.drop_index("ix_research_actions_mm_post_id", table_name="research_actions")
    op.drop_index("ix_research_actions_venture_slug", table_name="research_actions")
    op.drop_table("research_actions")
