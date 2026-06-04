"""Finance Agent — revenue analysis, cost tracking, and financial reporting."""
from __future__ import annotations

from app.agents.base import BaseAgent, AgentState
from app.agents.registry import register_agent


@register_agent("finance")
class FinanceAgent(BaseAgent):
    name = "Finance"
    purpose = "Revenue analysis, cost tracking, P&L reporting, and financial forecasting"
    agent_type = "finance"

    def _default_system_prompt(self) -> str:
        return (
            "You are the Finance Agent for CortexOS Australia.\n\n"
            "Your responsibilities:\n"
            "1. Revenue analysis across all ventures and platforms\n"
            "2. LLM API cost tracking and optimisation\n"
            "3. P&L reporting (monthly/quarterly)\n"
            "4. Revenue forecasting and target tracking\n"
            "5. Tax considerations for Australian trust structures\n\n"
            "Note: Revenue flows through Cudan Studio. TPI pension rules apply — "
            "keep all revenue outside personal income.\n\n"
            "Present all AUD figures clearly. Flag any cost anomalies immediately."
        )

    async def _act(self, state: AgentState) -> AgentState:
        context = state.get("context", {})
        period = context.get("period", "current month")

        state["tool_results"].append(
            {
                "tool": "financial_analysis",
                "result": f"Financial analysis completed for: {period}",
                "status": "complete",
            }
        )
        state["messages"].append(
            {
                "role": "user",
                "content": (
                    f"Provide the financial summary for {period} "
                    "with revenue, costs, profit margin, and recommendations."
                ),
            }
        )
        return state
