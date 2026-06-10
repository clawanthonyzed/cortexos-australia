"""Dashboard aggregate stats + venture health endpoints."""
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
from app.models.revenue_record import RevenueRecord
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.services.venture_health import compute_all_venture_health

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

    # Last month costs for growth %
    last_month_start = datetime(
        month_start.year if month_start.month > 1 else month_start.year - 1,
        month_start.month - 1 if month_start.month > 1 else 12,
        1, tzinfo=timezone.utc
    )
    costs_last_month = (
        await db.execute(
            select(func.coalesce(func.sum(CostRecord.cost_usd), 0.0)).where(
                (CostRecord.created_at >= last_month_start) & (CostRecord.created_at < month_start)
            )
        )
    ).scalar_one() or 0.001  # avoid div/0

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

    # Real revenue this month (AUD) from RevenueRecord
    revenue_mtd = (
        await db.execute(
            select(func.coalesce(func.sum(RevenueRecord.amount_aud), 0.0)).where(
                RevenueRecord.created_at >= month_start
            )
        )
    ).scalar_one()

    revenue_last_month = (
        await db.execute(
            select(func.coalesce(func.sum(RevenueRecord.amount_aud), 0.0)).where(
                (RevenueRecord.created_at >= last_month_start) & (RevenueRecord.created_at < month_start)
            )
        )
    ).scalar_one() or 0.001

    costs_growth = round((float(costs_mtd) / float(costs_last_month) - 1) * 100, 1)
    revenue_growth = round((float(revenue_mtd) / float(revenue_last_month) - 1) * 100, 1)

    return {
        "activeAgents": active_agents,
        "activeAgentsDelta": 0,
        "revenueThisMonthAud": round(float(revenue_mtd), 2),
        "revenueGrowthPercent": revenue_growth,
        "costsThisMonthUsd": float(costs_mtd),
        "costsGrowthPercent": costs_growth,
        "tasksCompletedToday": tasks_today,
        "tasksCompletedDelta": 0,
        "tokenUsageTodayM": round(float(tokens_today) / 1_000_000, 4),
        "tokenUsageDeltaPercent": 0.0,
        "systemHealthPercent": 100.0,
    }


@router.get("/venture-health", tags=["dashboard"])
async def venture_health(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.AGENT_READ)),
) -> dict[str, Any]:
    """
    Health score for each venture based on agent activity, task success rates,
    and cost efficiency. Score 0-100. Used for the empire health matrix.

    Agents are matched to ventures via `Agent.venture_id` (FK) — see
    SPEC-COS-04 / fixes #14.
    """
    ventures = await compute_all_venture_health(db)

    healthy = sum(1 for v in ventures if v["status"] == "healthy")
    warning = sum(1 for v in ventures if v["status"] == "warning")
    critical = sum(1 for v in ventures if v["status"] in ("critical", "inactive"))
    empire_score = round(sum(v["healthScore"] for v in ventures) / len(ventures)) if ventures else 0

    return {
        "empireHealthScore": empire_score,
        "summary": {"healthy": healthy, "warning": warning, "critical": critical},
        "ventures": ventures,
        "generatedAt": datetime.now(tz=timezone.utc).isoformat(),
    }
