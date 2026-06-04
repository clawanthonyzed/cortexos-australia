"""Workflow node types for LangGraph StateGraph."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, TypedDict

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)


class WorkflowRunState(TypedDict):
    """LangGraph state for workflow execution."""

    workflow_id: str
    run_id: str
    input_data: dict[str, Any]
    current_node_id: str
    completed_nodes: list[str]
    node_results: dict[str, Any]
    variables: dict[str, Any]
    should_stop: bool
    requires_approval: bool
    approval_node_id: str | None
    error: str | None
    started_at: str


def build_agent_node(node_config: dict[str, Any], db: AsyncSession):
    """
    Factory that returns an async node function for running an agent.
    node_config expected keys:
        - agent_id: UUID of the agent
        - agent_type: type string (fallback if no agent_id)
        - task_template: string with {variable} substitution
    """
    async def agent_node(state: WorkflowRunState) -> WorkflowRunState:
        from app.agents.registry import AgentRegistry
        from app.agents.executor import AgentExecutor

        node_id = node_config.get("node_id", "agent_node")
        agent_id_str = node_config.get("agent_id")
        task_template = node_config.get("task_template", "Process the workflow input.")

        # Substitute variables into the task
        try:
            task = task_template.format(**state.get("variables", {}), **state.get("input_data", {}))
        except KeyError:
            task = task_template

        try:
            if agent_id_str:
                agent_id = uuid.UUID(agent_id_str)
                executor = AgentExecutor(db)
                result = await executor.execute_agent_directly(
                    agent_id=agent_id,
                    task=task,
                    context=state.get("variables", {}),
                )
            else:
                # Spawn by type
                agent_type = node_config.get("agent_type", "custom")
                agent = await AgentRegistry.spawn(db=db, agent_type=agent_type)
                result = await agent.run(task=task, context=state.get("variables", {}))

            state["node_results"][node_id] = {
                "content": result.content,
                "success": result.success,
                "cost_usd": result.cost_usd,
                "tokens": result.tokens_used,
            }
            state["variables"][f"{node_id}_output"] = result.content
            state["completed_nodes"].append(node_id)

        except Exception as exc:
            logger.error("Agent node failed", node_id=node_id, error=str(exc))
            state["error"] = str(exc)
            state["should_stop"] = True

        return state

    return agent_node


def build_condition_node(node_config: dict[str, Any]):
    """
    Returns an async condition node that evaluates an expression
    and sets the next route in state["variables"]["_next_route"].
    """
    async def condition_node(state: WorkflowRunState) -> WorkflowRunState:
        node_id = node_config.get("node_id", "condition")
        condition = node_config.get("condition", "True")
        true_route = node_config.get("true_route", "end")
        false_route = node_config.get("false_route", "end")

        try:
            # Safe eval of simple conditions using the state variables
            result = eval(condition, {"__builtins__": {}}, state.get("variables", {}))
            state["variables"]["_next_route"] = true_route if result else false_route
            state["completed_nodes"].append(node_id)
        except Exception as exc:
            logger.warning("Condition eval failed", condition=condition, error=str(exc))
            state["variables"]["_next_route"] = false_route

        return state

    return condition_node


def build_human_approval_node(node_config: dict[str, Any]):
    """
    Pauses the workflow and requires human approval via API.
    Sets requires_approval=True and stores the node_id to resume from.
    """
    async def human_approval_node(state: WorkflowRunState) -> WorkflowRunState:
        node_id = node_config.get("node_id", "approval")
        message = node_config.get("message", "Workflow requires your approval to continue.")

        logger.info(
            "Workflow paused — awaiting human approval",
            run_id=state.get("run_id"),
            node=node_id,
        )

        state["requires_approval"] = True
        state["approval_node_id"] = node_id
        state["should_stop"] = True
        state["variables"][f"{node_id}_message"] = message
        state["completed_nodes"].append(f"{node_id}_pending")

        return state

    return human_approval_node
