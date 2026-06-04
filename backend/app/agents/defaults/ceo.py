"""CEO Agent — strategic planning, coordination, and delegation."""
from __future__ import annotations

from app.agents.base import BaseAgent, AgentState
from app.agents.registry import register_agent


@register_agent("ceo")
class CEOAgent(BaseAgent):
    name = "CEO"
    purpose = "Strategic planning, venture coordination, and high-level decision-making"
    agent_type = "ceo"

    def _default_system_prompt(self) -> str:
        return (
            "You are the CEO Agent for CortexOS Australia, an AI holding company.\n\n"
            "Your responsibilities:\n"
            "1. Strategic planning and goal setting\n"
            "2. Coordinating specialist agents (Research, Product, Marketing, Finance, etc.)\n"
            "3. Prioritising tasks and ventures\n"
            "4. Making high-level decisions based on data\n"
            "5. Revenue optimisation across all product lines\n\n"
            "Think like a seasoned executive. Be decisive, data-driven, and outcome-focused.\n"
            "Always structure your responses with: SITUATION → ANALYSIS → DECISION → NEXT ACTIONS."
        )

    async def _act(self, state: AgentState) -> AgentState:
        """CEO-specific action: decompose into sub-tasks for delegation."""
        last_thought = state["thoughts"][-1] if state["thoughts"] else ""

        # If the CEO's last thought mentions delegation, simulate it
        if "delegate" in last_thought.lower() or "assign" in last_thought.lower():
            state["tool_results"].append(
                {
                    "tool": "delegation",
                    "result": "Sub-tasks queued for specialist agents",
                    "status": "queued",
                }
            )

        state["should_stop"] = True
        return state
