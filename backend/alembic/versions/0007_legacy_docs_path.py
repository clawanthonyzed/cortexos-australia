"""Stage 2.4 — link ventures to their legacy business-idea-dash documents.

Purely additive: one nullable column on ventures. No physical files in
business-idea-dash are moved, renamed, or deleted by this migration or by
the data backfill that follows it.

Revision ID: 0007_legacy_docs_path
Revises: 0006_governance_registry
Create Date: 2026-10-06
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007_legacy_docs_path"
down_revision: Union[str, None] = "0006_governance_registry"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ventures",
        sa.Column("legacy_docs_path", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("ventures", "legacy_docs_path")
