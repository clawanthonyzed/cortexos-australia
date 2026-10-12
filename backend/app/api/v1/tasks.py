"""Task CRUD + execute/cancel/retry/stream endpoints."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.executor import AgentExecutor
from app.auth.rbac import Permission, require_permission
from app.dependencies import get_db, paginate
from app.models.agent import Agent
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


def _deliverable(task: Task) -> str | None:
    """Link to the finished work, when a run recorded one in result_json."""
    try:
        data = json.loads(task.result_json or "null")
    except ValueError:
        return None
    return data.get("deliverable") if isinstance(data, dict) else None


def _task_read(task: Task) -> TaskRead:
    """TaskRead from a Task row. input_data/result_json are TEXT columns holding JSON, so
    model_validate(task) failed for every single-task response (found 2026-10-10)."""
    d = {a.key: getattr(task, a.key) for a in Task.__mapper__.column_attrs}
    for field, empty in (("input_data", {}), ("result_json", None)):
        v = d.get(field)
        if isinstance(v, str):
            try:
                d[field] = json.loads(v) if v.strip() else empty
            except ValueError:
                d[field] = empty
    return TaskRead.model_validate(d)


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

    # The board shows who owns each task; resolve agent names in one query.
    agent_ids = {t.agent_id for t in tasks if t.agent_id}
    names = dict((await db.execute(select(Agent.id, Agent.name).where(Agent.id.in_(agent_ids)))).all()) if agent_ids else {}

    return {
        "items": [{**TaskReadBrief.model_validate(t).model_dump(mode="json"), "agent_name": names.get(t.agent_id),
                   "deliverable": _deliverable(t)} for t in tasks],
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
    return _task_read(task)


@router.get("/stats", response_model=dict[str, Any], tags=["tasks"])
async def task_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TASK_READ)),
) -> dict[str, Any]:
    """Queue statistics for dashboard widgets."""
    from datetime import date, timezone
    today_start = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=timezone.utc)

    async def count(where_clause) -> int:
        result = await db.execute(select(func.count()).select_from(Task).where(where_clause))
        return result.scalar_one()

    queued = await count(Task.status == TaskStatus.QUEUED)
    running = await count(Task.status == TaskStatus.RUNNING)
    completed_today = await count(
        (Task.status == TaskStatus.COMPLETED) & (Task.completed_at >= today_start)
    )
    failed_today = await count(
        (Task.status == TaskStatus.FAILED) & (Task.completed_at >= today_start)
    )

    # Average duration of tasks completed today
    dur_result = await db.execute(
        select(Task.started_at, Task.completed_at).where(
            (Task.status == TaskStatus.COMPLETED)
            & (Task.completed_at >= today_start)
            & (Task.started_at.is_not(None))
        )
    )
    rows = dur_result.all()
    avg_duration_ms = 0.0
    if rows:
        durations = [
            (r.completed_at - r.started_at).total_seconds() * 1000
            for r in rows
            if r.completed_at and r.started_at
        ]
        avg_duration_ms = sum(durations) / len(durations) if durations else 0.0

    return {
        "queued": queued,
        "running": running,
        "completedToday": completed_today,
        "failedToday": failed_today,
        "avgDurationMs": round(avg_duration_ms, 2),
        "totalCostToday": 0.0,
    }


THOUGHTS_ROOT = Path("/opt/openclaw/second-brain/inbox")


@router.get("/{task_id}/deliverable", response_model=dict[str, Any], tags=["tasks"])
async def get_task_deliverable(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TASK_READ)),
) -> dict[str, Any]:
    """The finished work for a task (2026-10-12). Agent runs record a GitHub link to the draft in
    result_json; the same file is in the read-only Second Brain mount, so return its Deliverable
    section as text for the task drawer. Only files inside the vault inbox are ever read."""
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=_error("Task not found"))
    url = _deliverable(task)
    if not url:
        raise HTTPException(status_code=404, detail=_error("No deliverable recorded for this task"))
    name = url.rstrip("/").rsplit("/", 1)[-1]
    candidates = [THOUGHTS_ROOT / "thoughts" / name, THOUGHTS_ROOT / name]
    path = next((p for p in candidates if p.resolve().parent in (THOUGHTS_ROOT.resolve(), (THOUGHTS_ROOT / "thoughts").resolve()) and p.is_file()), None)
    if path is None:
        return {"url": url, "text": None, "model": None, "note": "Draft file not found on the server; open the link."}
    raw = path.read_text(errors="replace")
    model = None
    for line in raw.splitlines()[:15]:
        if line.startswith("| Model |"):
            model = line.split("|")[2].strip()
    body = raw.split("## Deliverable", 1)[1] if "## Deliverable" in raw else raw
    body = body.split("\n## Next step for Anthony", 1)[0].strip()
    return {"url": url, "text": body, "model": model}


@router.post("/{task_id}/status", response_model=TaskRead, tags=["tasks"])
async def set_task_board_status(
    task_id: uuid.UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TASK_UPDATE)),
) -> TaskRead:
    """Tick a task done (or reopen it) from the Tasks board. Never touches a running task."""
    from datetime import timezone
    new_status = str(payload.get("status", "")).lower()
    if new_status not in (TaskStatus.COMPLETED, TaskStatus.PENDING, TaskStatus.CANCELLED):
        raise HTTPException(status_code=422, detail=_error("status must be 'completed', 'pending' or 'cancelled'"))
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=_error("Task not found"))
    if task.status == TaskStatus.RUNNING:
        raise HTTPException(status_code=409, detail=_error("Task is running; cancel it first"))
    task.status = new_status
    task.completed_at = datetime.now(timezone.utc) if new_status == TaskStatus.COMPLETED else None
    await db.flush()
    await db.refresh(task)
    return _task_read(task)


@router.post("/{task_id}/comments", response_model=TaskRead, tags=["tasks"])
async def add_task_comment(
    task_id: uuid.UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TASK_UPDATE)),
) -> TaskRead:
    """Add a note to a task. Stored in the task's input_data under "comments"."""
    from datetime import timezone
    text = str(payload.get("text", "")).strip()
    if not text:
        raise HTTPException(status_code=422, detail=_error("Comment text is required"))
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=_error("Task not found"))
    try:
        data = json.loads(task.input_data or "{}")
        data = data if isinstance(data, dict) else {}
    except ValueError:
        data = {}
    data.setdefault("comments", []).append({
        "text": text[:4000],
        "author": getattr(current_user, "username", None) or getattr(current_user, "email", None) or "anthony",
        "at": datetime.now(timezone.utc).isoformat(),
    })
    task.input_data = json.dumps(data)
    await db.flush()
    await db.refresh(task)
    return _task_read(task)


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
    return _task_read(task)


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
    return _task_read(task)


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
    return _task_read(task)


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
    return _task_read(task)


@router.get("/{task_id}/stream", tags=["tasks"])
async def stream_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TASK_CREATE)),
) -> StreamingResponse:
    """
    Stream task execution as Server-Sent Events.

    Registers a queue BEFORE starting execution so no events are lost.
    Events: task.started, agent.thinking, agent.token, task.completed, task.error.

    Connect with EventSource or fetch+ReadableStream.
    The stream closes automatically when task.completed or task.error is emitted.
    """
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=_error("Task not found"))

    if task.status == TaskStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_error("Task is already running — connect to its existing stream via WS"),
        )

    if task.status == TaskStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_error("Task already completed"),
        )

    if not task.agent_id:
        raise HTTPException(status_code=422, detail=_error("Task has no assigned agent"))

    # Register queue BEFORE spawning execution so we capture every event
    queue = AgentExecutor.register_stream(task_id)
    executor = AgentExecutor(db)

    # Fire execution as a background coroutine — do not await here
    asyncio.create_task(executor.execute_task(task_id))

    async def event_generator() -> AsyncGenerator[str, None]:
        terminal_types = {"task.completed", "task.error"}
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=120.0)
                except asyncio.TimeoutError:
                    # Keepalive comment to prevent nginx/proxy timeout
                    yield ": keepalive\n\n"
                    continue

                event_type = event.get("type") or event.get("event", "message")
                yield f"event: {event_type}\ndata: {json.dumps(event)}\n\n"

                if event_type in terminal_types:
                    break
        finally:
            AgentExecutor.unregister_stream(task_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
