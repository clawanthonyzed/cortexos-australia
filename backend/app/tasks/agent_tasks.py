"""Celery tasks for agent and workflow execution."""
from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Any

import structlog

from app.tasks.celery_app import celery_app

logger = structlog.get_logger(__name__)


def _run_async(coro: Any) -> Any:
    """Run an async coroutine from a sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    bind=True,
    name="app.tasks.agent_tasks.run_agent_task",
    max_retries=3,
    default_retry_delay=30,
)
def run_agent_task(
    self: Any,
    task_id: str,
) -> dict[str, Any]:
    """
    Celery task: execute a Task by its UUID.
    Updates task status in DB throughout.
    """
    logger.info("Celery agent task started", task_id=task_id)

    async def _execute() -> dict[str, Any]:
        from app.database import AsyncSessionLocal
        from app.agents.executor import AgentExecutor

        async with AsyncSessionLocal() as db:
            executor = AgentExecutor(db)
            result = await executor.execute_task(uuid.UUID(task_id))
            await db.commit()
            return {
                "success": result.success,
                "content": result.content[:1000] if result.content else "",
                "tokens_used": result.tokens_used,
                "cost_usd": result.cost_usd,
                "duration_seconds": result.duration_seconds,
                "error": result.error,
            }

    try:
        return _run_async(_execute())
    except Exception as exc:
        logger.error("Celery agent task failed", task_id=task_id, error=str(exc))
        try:
            raise self.retry(exc=exc, countdown=60)
        except self.MaxRetriesExceededError:
            return {"success": False, "error": str(exc)}


@celery_app.task(
    bind=True,
    name="app.tasks.agent_tasks.run_workflow_task",
    max_retries=2,
    default_retry_delay=60,
)
def run_workflow_task(
    self: Any,
    workflow_id: str,
    input_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Celery task: execute a Workflow by its UUID."""
    logger.info("Celery workflow task started", workflow_id=workflow_id)

    async def _execute() -> dict[str, Any]:
        from app.database import AsyncSessionLocal
        from app.workflows.engine import WorkflowEngine

        async with AsyncSessionLocal() as db:
            engine = WorkflowEngine(db)
            final_state = await engine.execute(
                workflow_id=uuid.UUID(workflow_id),
                input_data=input_data or {},
            )
            await db.commit()
            return {
                "success": not bool(final_state.get("error")),
                "run_id": final_state.get("run_id"),
                "completed_nodes": final_state.get("completed_nodes", []),
                "requires_approval": final_state.get("requires_approval", False),
                "error": final_state.get("error"),
            }

    try:
        return _run_async(_execute())
    except Exception as exc:
        logger.error("Celery workflow task failed", workflow_id=workflow_id, error=str(exc))
        try:
            raise self.retry(exc=exc, countdown=120)
        except self.MaxRetriesExceededError:
            return {"success": False, "error": str(exc)}


@celery_app.task(name="app.tasks.agent_tasks.cleanup_stale_tasks")
def cleanup_stale_tasks() -> dict[str, Any]:
    """Periodic task: mark tasks that have been running too long as failed."""
    async def _cleanup() -> dict[str, Any]:
        from app.database import AsyncSessionLocal
        from app.models.task import Task, TaskStatus
        from sqlalchemy import select, update

        cutoff = datetime.now(tz=timezone.utc).replace(
            hour=datetime.now(tz=timezone.utc).hour - 2
        )

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Task).where(
                    Task.status == TaskStatus.RUNNING,
                    Task.started_at < cutoff,
                )
            )
            stale_tasks = result.scalars().all()
            count = 0
            for task in stale_tasks:
                task.status = TaskStatus.FAILED
                task.error_message = "Task timed out after 2 hours"
                count += 1
            await db.commit()
            return {"cleaned_up": count}

    return _run_async(_cleanup())
