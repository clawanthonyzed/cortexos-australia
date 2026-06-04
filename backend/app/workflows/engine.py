"""WorkflowEngine — parse graph_json and build + run a LangGraph StateGraph."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow import Workflow, WorkflowStatus
from app.workflows.nodes import (
    WorkflowRunState,
    build_agent_node,
    build_condition_node,
    build_human_approval_node,
)

logger = structlog.get_logger(__name__)


class WorkflowEngine:
    """
    Parses a workflow's graph_json (React Flow format) and executes it
    using LangGraph StateGraph.

    graph_json structure:
    {
        "nodes": [
            {
                "id": "node-1",
                "type": "agent_node" | "condition_node" | "human_approval" | "start" | "end",
                "data": { ... node-specific config ... }
            },
            ...
        ],
        "edges": [
            { "id": "edge-1", "source": "node-1", "target": "node-2" },
            ...
        ]
    }
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def execute(
        self,
        workflow_id: uuid.UUID,
        input_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Load a workflow from DB and execute it.
        Returns the final run state.
        """
        # Load workflow
        result = await self.db.execute(
            select(Workflow).where(Workflow.id == workflow_id)
        )
        workflow = result.scalar_one_or_none()
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        # Update status
        workflow.status = WorkflowStatus.RUNNING
        workflow.run_count += 1
        await self.db.flush()

        run_id = str(uuid.uuid4())
        initial_state = WorkflowRunState(
            workflow_id=str(workflow_id),
            run_id=run_id,
            input_data=input_data or {},
            current_node_id="start",
            completed_nodes=[],
            node_results={},
            variables={},
            should_stop=False,
            requires_approval=False,
            approval_node_id=None,
            error=None,
            started_at=datetime.now(tz=timezone.utc).isoformat(),
        )

        try:
            try:
                graph_data = json.loads(workflow.graph_json)
            except (json.JSONDecodeError, TypeError):
                graph_data = {}

            if not graph_data or not graph_data.get("nodes"):
                # Simple linear workflow from WorkflowStep table
                final_state = await self._execute_steps(workflow, initial_state)
            else:
                # Full graph execution
                final_state = await self._execute_graph(graph_data, initial_state)

            if final_state.get("error"):
                workflow.status = WorkflowStatus.FAILED
                workflow.failure_count += 1
            elif final_state.get("requires_approval"):
                workflow.status = WorkflowStatus.PAUSED
            else:
                workflow.status = WorkflowStatus.COMPLETED
                workflow.success_count += 1

        except Exception as exc:
            logger.error("Workflow execution failed", workflow_id=str(workflow_id), error=str(exc))
            workflow.status = WorkflowStatus.FAILED
            workflow.failure_count += 1
            await self.db.flush()
            raise

        await self.db.flush()
        return dict(final_state)

    async def _execute_graph(
        self,
        graph_data: dict[str, Any],
        initial_state: WorkflowRunState,
    ) -> WorkflowRunState:
        """Build and run a LangGraph StateGraph from React Flow graph_data."""
        nodes: list[dict[str, Any]] = graph_data.get("nodes", [])
        edges: list[dict[str, Any]] = graph_data.get("edges", [])

        try:
            from langgraph.graph import END, START, StateGraph

            sg: StateGraph = StateGraph(WorkflowRunState)

            # Add nodes
            for node in nodes:
                node_id = node["id"]
                node_type = node.get("type", "agent_node")
                node_data = node.get("data", {})
                node_data["node_id"] = node_id

                if node_type in ("start", "end"):
                    continue
                elif node_type == "agent_node":
                    sg.add_node(node_id, build_agent_node(node_data, self.db))
                elif node_type == "condition_node":
                    sg.add_node(node_id, build_condition_node(node_data))
                elif node_type == "human_approval":
                    sg.add_node(node_id, build_human_approval_node(node_data))
                else:
                    logger.warning("Unknown node type", node_type=node_type)

            # Add edges
            start_nodes = [
                e["target"] for e in edges if e["source"] == "start"
            ]
            if start_nodes:
                sg.set_entry_point(start_nodes[0])
            else:
                # Find node with no incoming edges (excluding start)
                targets = {e["target"] for e in edges}
                sources = {e["source"] for e in edges}
                entry_candidates = sources - targets - {"start", "end"}
                if entry_candidates:
                    sg.set_entry_point(next(iter(entry_candidates)))

            for edge in edges:
                source = edge["source"]
                target = edge["target"]
                if source == "start" or target == "end":
                    if target == "end":
                        sg.add_edge(source, END)
                    continue
                sg.add_edge(source, target)

            compiled = sg.compile()
            final_state = await compiled.ainvoke(initial_state)
            return final_state

        except ImportError:
            logger.warning("LangGraph not available — running nodes sequentially")
            return await self._execute_sequential(nodes, edges, initial_state)

    async def _execute_sequential(
        self,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        state: WorkflowRunState,
    ) -> WorkflowRunState:
        """Fallback sequential execution without LangGraph."""
        # Build adjacency map
        adj: dict[str, str] = {}
        for edge in edges:
            adj[edge["source"]] = edge["target"]

        current = "start"
        visited: set[str] = set()

        while current and current not in ("end", None) and len(visited) < 50:
            visited.add(current)
            next_node_id = adj.get(current)
            if not next_node_id or next_node_id == "end":
                break

            # Find and execute the node
            node_def = next((n for n in nodes if n["id"] == next_node_id), None)
            if node_def:
                node_type = node_def.get("type", "agent_node")
                node_data = {**node_def.get("data", {}), "node_id": next_node_id}

                if node_type == "agent_node":
                    state = await build_agent_node(node_data, self.db)(state)
                elif node_type == "condition_node":
                    state = await build_condition_node(node_data)(state)
                elif node_type == "human_approval":
                    state = await build_human_approval_node(node_data)(state)

                if state.get("should_stop"):
                    break

            current = next_node_id

        return state

    async def _execute_steps(
        self,
        workflow: Workflow,
        state: WorkflowRunState,
    ) -> WorkflowRunState:
        """Execute workflow using its WorkflowStep records (linear)."""
        from sqlalchemy import select as sa_select
        from app.models.workflow import WorkflowStep

        steps_result = await self.db.execute(
            sa_select(WorkflowStep)
            .where(WorkflowStep.workflow_id == workflow.id)
            .order_by(WorkflowStep.order)
        )
        steps = steps_result.scalars().all()

        for step in steps:
            if state.get("should_stop"):
                break
            try:
                config = json.loads(step.config_json)
            except (json.JSONDecodeError, TypeError):
                config = {}

            config["node_id"] = str(step.id)

            if step.step_type == "agent_node":
                state = await build_agent_node(config, self.db)(state)
            elif step.step_type == "condition_node":
                state = await build_condition_node(config)(state)
            elif step.step_type == "human_approval":
                state = await build_human_approval_node(config)(state)

        return state
