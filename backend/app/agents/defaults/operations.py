"""Operations Agent — SOPs, workflow management, and process optimisation."""
from __future__ import annotations

from app.agents.base import BaseAgent, AgentState
from app.agents.registry import register_agent


@register_agent("operations")
class OperationsAgent(BaseAgent):
    name = "Operations"
    purpose = "SOP creation, workflow design, process optimisation, and team coordination"
    agent_type = "operations"

    def _default_system_prompt(self) -> str:
        return (
            "You are the Operations Agent for CortexOS Australia.\n\n"
            "Your responsibilities:\n"
            "1. Standard Operating Procedure (SOP) creation and maintenance\n"
            "2. Workflow design and optimisation\n"
            "3. Agent task scheduling and prioritisation\n"
            "4. Bottleneck identification and process improvement\n"
            "5. Infrastructure and tooling recommendations\n\n"
            "Think in systems. Every process should be:\n"
            "- Documented with clear steps\n"
            "- Measurable with defined KPIs\n"
            "- Reproducible without tribal knowledge\n"
            "- Automatable where possible."
        )

    async def _act(self, state: AgentState) -> AgentState:
        context = state.get("context", {})
        process = context.get("process", "general workflow")

        state["tool_results"].append(
            {
                "tool": "sop_generation",
                "result": f"SOP drafted for: {process}",
                "status": "draft",
            }
        )
        state["messages"].append(
            {
                "role": "user",
                "content": (
                    f"Finalise the SOP for '{process}' "
                    "with step-by-step instructions, owner assignments, and KPIs."
                ),
            }
        )
        return state
