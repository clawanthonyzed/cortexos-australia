"""Multi-tenant venture workspaces — SPEC-COS-04.

Adds the `ventures` table, a nullable `venture_id` FK (ON DELETE SET NULL)
to `agents`, `tasks`, `cost_records`, `memory_items`, `audit_logs`, and
`users`, seeds the 18 empire ventures, and backfills `agents.venture_id`
via the manager-name-prefix heuristic that previously lived in
`venture_health()`.

Revision ID: 0002_venture_workspaces
Revises: 0001_initial
Create Date: 2026-06-10
"""
from __future__ import annotations

import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.seeds.ventures import VENTURE_SEED_DATA

revision: str = "0002_venture_workspaces"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Tables that get a nullable venture_id FK in this migration
_VENTURE_SCOPED_TABLES = ("agents", "tasks", "cost_records", "memory_items", "audit_logs", "users")


def upgrade() -> None:
    # ── Ventures table ────────────────────────────────────────────────────────
    op.create_table(
        "ventures",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("manager_name", sa.String(100), nullable=False),
        sa.Column("category", sa.String(50), nullable=False, server_default="other"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ventures_slug", "ventures", ["slug"])
    op.create_index("ix_ventures_manager_name", "ventures", ["manager_name"])

    # ── venture_id FK on existing tables ─────────────────────────────────────
    for table in _VENTURE_SCOPED_TABLES:
        op.add_column(table, sa.Column("venture_id", postgresql.UUID(as_uuid=True), nullable=True))
        op.create_foreign_key(
            f"fk_{table}_venture_id", table, "ventures", ["venture_id"], ["id"], ondelete="SET NULL"
        )
        op.create_index(f"ix_{table}_venture_id", table, ["venture_id"])

    # ── Seed the 18 empire ventures ──────────────────────────────────────────
    ventures_table = sa.table(
        "ventures",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("slug", sa.String),
        sa.column("name", sa.String),
        sa.column("manager_name", sa.String),
        sa.column("category", sa.String),
    )

    venture_ids: dict[str, uuid.UUID] = {v["slug"]: uuid.uuid4() for v in VENTURE_SEED_DATA}
    op.bulk_insert(
        ventures_table,
        [
            {
                "id": venture_ids[v["slug"]],
                "slug": v["slug"],
                "name": v["name"],
                "manager_name": v["manager_name"],
                "category": v["category"],
            }
            for v in VENTURE_SEED_DATA
        ],
    )

    # ── Backfill agents.venture_id via manager-name prefix match ────────────
    conn = op.get_bind()
    agent_rows = conn.execute(sa.text("SELECT id, name FROM agents")).fetchall()
    for agent_id, agent_name in agent_rows:
        agent_name_lower = (agent_name or "").lower()
        for v in VENTURE_SEED_DATA:
            if agent_name_lower.startswith(v["manager_name"].lower()):
                conn.execute(
                    sa.text("UPDATE agents SET venture_id = :vid WHERE id = :aid"),
                    {"vid": venture_ids[v["slug"]], "aid": agent_id},
                )
                break


def downgrade() -> None:
    for table in _VENTURE_SCOPED_TABLES:
        op.drop_index(f"ix_{table}_venture_id", table_name=table)
        op.drop_constraint(f"fk_{table}_venture_id", table, type_="foreignkey")
        op.drop_column(table, "venture_id")

    op.drop_index("ix_ventures_manager_name", table_name="ventures")
    op.drop_index("ix_ventures_slug", table_name="ventures")
    op.drop_table("ventures")
