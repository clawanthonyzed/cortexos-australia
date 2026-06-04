"""BaseAgent — LangGraph-backed agent with memory, observability, and cost tracking."""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, TypedDict

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.base import BaseLLM, LLMMessage
from app.llm.factory import LLMFactory
from app.memory.manager import MemoryManager
from app.models.agent import AgentStatus
from app.models.cost_record import CostRecord
from app.observability.langfuse import get_tracer

logger = structlog.get_logger(__name__)


@dataclass
class AgentResult:
    """Return value from BaseAgent.run()"""

    content: str
    success: bool = True
    error: str | None = None
    tokens_used: int = 0
    cost_usd: float = 0.0
    duration_seconds: float = 0.0
    iterations: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    trace_id: str | None = None


class AgentState(TypedDict):
    """LangGraph state dict for the ReAct loop."""

    task: str
    context: dict[str, Any]
    messages: list[dict[str, str]]
    thoughts: list[str]
    tool_results: list[dict[str, Any]]
    final_answer: str
    iterations: int
    max_iterations: int
    should_stop: bool
    error: str | None


class BaseAgent:
    """
    LangGraph-backed agent with:
    - Configurable LLM (via LLMFactory)
    - Short/long-term memory (MemoryManager)
    - Token cost tracking (CostRecord)
    - Langfuse observability
    - ReAct reasoning loop
    """

    name: str = "base"
    purpose: str = "General purpose agent"
    agent_type: str = "custom"

    def __init__(
        self,
        db: AsyncSession,
        model_provider: str = "claude",
        model_name: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        system_prompt: str | None = None,
        agent_db_id: uuid.UUID | None = None,
        tools: list[Any] | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        self.db = db
        self.llm: BaseLLM = LLMFactory.create(model_provider, model_name)
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt or self._default_system_prompt()
        self.agent_db_id = agent_db_id
        self.tools: list[Any] = tools or []
        self.config: dict[str, Any] = config or {}
        self.memory: MemoryManager = MemoryManager(db=db)
        self.status: str = AgentStatus.IDLE

    def _default_system_prompt(self) -> str:
        return (
            f"You are {self.name}, an AI agent.\n"
            f"Purpose: {self.purpose}\n\n"
            "Think step-by-step. Be concise and accurate. "
            "When you have enough information, provide a clear final answer."
        )

    def _build_state(
        self, task: str, context: dict[str, Any], max_iterations: int
    ) -> AgentState:
        return AgentState(
            task=task,
            context=context,
            messages=[],
            thoughts=[],
            tool_results=[],
            final_answer="",
            iterations=0,
            max_iterations=max_iterations,
            should_stop=False,
            error=None,
        )

    async def _think(self, state: AgentState) -> AgentState:
        """Reasoning step — build prompt and call LLM."""
        # Inject memory context
        memories = await self.memory.recall(
            query=state["task"],
            agent_id=str(self.agent_db_id) if self.agent_db_id else None,
            limit=5,
        )
        memory_context = ""
        if memories:
            memory_context = "\n\nRelevant memories:\n" + "\n".join(
                f"- {m.get('memory', '')}" for m in memories
            )

        system = (
            self.system_prompt
            + memory_context
            + "\n\nContext:\n"
            + json.dumps(state["context"], indent=2, default=str)
        )

        messages_so_far = [LLMMessage(**m) for m in state["messages"]]
        if not messages_so_far:
            messages_so_far = [LLMMessage(role="user", content=state["task"])]

        response = await self.llm.complete(
            messages=messages_so_far,
            system=system,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        state["messages"].append({"role": "assistant", "content": response.content})
        state["thoughts"].append(response.content)
        state["iterations"] += 1

        # Store cost
        if self.agent_db_id:
            record = CostRecord(
                agent_id=self.agent_db_id,
                provider=self.llm.provider,
                model=self.llm.model,
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
                cache_creation_tokens=response.usage.cache_creation_tokens,
                cache_read_tokens=response.usage.cache_read_tokens,
                cost_usd=response.usage.cost_usd,
                label="agent_think",
            )
            self.db.add(record)
            await self.db.flush()

        # Determine if we should stop
        lower = response.content.lower()
        if any(
            marker in lower
            for marker in ["final answer:", "my answer:", "in conclusion:", "therefore:"]
        ):
            state["final_answer"] = response.content
            state["should_stop"] = True

        if state["iterations"] >= state["max_iterations"]:
            state["final_answer"] = response.content
            state["should_stop"] = True

        return state

    async def _act(self, state: AgentState) -> AgentState:
        """Tool execution step (override in subclasses to call real tools)."""
        # Base implementation: no tools, go straight to stop
        if not self.tools:
            state["should_stop"] = True
        return state

    def _build_langgraph(self) -> Any:
        """
        Build a LangGraph StateGraph for the think → act → decide loop.
        Returns a compiled graph.
        """
        try:
            from langgraph.graph import END, StateGraph

            graph: StateGraph = StateGraph(AgentState)
            graph.add_node("think", self._think)
            graph.add_node("act", self._act)

            def should_continue(state: AgentState) -> str:
                if state.get("should_stop") or state.get("error"):
                    return "end"
                return "act"

            graph.set_entry_point("think")
            graph.add_conditional_edges("think", should_continue, {"end": END, "act": "act"})
            graph.add_edge("act", "think")

            return graph.compile()
        except ImportError:
            return None

    async def run(
        self,
        task: str,
        context: dict[str, Any] | None = None,
        max_iterations: int = 10,
    ) -> AgentResult:
        """Execute the agent on a task and return AgentResult."""
        self.status = AgentStatus.RUNNING
        t0 = time.perf_counter()
        tracer = get_tracer(f"agent:{self.name}", metadata={"task": task[:200]})

        context = context or {}
        state = self._build_state(task, context, max_iterations)

        total_tokens = 0
        total_cost = 0.0
        trace_id: str | None = None

        with tracer:
            trace_id = tracer.trace_id
            try:
                compiled_graph = self._build_langgraph()

                if compiled_graph:
                    final_state = await compiled_graph.ainvoke(state)
                else:
                    # Fallback: manual loop without LangGraph
                    while not state["should_stop"] and state["error"] is None:
                        state = await self._think(state)
                        if not state["should_stop"]:
                            state = await self._act(state)
                    final_state = state

                content = (
                    final_state.get("final_answer")
                    or (final_state["thoughts"][-1] if final_state["thoughts"] else "")
                    or "No response generated."
                )

                # Store result in memory
                await self.memory.remember(
                    content=f"Task: {task[:200]}\nResult: {content[:500]}",
                    agent_id=str(self.agent_db_id) if self.agent_db_id else None,
                    memory_type="episodic",
                    importance=0.6,
                )

                self.status = AgentStatus.IDLE
                elapsed = time.perf_counter() - t0

                return AgentResult(
                    content=content,
                    success=True,
                    tokens_used=total_tokens,
                    cost_usd=total_cost,
                    duration_seconds=round(elapsed, 3),
                    iterations=final_state.get("iterations", 0),
                    trace_id=trace_id,
                )

            except Exception as exc:
                self.status = AgentStatus.ERROR
                elapsed = time.perf_counter() - t0
                logger.error("Agent run failed", agent=self.name, error=str(exc))
                return AgentResult(
                    content="",
                    success=False,
                    error=str(exc),
                    duration_seconds=round(elapsed, 3),
                    trace_id=trace_id,
                )
