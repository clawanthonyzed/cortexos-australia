"""SPEC-COS-16 — add source tracking for direct agent memory writes.

Revision ID: 0005_agent_write_access
Revises: 0004_draft_posted
Create Date: 2026-07-17
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_agent_write_access"
down_revision: Union[str, None] = "0004_draft_posted"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "memory_items",
        sa.Column("source", sa.String(20), nullable=False, server_default="dashboard"),
    )
    op.create_index("ix_memory_items_source", "memory_items", ["source"])
    # Existing auto-ingested rows (celery-beat scrapers) are distinguishable
    # by their external_id prefix — reclassify them out of "dashboard".
    op.execute(
        "UPDATE memory_items SET source = 'auto_ingest' "
        "WHERE external_id LIKE 'worklog:%' OR external_id LIKE 'agentfile:%' "
        "OR external_id LIKE 'empire:health:%'"
    )


def downgrade() -> None:
    op.drop_index("ix_memory_items_source", table_name="memory_items")
    op.drop_column("memory_items", "source")
