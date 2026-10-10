"""Add a real status column to ventures (active, building, standby, archived).

Purely additive: one column with a server default of 'building' for existing
rows (safe, conservative default — never silently claims a venture is
'active' without someone saying so). No existing data is changed beyond
backfilling this one new column, and domain-flipping is set to 'active'
explicitly in the follow-up data migration, not in this schema change.

Revision ID: 0008_venture_status
Revises: 0007_legacy_docs_path
Create Date: 2026-10-06
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008_venture_status"
down_revision: Union[str, None] = "0007_legacy_docs_path"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ventures",
        sa.Column("status", sa.String(20), nullable=False, server_default="building"),
    )


def downgrade() -> None:
    op.drop_column("ventures", "status")
