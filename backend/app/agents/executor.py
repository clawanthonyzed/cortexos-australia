"""AgentExecutor — runs agents, updates DB state, records costs, broadcasts WS events."""
from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import AgentResult
from app.agents.registry import AgentRegistry
from app.models.agent import Agent as AgentModel, AgentStatus
from app.models.cost_record import CostRecord
from app.models.task import Task, TaskStatus

logger = structlog.get_logger(__name__)


def _broadcast(event_type: str, payload: dict) -> None:
    """Fire-and-forget WS broadcast — never blocks the executor."""
    try:
        from app.api.v1.ws_manager import manager as ws_manager
        asyncio.create_task(ws_manager.broadcast({"type": event_type, **payload}))
    except Exception:
        pass


class AgentExecutor:
    """
    Orchestrates agent execution:
    1. Loads the agent from DB
    2. Spawns the live BaseAgent instance
    3. Runs the task
    4. Updates Task and Agent DB records with results
    5. Broadcasts task/agent status changes via WebSocket
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def execute_task(self, task_id: uuid.UUID) -> AgentResult:
        """Execute a Task by its ID. Updates task status throughout execution."""
        task_result = await self.db.execute(select(Task).where(Task.id == task_id))
        task = task_result.scalar_one_or_none()
        if not task:
            raise ValueError(f"Task {task_id} not found")

        if not task.agent_id:
            raise ValueError(f"Task {task_id} has no assigned agent")

        # → running
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now(tz=timezone.utc)
        await self.db.flush()
        _broadcast("task.status_changed", {
            "taskId": str(task_id),
            "agentId": str(task.agent_id),
            "status": TaskStatus.RUNNING,
        })

        # Spawn agent
        agent = await AgentRegistry.spawn_from_db(self.db, task.agent_id)
        if not agent:
            task.status = TaskStatus.FAILED
            task.error_message = f"Agent {task.agent_id} not found in registry"
            await self.db.flush()
            _broadcast("task.status_changed", {
                "taskId": str(task_id),
                "status": TaskStatus.FAILED,
                "error": task.error_message,
            })
            return AgentResult(content="", success=False, error=task.error_message)

        # Broadcast agent → running
        _broadcast("agent.status_changed", {
            "agentId": str(task.agent_id),
            "status": AgentStatus.RUNNING,
        })

        try:
            input_data: dict = json.loads(task.input_data)
        except (json.JSONDecodeError, TypeError):
            input_data = {}

        task_prompt = input_data.get("prompt", task.description or task.title)
        context = input_data.get("context", {})

        try:
            result = await agent.run(task=task_prompt, context=context)
        except Exception as exc:
            logger.error("Agent execution error", task_id=str(task_id), error=str(exc))
            result = AgentResult(content="", success=False, error=str(exc))

        now = datetime.now(tz=timezone.utc)
        if result.success:
            task.status = TaskStatus.COMPLETED
            task.result_json = json.dumps({
                "content": result.content,
                "tokens_used": result.tokens_used,
                "cost_usd": result.cost_usd,
                "duration_seconds": result.duration_seconds,
                "iterations": result.iterations,
                "trace_id": result.trace_id,
            })
        else:
            task.retry_count += 1
            task.status = TaskStatus.RETRYING if task.retry_count < task.max_retries else TaskStatus.FAILED
            task.error_message = result.error

        task.completed_at = now
        await self.db.flush()

        _broadcast("task.status_changed", {
            "taskId": str(task_id),
            "agentId": str(task.agent_id),
            "status": task.status,
            "costUsd": result.cost_usd,
            "durationSeconds": result.duration_seconds,
        })

        await self._update_agent_metrics(task.agent_id, result)

        _broadcast("agent.status_changed", {
            "agentId": str(task.agent_id),
            "status": AgentStatus.IDLE,
            "lastRunAt": now.isoformat(),
        })

        return result

    async def execute_agent_directly(
        self,
        agent_id: uuid.UUID,
        task: str,
        context: dict | None = None,
        max_iterations: int = 10,
    ) -> AgentResult:
        """Run an agent directly without creating a Task record."""
        agent = await AgentRegistry.spawn_from_db(self.db, agent_id)
        if not agent:
            return AgentResult(content="", success=False, error=f"Agent {agent_id} not found")

        _broadcast("agent.status_changed", {"agentId": str(agent_id), "status": AgentStatus.RUNNING})
        result = await agent.run(task=task, context=context or {}, max_iterations=max_iterations)
        await self._update_agent_metrics(agent_id, result)
        _broadcast("agent.status_changed", {"agentId": str(agent_id), "status": AgentStatus.IDLE})
        return result

    async def _update_agent_metrics(self, agent_id: uuid.UUID, result: AgentResult) -> None:
        """Increment the agent's aggregated metrics in the database."""
        agent_result = await self.db.execute(select(AgentModel).where(AgentModel.id == agent_id))
        db_agent = agent_result.scalar_one_or_none()
        if not db_agent:
            return

        db_agent.total_tokens_used += result.tokens_used
        db_agent.total_cost_usd += result.cost_usd
        db_agent.last_run_at = datetime.now(tz=timezone.utc)
        db_agent.success_count += 1 if result.success else 0
        db_agent.error_count += 0 if result.success else 1
        db_agent.status = AgentStatus.IDLE
        await self.db.flush()

        _broadcast("agent.metrics_updated", {
            "agentId": str(agent_id),
            "totalCostUsd": db_agent.total_cost_usd,
            "successCount": db_agent.success_count,
            "errorCount": db_agent.error_count,
        })
