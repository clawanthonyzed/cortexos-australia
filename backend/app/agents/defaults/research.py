"""Research Agent — market research, competitor analysis, trend discovery."""
from __future__ import annotations

from app.agents.base import BaseAgent, AgentState
from app.agents.registry import register_agent


@register_agent("research")
class ResearchAgent(BaseAgent):
    name = "Research"
    purpose = "Market research, competitor analysis, trend discovery, and data synthesis"
    agent_type = "research"

    def _default_system_prompt(self) -> str:
        return (
            "You are the Research Agent for CortexOS Australia.\n\n"
            "Your responsibilities:\n"
            "1. Market research and opportunity identification\n"
            "2. Competitor analysis (pricing, positioning, features)\n"
            "3. Trend analysis across digital product markets\n"
            "4. Keyword research for SEO opportunities\n"
            "5. Synthesising research into actionable insights\n\n"
            "Be thorough and evidence-based. Structure research as:\n"
            "FINDINGS → KEY INSIGHTS → OPPORTUNITIES → RECOMMENDATIONS.\n\n"
            "Focus on Australian market conditions and AUD pricing where relevant."
        )

    async def _act(self, state: AgentState) -> AgentState:
        """Research-specific action: simulate web research synthesis."""
        context = state.get("context", {})
        topic = context.get("topic", state["task"])

        state["tool_results"].append(
            {
                "tool": "research_synthesis",
                "result": f"Research completed for: {topic}",
                "sources": ["market reports", "competitor websites", "trend data"],
                "status": "complete",
            }
        )
        state["messages"].append(
            {
                "role": "user",
                "content": (
                    f"Based on your research about '{topic}', "
                    "provide your final structured findings and recommendations."
                ),
            }
        )
        return state
