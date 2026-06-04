"""Marketing Agent — social media, email marketing, paid ads, distribution."""
from __future__ import annotations

from app.agents.base import BaseAgent, AgentState
from app.agents.registry import register_agent


@register_agent("marketing")
class MarketingAgent(BaseAgent):
    name = "Marketing"
    purpose = "Social media strategy, email campaigns, paid ads, and product distribution"
    agent_type = "marketing"

    def _default_system_prompt(self) -> str:
        return (
            "You are the Marketing Agent for CortexOS Australia.\n\n"
            "Your responsibilities:\n"
            "1. Social media content strategy (Instagram, TikTok, Pinterest, X)\n"
            "2. Email marketing campaigns and automation flows\n"
            "3. Paid advertising strategy (Meta Ads, Google Ads)\n"
            "4. Influencer and affiliate partnership outreach\n"
            "5. Product launch sequences and promotional calendars\n\n"
            "Focus on ROI and measurable outcomes. Structure campaigns as:\n"
            "OBJECTIVE → TARGET AUDIENCE → CHANNELS → CREATIVE → BUDGET → KPIs → TIMELINE."
        )

    async def _act(self, state: AgentState) -> AgentState:
        context = state.get("context", {})
        product = context.get("product", "digital product")

        state["tool_results"].append(
            {
                "tool": "campaign_planning",
                "result": f"Marketing campaign planned for: {product}",
                "status": "complete",
            }
        )
        state["messages"].append(
            {
                "role": "user",
                "content": (
                    f"Create the full marketing plan for '{product}' "
                    "including content calendar, channel strategy, and launch sequence."
                ),
            }
        )
        return state
