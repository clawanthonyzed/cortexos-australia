"""Dashboard aggregate stats + venture health endpoints."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
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

# Venture registry — maps venture slug to display info
# In future this will be driven by a Venture DB table
_VENTURES = [
    {"slug": "bloom-and-bub", "name": "Bloom & Bub", "manager": "maren", "category": "digital_product"},
    {"slug": "cudan-studio", "name": "Cudan Studio", "manager": "cruz", "category": "service"},
    {"slug": "kdp-colouring-books", "name": "KDP Colouring Books", "manager": "atlas", "category": "digital_product"},
    {"slug": "mapdrop", "name": "MapDrop", "manager": "remy", "category": "digital_product"},
    {"slug": "lo-fi-engine", "name": "Lo-Fi Engine", "manager": "kai", "category": "content"},
    {"slug": "ambient-escapes", "name": "Ambient Escapes", "manager": "murray", "category": "content"},
    {"slug": "domain-flipping", "name": "Domain Flipping", "manager": "scout", "category": "arbitrage"},
    {"slug": "polymarket-tracker", "name": "Polymarket Tracker", "manager": "quant", "category": "fintech"},
    {"slug": "prediction-pulse", "name": "Prediction Pulse", "manager": "quant", "category": "fintech"},
    {"slug": "handwritten-book", "name": "Handwritten Book", "manager": "wren", "category": "digital_product"},
    {"slug": "affiliate-empire", "name": "Affiliate Empire", "manager": "harper", "category": "affiliate"},
    {"slug": "weekly-wonder", "name": "Weekly Wonder", "manager": "wonder", "category": "content"},
    {"slug": "meal-plan-cart", "name": "Meal Plan Cart", "manager": "bondi", "category": "digital_product"},
    {"slug": "scroll-and-stone", "name": "Scroll & Stone", "manager": "levi", "category": "digital_product"},
    {"slug": "agentic-os", "name": "CortexOS", "manager": "orbit", "category": "saas"},
    {"slug": "wantsyoutoknow", "name": "WantsYouToKnow", "manager": "ellis", "category": "content"},
    {"slug": "the-footnote", "name": "The Footnote", "manager": "callum", "category": "content"},
    {"slug": "sage-ai", "name": "Sage AI", "manager": "neve", "category": "saas"},
]


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


@router.get("/venture-health", tags=["dashboard"])
async def venture_health(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.AGENT_READ)),
) -> dict[str, Any]:
    """
    Health score for each venture based on agent activity, task success rates,
    and cost efficiency. Score 0-100. Used for the empire health matrix.
    """
    window = datetime.now(tz=timezone.utc) - timedelta(days=7)

    # Tasks per agent over 7 days
    task_rows = (await db.execute(
        select(Task.agent_id, Task.status, func.count(Task.id).label("cnt"))
        .where(Task.created_at >= window)
        .group_by(Task.agent_id, Task.status)
    )).all()

    # Build agent task map: {agent_id: {status: count}}
    agent_tasks: dict[str, dict[str, int]] = {}
    for row in task_rows:
        if not row.agent_id:
            continue
        aid = str(row.agent_id)
        if aid not in agent_tasks:
            agent_tasks[aid] = {}
        agent_tasks[aid][row.status] = row.cnt

    # Agent names
    agents = (await db.execute(select(Agent.id, Agent.name, Agent.status, Agent.last_run_at))).all()
    agent_map = {str(a.id): a for a in agents}

    ventures = []
    for v in _VENTURES:
        # Find agents for this venture by matching name prefix or manager field
        manager_slug = v["manager"]
        matching_agents = [
            a for aid, a in agent_map.items()
            if a.name.lower().startswith(manager_slug.lower())
        ]

        total_tasks = sum(
            sum(agent_tasks.get(str(a.id), {}).values())
            for a in matching_agents
        )
        completed = sum(
            agent_tasks.get(str(a.id), {}).get("completed", 0)
            for a in matching_agents
        )
        failed = sum(
            agent_tasks.get(str(a.id), {}).get("failed", 0)
            for a in matching_agents
        )

        # Health score components (0-100)
        # Activity: tasks in last 7d (cap at 20 for full score)
        activity_score = min(100, total_tasks * 5)
        # Success rate
        success_rate = (completed / total_tasks * 100) if total_tasks > 0 else 50
        # Recency: any agent run in last 24h?
        recent = any(
            a.last_run_at and (datetime.now(tz=timezone.utc) - a.last_run_at).total_seconds() < 86400
            for a in matching_agents
        )
        recency_score = 100 if recent else (50 if matching_agents else 0)

        health_score = round(
            activity_score * 0.3 + success_rate * 0.5 + recency_score * 0.2
        )

        status_label = (
            "healthy" if health_score >= 70
            else "warning" if health_score >= 40
            else "critical" if matching_agents
            else "inactive"
        )

        ventures.append({
            "slug": v["slug"],
            "name": v["name"],
            "manager": v["manager"],
            "category": v["category"],
            "healthScore": health_score,
            "status": status_label,
            "tasksLast7d": total_tasks,
            "successRate": round(success_rate, 1),
            "agentCount": len(matching_agents),
            "lastActivityAt": max(
                (a.last_run_at for a in matching_agents if a.last_run_at),
                default=None,
            ),
        })

    # Sort by health score descending
    ventures.sort(key=lambda x: x["healthScore"], reverse=True)

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
