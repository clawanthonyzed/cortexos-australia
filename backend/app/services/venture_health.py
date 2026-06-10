"""Venture health scoring — shared by `/dashboard/venture-health` and
`/ventures/{id}/health` (SPEC-COS-04 / fixes #14).

Agents are matched to ventures via `Agent.venture_id` (FK), not the
previous `agent.name.startswith(manager_slug)` heuristic.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.models.task import Task
from app.models.venture import Venture

HEALTH_WINDOW_DAYS = 7
RECENCY_WINDOW_SECONDS = 86400


async def compute_all_venture_health(db: AsyncSession) -> list[dict[str, Any]]:
    """Health score for every venture in the registry, sorted best-first."""
    window = datetime.now(tz=timezone.utc) - timedelta(days=HEALTH_WINDOW_DAYS)

    task_rows = (await db.execute(
        select(Task.agent_id, Task.status, func.count(Task.id).label("cnt"))
        .where(Task.created_at >= window)
        .group_by(Task.agent_id, Task.status)
    )).all()
    agent_tasks = _group_agent_tasks(task_rows)

    agents = (await db.execute(select(Agent.id, Agent.venture_id, Agent.last_run_at))).all()
    ventures = (await db.execute(select(Venture).order_by(Venture.name))).scalars().all()

    results = [
        _score_venture(v, [a for a in agents if a.venture_id == v.id], agent_tasks)
        for v in ventures
    ]
    results.sort(key=lambda x: x["healthScore"], reverse=True)
    return results


async def compute_venture_health(db: AsyncSession, venture: Venture) -> dict[str, Any]:
    """Health score for a single venture."""
    window = datetime.now(tz=timezone.utc) - timedelta(days=HEALTH_WINDOW_DAYS)

    agents = (await db.execute(
        select(Agent.id, Agent.venture_id, Agent.last_run_at).where(Agent.venture_id == venture.id)
    )).all()

    agent_tasks: dict[str, dict[str, int]] = {}
    if agents:
        agent_ids = [a.id for a in agents]
        task_rows = (await db.execute(
            select(Task.agent_id, Task.status, func.count(Task.id).label("cnt"))
            .where(Task.created_at >= window, Task.agent_id.in_(agent_ids))
            .group_by(Task.agent_id, Task.status)
        )).all()
        agent_tasks = _group_agent_tasks(task_rows)

    return _score_venture(venture, agents, agent_tasks)


def _group_agent_tasks(task_rows: Sequence[Any]) -> dict[str, dict[str, int]]:
    agent_tasks: dict[str, dict[str, int]] = {}
    for row in task_rows:
        if not row.agent_id:
            continue
        agent_tasks.setdefault(str(row.agent_id), {})[row.status] = row.cnt
    return agent_tasks


def _score_venture(venture: Venture, matching_agents: Sequence[Any], agent_tasks: dict[str, dict[str, int]]) -> dict[str, Any]:
    total_tasks = sum(sum(agent_tasks.get(str(a.id), {}).values()) for a in matching_agents)
    completed = sum(agent_tasks.get(str(a.id), {}).get("completed", 0) for a in matching_agents)

    activity_score = min(100, total_tasks * 5)
    success_rate = (completed / total_tasks * 100) if total_tasks > 0 else 50
    recent = any(
        a.last_run_at and (datetime.now(tz=timezone.utc) - a.last_run_at).total_seconds() < RECENCY_WINDOW_SECONDS
        for a in matching_agents
    )
    recency_score = 100 if recent else (50 if matching_agents else 0)

    health_score = round(activity_score * 0.3 + success_rate * 0.5 + recency_score * 0.2)

    status_label = (
        "healthy" if health_score >= 70
        else "warning" if health_score >= 40
        else "critical" if matching_agents
        else "inactive"
    )

    return {
        "slug": venture.slug,
        "name": venture.name,
        "manager": venture.manager_name,
        "category": venture.category,
        "healthScore": health_score,
        "status": status_label,
        "tasksLast7d": total_tasks,
        "successRate": round(success_rate, 1),
        "agentCount": len(matching_agents),
        "lastActivityAt": max(
            (a.last_run_at for a in matching_agents if a.last_run_at),
            default=None,
        ),
    }
