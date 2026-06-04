"""Initial schema — all tables with pgvector extension.

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-02
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Extensions ──────────────────────────────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # ── Roles ────────────────────────────────────────────────────────────────
    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(50), nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("permissions", sa.Text, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("ix_roles_name", "roles", ["name"])

    # ── Users ─────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("username", sa.String(100), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_verified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("refresh_token_hash", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_username", "users", ["username"])

    # ── User Roles ─────────────────────────────────────────────────────────────
    op.create_table(
        "user_roles",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_role"),
    )

    # ── Agents ─────────────────────────────────────────────────────────────────
    op.create_table(
        "agents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("purpose", sa.Text, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("model_provider", sa.String(50), nullable=False, server_default="claude"),
        sa.Column("model_name", sa.String(100), nullable=False, server_default="claude-sonnet-4-6"),
        sa.Column("temperature", sa.Float, nullable=False, server_default="0.7"),
        sa.Column("max_tokens", sa.Integer, nullable=False, server_default="4096"),
        sa.Column("config_json", sa.Text, nullable=False, server_default="{}"),
        sa.Column("system_prompt", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="idle"),
        sa.Column("total_tokens_used", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_cost_usd", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("success_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("agent_type", sa.String(50), nullable=False, server_default="custom"),
        sa.Column("tags", sa.Text, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_agents_name", "agents", ["name"])
    op.create_index("ix_agents_status", "agents", ["status"])
    op.create_index("ix_agents_agent_type", "agents", ["agent_type"])

    # ── Workflows ─────────────────────────────────────────────────────────────
    op.create_table(
        "workflows",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("graph_json", sa.Text, nullable=False, server_default="{}"),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("trigger_type", sa.String(20), nullable=False, server_default="manual"),
        sa.Column("cron_expression", sa.String(100), nullable=True),
        sa.Column("config_json", sa.Text, nullable=False, server_default="{}"),
        sa.Column("run_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("success_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("failure_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_workflows_name", "workflows", ["name"])
    op.create_index("ix_workflows_status", "workflows", ["status"])

    # ── Workflow Steps ─────────────────────────────────────────────────────────
    op.create_table(
        "workflow_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("step_type", sa.String(50), nullable=False, server_default="agent_node"),
        sa.Column("config_json", sa.Text, nullable=False, server_default="{}"),
        sa.Column("order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("next_steps_json", sa.Text, nullable=False, server_default="[]"),
        sa.Column("node_id", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_workflow_steps_workflow_id", "workflow_steps", ["workflow_id"])

    # ── Tasks ─────────────────────────────────────────────────────────────────
    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("input_data", sa.Text, nullable=False, server_default="{}"),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("priority", sa.Integer, nullable=False, server_default="5"),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result_json", sa.Text, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("error_traceback", sa.Text, nullable=True),
        sa.Column("retry_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer, nullable=False, server_default="3"),
        sa.Column("celery_task_id", sa.String(255), nullable=True),
        sa.Column("parent_task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflows.id", ondelete="SET NULL"), nullable=True),
        sa.Column("workflow_step_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflow_steps.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_tasks_title", "tasks", ["title"])
    op.create_index("ix_tasks_status", "tasks", ["status"])
    op.create_index("ix_tasks_agent_id", "tasks", ["agent_id"])
    op.create_index("ix_tasks_parent_task_id", "tasks", ["parent_task_id"])
    op.create_index("ix_tasks_workflow_id", "tasks", ["workflow_id"])

    # ── Memory Items ───────────────────────────────────────────────────────────
    op.create_table(
        "memory_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("memory_type", sa.String(20), nullable=False, server_default="short_term"),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("tags", sa.Text, nullable=False, server_default="[]"),
        sa.Column("embedding_text", sa.Text, nullable=True),
        sa.Column("embedding_model", sa.String(100), nullable=True),
        sa.Column("embedding_dims", sa.Integer, nullable=True),
        sa.Column("importance_score", sa.Float, nullable=False, server_default="0.5"),
        sa.Column("access_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("source_task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_memory_items_agent_id", "memory_items", ["agent_id"])
    op.create_index("ix_memory_items_user_id", "memory_items", ["user_id"])
    op.create_index("ix_memory_items_memory_type", "memory_items", ["memory_type"])
    op.create_index("ix_memory_items_category", "memory_items", ["category"])
    op.create_index("ix_memory_items_external_id", "memory_items", ["external_id"])

    # ── Products ───────────────────────────────────────────────────────────────
    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("short_description", sa.Text, nullable=True),
        sa.Column("product_type", sa.String(50), nullable=False, server_default="digital_download"),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("tags", sa.Text, nullable=False, server_default="[]"),
        sa.Column("price_aud", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("original_price_aud", sa.Float, nullable=True),
        sa.Column("is_free", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("is_featured", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("listings_json", sa.Text, nullable=False, server_default="{}"),
        sa.Column("assets_json", sa.Text, nullable=False, server_default="[]"),
        sa.Column("cover_image_url", sa.String(1000), nullable=True),
        sa.Column("total_sales", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_revenue_aud", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("view_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("seo_title", sa.String(255), nullable=True),
        sa.Column("seo_description", sa.Text, nullable=True),
        sa.Column("seo_keywords", sa.Text, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_products_name", "products", ["name"])
    op.create_index("ix_products_slug", "products", ["slug"])
    op.create_index("ix_products_status", "products", ["status"])
    op.create_index("ix_products_category", "products", ["category"])

    # ── Cost Records ───────────────────────────────────────────────────────────
    op.create_table(
        "cost_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflows.id", ondelete="SET NULL"), nullable=True),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("prompt_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("completion_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("cache_creation_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("cache_read_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("trace_id", sa.String(255), nullable=True),
        sa.Column("label", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_cost_records_agent_id", "cost_records", ["agent_id"])
    op.create_index("ix_cost_records_task_id", "cost_records", ["task_id"])
    op.create_index("ix_cost_records_provider", "cost_records", ["provider"])
    op.create_index("ix_cost_records_model", "cost_records", ["model"])
    op.create_index("ix_cost_records_trace_id", "cost_records", ["trace_id"])

    # ── Audit Logs ─────────────────────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("resource_id", sa.String(255), nullable=True),
        sa.Column("method", sa.String(10), nullable=True),
        sa.Column("path", sa.String(500), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("status_code", sa.Integer, nullable=True),
        sa.Column("success", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("before_json", sa.Text, nullable=True),
        sa.Column("after_json", sa.Text, nullable=True),
        sa.Column("metadata_json", sa.Text, nullable=False, server_default="{}"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_resource_type", "audit_logs", ["resource_type"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("cost_records")
    op.drop_table("products")
    op.drop_table("memory_items")
    op.drop_table("tasks")
    op.drop_table("workflow_steps")
    op.drop_table("workflows")
    op.drop_table("agents")
    op.drop_table("user_roles")
    op.drop_table("users")
    op.drop_table("roles")
