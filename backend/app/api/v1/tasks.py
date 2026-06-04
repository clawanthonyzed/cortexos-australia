"""Task CRUD + execute/cancel/retry endpoints."""
from __future__ import annotations

import json
import uuid
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import Permission, require_permission
from app.dependencies import get_db, paginate
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.schemas.task import (
    TaskCreate,
    TaskExecuteRequest,
    TaskRead,
    TaskReadBrief,
    TaskRetryRequest,
    TaskUpdate,
)

logger = structlog.get_logger(__name__)
router = APIRouter()


def _error(msg: str, detail: Any = None) -> dict[str, Any]:
    return {"error": msg, "detail": detail or {}}


@router.get("", response_model=dict[str, Any], tags=["tasks"])
async def list_tasks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TASK_READ)),
    pagination: dict = Depends(paginate),
    status_filter: str | None = Query(None, alias="status"),
    agent_id: uuid.UUID | None = Query(None),
    priority_min: int | None = Query(None),
) -> dict[str, Any]:
    """List tasks with pagination and filtering."""
    stmt = select(Task)
    if status_filter:
        stmt = stmt.where(Task.status == status_filter)
    if agent_id:
        stmt = stmt.where(Task.agent_id == agent_id)
    if priority_min:
        stmt = stmt.where(Task.priority >= priority_min)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.offset(pagination["offset"]).limit(pagination["limit"]).order_by(
        Task.priority.desc(), Task.created_at.desc()
    )
    result = await db.execute(stmt)
    tasks = result.scalars().all()

    return {
        "items": [TaskReadBrief.model_validate(t) for t in tasks],
        "total": total,
        "page": pagination["page"],
        "page_size": pagination["page_size"],
    }


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED, tags=["tasks"])
async def create_task(
    payload: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TASK_CREATE)),
) -> TaskRead:
    """Create a new task."""
    task = Task(
        title=payload.title,
        description=payload.description,
        input_data=json.dumps(payload.input_data),
        agent_id=payload.agent_id,
        priority=payload.priority,
        scheduled_at=payload.scheduled_at,
        max_retries=payload.max_retries,
        parent_task_id=payload.parent_task_id,
        workflow_id=payload.workflow_id,
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return TaskRead.model_validate(task)


@router.get("/{task_id}", response_model=TaskRead, tags=["tasks"])
async def get_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TASK_READ)),
) -> TaskRead:
    """Get a single task."""
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=_error("Task not found"))
    return TaskRead.model_validate(task)


@router.patch("/{task_id}", response_model=TaskRead, tags=["tasks"])
async def update_task(
    task_id: uuid.UUID,
    payload: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TASK_UPDATE)),
) -> TaskRead:
    """Update a task (only pending/queued tasks can be edited)."""
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=_error("Task not found"))

    if task.status in (TaskStatus.RUNNING, TaskStatus.COMPLETED):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_error(f"Cannot update a task in {task.status} state"),
        )

    update_data = payload.model_dump(exclude_none=True)
    for field, value in update_data.items():
        if field == "input_data":
            setattr(task, field, json.dumps(value))
        else:
            setattr(task, field, value)

    await db.flush()
    await db.refresh(task)
    return TaskRead.model_validate(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None, tags=["tasks"])
async def delete_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TASK_DELETE)),
) -> None:
    """Delete a task."""
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=_error("Task not found"))
    if task.status == TaskStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_error("Cannot delete a running task — cancel it first"),
        )
    await db.delete(task)


@router.post("/{task_id}/execute", response_model=dict[str, Any], tags=["tasks"])
async def execute_task(
    task_id: uuid.UUID,
    payload: TaskExecuteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TASK_CREATE)),
) -> dict[str, Any]:
    """Trigger execution of an existing pending task."""
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=_error("Task not found"))

    if task.status == TaskStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_error("Task is already running"),
        )

    if payload.override_agent_id:
        task.agent_id = payload.override_agent_id

    if payload.async_run:
        from app.tasks.agent_tasks import run_agent_task
        from app.models.task import TaskStatus
        task.status = TaskStatus.QUEUED
        await db.flush()
        celery_result = run_agent_task.delay(str(task_id))
        task.celery_task_id = celery_result.id
        await db.flush()
        return {"task_id": str(task_id), "celery_task_id": celery_result.id, "status": "queued"}

    from app.agents.executor import AgentExecutor
    executor = AgentExecutor(db)
    result = await executor.execute_task(task_id)
    return {
        "task_id": str(task_id),
        "status": "completed" if result.success else "failed",
        "result": result.content[:500] if result.content else "",
        "error": result.error,
        "cost_usd": result.cost_usd,
    }


@router.post("/{task_id}/cancel", response_model=TaskRead, tags=["tasks"])
async def cancel_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TASK_CANCEL)),
) -> TaskRead:
    """Cancel a pending or queued task."""
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=_error("Task not found"))

    if task.status not in (TaskStatus.PENDING, TaskStatus.QUEUED, TaskStatus.RETRYING):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_error(f"Cannot cancel task in {task.status} state"),
        )

    # Revoke Celery task if dispatched
    if task.celery_task_id:
        try:
            from app.tasks.celery_app import celery_app
            celery_app.control.revoke(task.celery_task_id, terminate=True)
        except Exception:
            pass

    task.status = TaskStatus.CANCELLED
    await db.flush()
    await db.refresh(task)
    return TaskRead.model_validate(task)


@router.post("/{task_id}/retry", response_model=TaskRead, tags=["tasks"])
async def retry_task(
    task_id: uuid.UUID,
    payload: TaskRetryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TASK_CREATE)),
) -> TaskRead:
    """Retry a failed task."""
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=_error("Task not found"))

    if task.status not in (TaskStatus.FAILED, TaskStatus.CANCELLED):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_error(f"Cannot retry task in {task.status} state"),
        )

    if payload.reset_input:
        task.input_data = json.dumps(payload.reset_input)

    task.status = TaskStatus.QUEUED
    task.error_message = None
    task.error_traceback = None
    await db.flush()

    from app.tasks.agent_tasks import run_agent_task
    celery_result = run_agent_task.delay(str(task_id))
    task.celery_task_id = celery_result.id
    await db.flush()
    await db.refresh(task)
    return TaskRead.model_validate(task)
