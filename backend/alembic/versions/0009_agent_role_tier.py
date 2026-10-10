"""Add role_tier to agents (owner, 2ic, consultant, manager, worker).

Purely additive: one column with a server default of 'worker' for existing
rows (conservative — never silently claims an agent is a manager/consultant
without someone saying so). Real tier values are backfilled in a separate
data-only pass (scripts/backfill_role_tier.py) against the known org chart,
not in this schema migration.

Revision ID: 0009_agent_role_tier
Revises: 0008_venture_status
Create Date: 2026-10-08
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009_agent_role_tier"
down_revision: Union[str, None] = "0008_venture_status"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "agents",
        sa.Column("role_tier", sa.String(20), nullable=False, server_default="worker"),
    )
    op.create_index("ix_agents_role_tier", "agents", ["role_tier"])


def downgrade() -> None:
    op.drop_index("ix_agents_role_tier", table_name="agents")
    op.drop_column("agents", "role_tier")
