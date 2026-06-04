"""Agent CRUD + run/stop/pause/clone endpoints."""
from __future__ import annotations

import json
import uuid
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.executor import AgentExecutor
from app.agents.registry import AgentRegistry
from app.auth.rbac import Permission, require_permission
from app.dependencies import get_db, paginate
from app.models.agent import Agent, AgentStatus
from app.models.user import User
from app.schemas.agent import (
    AgentCloneRequest,
    AgentCreate,
    AgentRead,
    AgentReadBrief,
    AgentRunRequest,
    AgentRunResult,
    AgentUpdate,
)

logger = structlog.get_logger(__name__)
router = APIRouter()


def _error(msg: str, detail: Any = None) -> dict[str, Any]:
    return {"error": msg, "detail": detail or {}}


@router.get("", response_model=dict[str, Any], tags=["agents"])
async def list_agents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.AGENT_READ)),
    pagination: dict = Depends(paginate),
    agent_type: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
) -> dict[str, Any]:
    """List all agents with pagination."""
    stmt = select(Agent)
    if agent_type:
        stmt = stmt.where(Agent.agent_type == agent_type)
    if status_filter:
        stmt = stmt.where(Agent.status == status_filter)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.offset(pagination["offset"]).limit(pagination["limit"]).order_by(Agent.created_at.desc())
    result = await db.execute(stmt)
    agents = result.scalars().all()

    return {
        "items": [AgentReadBrief.model_validate(a) for a in agents],
        "total": total,
        "page": pagination["page"],
        "page_size": pagination["page_size"],
    }


@router.post("", response_model=AgentRead, status_code=status.HTTP_201_CREATED, tags=["agents"])
async def create_agent(
    payload: AgentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.AGENT_CREATE)),
) -> AgentRead:
    """Create a new agent."""
    # Check name uniqueness
    existing = await db.execute(select(Agent).where(Agent.name == payload.name))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_error("Agent name already in use"),
        )

    agent = Agent(
        name=payload.name,
        purpose=payload.purpose,
        description=payload.description,
        model_provider=payload.model_provider,
        model_name=payload.model_name,
        temperature=payload.temperature,
        max_tokens=payload.max_tokens,
        config_json=json.dumps(payload.config_json),
        system_prompt=payload.system_prompt,
        agent_type=payload.agent_type,
        tags=json.dumps(payload.tags),
    )
    db.add(agent)
    await db.flush()
    await db.refresh(agent)
    return AgentRead.model_validate(agent)


@router.get("/{agent_id}", response_model=AgentRead, tags=["agents"])
async def get_agent(
    agent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.AGENT_READ)),
) -> AgentRead:
    """Get a single agent by ID."""
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=_error("Agent not found"))
    return AgentRead.model_validate(agent)


@router.patch("/{agent_id}", response_model=AgentRead, tags=["agents"])
async def update_agent(
    agent_id: uuid.UUID,
    payload: AgentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.AGENT_UPDATE)),
) -> AgentRead:
    """Partially update an agent."""
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=_error("Agent not found"))

    update_data = payload.model_dump(exclude_none=True)
    for field, value in update_data.items():
        if field == "config_json":
            setattr(agent, field, json.dumps(value))
        elif field == "tags":
            setattr(agent, field, json.dumps(value))
        else:
            setattr(agent, field, value)

    await db.flush()
    await db.refresh(agent)
    return AgentRead.model_validate(agent)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None, tags=["agents"])
async def delete_agent(
    agent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.AGENT_DELETE)),
) -> None:
    """Delete an agent."""
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=_error("Agent not found"))
    await db.delete(agent)


@router.post("/{agent_id}/run", response_model=AgentRunResult, tags=["agents"])
async def run_agent(
    agent_id: uuid.UUID,
    payload: AgentRunRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.AGENT_RUN)),
) -> AgentRunResult:
    """Run an agent on a task (sync or async via Celery)."""
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=_error("Agent not found"))

    if agent.status == AgentStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_error("Agent is already running"),
        )

    if payload.async_run:
        # Dispatch to Celery — create a Task record first
        from app.models.task import Task, TaskStatus
        task = Task(
            title=f"Run: {payload.task[:80]}",
            description=payload.task,
            input_data=json.dumps({"prompt": payload.task, "context": payload.context}),
            agent_id=agent_id,
            status=TaskStatus.QUEUED,
        )
        db.add(task)
        await db.flush()

        from app.tasks.agent_tasks import run_agent_task
        celery_result = run_agent_task.delay(str(task.id))
        task.celery_task_id = celery_result.id
        await db.flush()

        return AgentRunResult(
            agent_id=agent_id,
            task_id=task.id,
            celery_task_id=celery_result.id,
            status="queued",
        )

    # Synchronous execution
    executor = AgentExecutor(db)
    result = await executor.execute_agent_directly(
        agent_id=agent_id,
        task=payload.task,
        context=payload.context,
        max_iterations=payload.max_iterations,
    )

    return AgentRunResult(
        agent_id=agent_id,
        status="completed" if result.success else "failed",
        result=result.content,
        error=result.error,
        tokens_used=result.tokens_used,
        cost_usd=result.cost_usd,
        duration_seconds=result.duration_seconds,
    )


@router.post("/{agent_id}/stop", response_model=AgentRead, tags=["agents"])
async def stop_agent(
    agent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.AGENT_RUN)),
) -> AgentRead:
    """Set agent status to idle (stops further task pickup)."""
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=_error("Agent not found"))
    agent.status = AgentStatus.IDLE
    await db.flush()
    await db.refresh(agent)
    return AgentRead.model_validate(agent)


@router.post("/{agent_id}/pause", response_model=AgentRead, tags=["agents"])
async def pause_agent(
    agent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.AGENT_RUN)),
) -> AgentRead:
    """Pause an agent (no new tasks dispatched)."""
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=_error("Agent not found"))
    agent.status = AgentStatus.PAUSED
    await db.flush()
    await db.refresh(agent)
    return AgentRead.model_validate(agent)


@router.post("/{agent_id}/clone", response_model=AgentRead, status_code=status.HTTP_201_CREATED, tags=["agents"])
async def clone_agent(
    agent_id: uuid.UUID,
    payload: AgentCloneRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.AGENT_CREATE)),
) -> AgentRead:
    """Clone an agent with a new name."""
    source = await db.get(Agent, agent_id)
    if not source:
        raise HTTPException(status_code=404, detail=_error("Agent not found"))

    cloned = Agent(
        name=payload.new_name,
        purpose=payload.new_purpose or source.purpose,
        description=source.description,
        model_provider=source.model_provider,
        model_name=source.model_name,
        temperature=source.temperature,
        max_tokens=source.max_tokens,
        config_json=source.config_json,
        system_prompt=source.system_prompt,
        agent_type=source.agent_type,
        tags=source.tags,
    )
    db.add(cloned)
    await db.flush()
    await db.refresh(cloned)
    return AgentRead.model_validate(cloned)


@router.get("/types/list", tags=["agents"])
async def list_agent_types(
    current_user: User = Depends(require_permission(Permission.AGENT_READ)),
) -> dict[str, Any]:
    """List all registered agent types."""
    return {"types": AgentRegistry.list_types()}
