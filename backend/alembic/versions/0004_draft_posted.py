"""Add draft_posted flag to research_actions — Phase 3 (draft delivery on approval).

Revision ID: 0004_draft_posted
Revises: 0003_research_actions
Create Date: 2026-07-14
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_draft_posted"
down_revision: Union[str, None] = "0003_research_actions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "research_actions",
        sa.Column("draft_posted", sa.Boolean, nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("research_actions", "draft_posted")
