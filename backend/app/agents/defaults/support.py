"""Support Agent — customer support workflows and FAQ generation."""
from __future__ import annotations

from app.agents.base import BaseAgent, AgentState
from app.agents.registry import register_agent


@register_agent("support")
class SupportAgent(BaseAgent):
    name = "Support"
    purpose = "Customer support workflows, FAQ generation, and issue resolution"
    agent_type = "support"

    def _default_system_prompt(self) -> str:
        return (
            "You are the Support Agent for CortexOS Australia.\n\n"
            "Your responsibilities:\n"
            "1. Drafting customer support response templates\n"
            "2. Creating comprehensive FAQ documents for products\n"
            "3. Designing support workflow SOPs\n"
            "4. Handling refund and dispute policy documentation\n"
            "5. Identifying common issues and proactive solutions\n\n"
            "Be empathetic, clear, and solution-focused. "
            "Responses should resolve issues completely, not just acknowledge them."
        )

    async def _act(self, state: AgentState) -> AgentState:
        context = state.get("context", {})
        issue_type = context.get("issue_type", "general")

        state["tool_results"].append(
            {
                "tool": "support_response",
                "result": f"Support response drafted for: {issue_type}",
                "status": "complete",
            }
        )
        state["messages"].append(
            {
                "role": "user",
                "content": "Finalise the support response ensuring it's empathetic and complete.",
            }
        )
        return state
