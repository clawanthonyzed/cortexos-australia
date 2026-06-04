"""AgentExecutor — runs agents, updates DB state, records costs."""
from __future__ import annotations

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


class AgentExecutor:
    """
    Orchestrates agent execution:
    1. Loads the agent from DB
    2. Spawns the live BaseAgent instance
    3. Runs the task
    4. Updates Task and Agent DB records with results
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def execute_task(self, task_id: uuid.UUID) -> AgentResult:
        """
        Execute a Task by its ID.
        Updates task status throughout execution.
        """
        # Load the task
        task_result = await self.db.execute(select(Task).where(Task.id == task_id))
        task = task_result.scalar_one_or_none()
        if not task:
            raise ValueError(f"Task {task_id} not found")

        if not task.agent_id:
            raise ValueError(f"Task {task_id} has no assigned agent")

        # Update task status → running
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now(tz=timezone.utc)
        await self.db.flush()

        # Spawn the agent
        agent = await AgentRegistry.spawn_from_db(self.db, task.agent_id)
        if not agent:
            task.status = TaskStatus.FAILED
            task.error_message = f"Agent {task.agent_id} not found in registry"
            await self.db.flush()
            return AgentResult(
                content="",
                success=False,
                error=task.error_message,
            )

        # Parse task input
        try:
            input_data: dict = json.loads(task.input_data)
        except (json.JSONDecodeError, TypeError):
            input_data = {}

        task_prompt = input_data.get("prompt", task.description or task.title)
        context = input_data.get("context", {})

        # Run the agent
        try:
            result = await agent.run(task=task_prompt, context=context)
        except Exception as exc:
            logger.error("Agent execution error", task_id=str(task_id), error=str(exc))
            result = AgentResult(content="", success=False, error=str(exc))

        # Update task with results
        now = datetime.now(tz=timezone.utc)
        if result.success:
            task.status = TaskStatus.COMPLETED
            task.result_json = json.dumps(
                {
                    "content": result.content,
                    "tokens_used": result.tokens_used,
                    "cost_usd": result.cost_usd,
                    "duration_seconds": result.duration_seconds,
                    "iterations": result.iterations,
                    "trace_id": result.trace_id,
                }
            )
        else:
            task.retry_count += 1
            if task.retry_count < task.max_retries:
                task.status = TaskStatus.RETRYING
            else:
                task.status = TaskStatus.FAILED
            task.error_message = result.error

        task.completed_at = now
        await self.db.flush()

        # Update agent metrics
        await self._update_agent_metrics(task.agent_id, result)

        return result

    async def execute_agent_directly(
        self,
        agent_id: uuid.UUID,
        task: str,
        context: dict | None = None,
        max_iterations: int = 10,
    ) -> AgentResult:
        """
        Run an agent directly without creating a Task record.
        Used for quick one-off calls.
        """
        agent = await AgentRegistry.spawn_from_db(self.db, agent_id)
        if not agent:
            return AgentResult(content="", success=False, error=f"Agent {agent_id} not found")

        result = await agent.run(task=task, context=context or {}, max_iterations=max_iterations)
        await self._update_agent_metrics(agent_id, result)
        return result

    async def _update_agent_metrics(
        self, agent_id: uuid.UUID, result: AgentResult
    ) -> None:
        """Increment the agent's aggregated metrics in the database."""
        agent_result = await self.db.execute(
            select(AgentModel).where(AgentModel.id == agent_id)
        )
        db_agent = agent_result.scalar_one_or_none()
        if not db_agent:
            return

        db_agent.total_tokens_used += result.tokens_used
        db_agent.total_cost_usd += result.cost_usd
        db_agent.last_run_at = datetime.now(tz=timezone.utc)

        if result.success:
            db_agent.success_count += 1
        else:
            db_agent.error_count += 1

        db_agent.status = AgentStatus.IDLE
        await self.db.flush()
