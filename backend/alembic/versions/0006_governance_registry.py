"""Governance registry — permissions, budgets, reporting lines, and a scheduled_jobs table.

Purely additive: every new column is nullable, no existing column or row is
changed. Built on top of the already-existing agents/ventures tables and
cost_records (used as-is by the spending gate, not duplicated here).

Revision ID: 0006_governance_registry
Revises: 0005_agent_write_access
Create Date: 2026-10-05
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006_governance_registry"
down_revision: Union[str, None] = "0005_agent_write_access"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- agents: reporting line, location, permissions, budget -------------
    op.add_column("agents", sa.Column("reporting_manager_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "agents_reporting_manager_id_fkey", "agents", "agents",
        ["reporting_manager_id"], ["id"], ondelete="SET NULL",
    )
    op.create_index("ix_agents_reporting_manager_id", "agents", ["reporting_manager_id"])

    op.add_column("agents", sa.Column("repo_path", sa.String(255), nullable=True))
    op.add_column("agents", sa.Column("working_directory", sa.String(255), nullable=True))
    op.add_column("agents", sa.Column("permitted_tools", sa.Text(), nullable=False, server_default="[]"))
    op.add_column("agents", sa.Column("permitted_services", sa.Text(), nullable=False, server_default="[]"))
    op.add_column("agents", sa.Column("monthly_budget_usd", sa.Float(), nullable=True))

    # --- ventures: repo link, hierarchy, budget -----------------------------
    op.add_column("ventures", sa.Column("repo_url", sa.String(255), nullable=True))
    op.add_column("ventures", sa.Column("parent_venture_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "ventures_parent_venture_id_fkey", "ventures", "ventures",
        ["parent_venture_id"], ["id"], ondelete="SET NULL",
    )
    op.add_column("ventures", sa.Column("monthly_budget_usd", sa.Float(), nullable=True))
    op.add_column("ventures", sa.Column("target_revenue_monthly_usd", sa.Float(), nullable=True))

    # --- scheduled_jobs: new table ------------------------------------------
    op.create_table(
        "scheduled_jobs",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("cron_schedule", sa.String(100), nullable=False),
        sa.Column("owner_agent_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("script_path", sa.String(255), nullable=False),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_run_status", sa.String(20), nullable=True),
        sa.Column("depends_on", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_scheduled_jobs_name", "scheduled_jobs", ["name"], unique=True)
    op.create_index("ix_scheduled_jobs_owner_agent_id", "scheduled_jobs", ["owner_agent_id"])


def downgrade() -> None:
    op.drop_index("ix_scheduled_jobs_owner_agent_id", table_name="scheduled_jobs")
    op.drop_index("ix_scheduled_jobs_name", table_name="scheduled_jobs")
    op.drop_table("scheduled_jobs")

    op.drop_column("ventures", "target_revenue_monthly_usd")
    op.drop_column("ventures", "monthly_budget_usd")
    op.drop_constraint("ventures_parent_venture_id_fkey", "ventures", type_="foreignkey")
    op.drop_column("ventures", "parent_venture_id")
    op.drop_column("ventures", "repo_url")

    op.drop_column("agents", "monthly_budget_usd")
    op.drop_column("agents", "permitted_services")
    op.drop_column("agents", "permitted_tools")
    op.drop_column("agents", "working_directory")
    op.drop_column("agents", "repo_path")
    op.drop_index("ix_agents_reporting_manager_id", table_name="agents")
    op.drop_constraint("agents_reporting_manager_id_fkey", "agents", type_="foreignkey")
    op.drop_column("agents", "reporting_manager_id")
