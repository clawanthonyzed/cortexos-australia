"""Dashboard aggregate stats endpoint."""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import Permission, require_permission
from app.dependencies import get_db
from app.models.agent import Agent, AgentStatus
from app.models.cost_record import CostRecord
from app.models.task import Task, TaskStatus
from app.models.user import User

router = APIRouter()


def _month_start() -> datetime:
    today = date.today()
    return datetime(today.year, today.month, 1, tzinfo=timezone.utc)


def _today_start() -> datetime:
    return datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=timezone.utc)


@router.get("/stats", tags=["dashboard"])
async def dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.AGENT_READ)),
) -> dict[str, Any]:
    """KPI snapshot for the dashboard Command Center."""
    month_start = _month_start()
    today_start = _today_start()

    # Active agents
    active_agents = (
        await db.execute(
            select(func.count()).select_from(Agent).where(Agent.status == AgentStatus.RUNNING)
        )
    ).scalar_one()

    # Costs this month (USD) from cost_records
    costs_mtd = (
        await db.execute(
            select(func.coalesce(func.sum(CostRecord.cost_usd), 0.0)).where(
                CostRecord.created_at >= month_start
            )
        )
    ).scalar_one()

    # Token usage today (total_tokens)
    tokens_today = (
        await db.execute(
            select(func.coalesce(func.sum(CostRecord.total_tokens), 0)).where(
                CostRecord.created_at >= today_start
            )
        )
    ).scalar_one()

    # Tasks completed today
    tasks_today = (
        await db.execute(
            select(func.count()).select_from(Task).where(
                (Task.status == TaskStatus.COMPLETED) & (Task.completed_at >= today_start)
            )
        )
    ).scalar_one()

    return {
        "activeAgents": active_agents,
        "activeAgentsDelta": 0,
        "revenueThisMonthAud": 0.0,
        "revenueGrowthPercent": 0.0,
        "costsThisMonthUsd": float(costs_mtd),
        "costsGrowthPercent": 0.0,
        "tasksCompletedToday": tasks_today,
        "tasksCompletedDelta": 0,
        "tokenUsageTodayM": round(float(tokens_today) / 1_000_000, 4),
        "tokenUsageDeltaPercent": 0.0,
        "systemHealthPercent": 100.0,
    }
