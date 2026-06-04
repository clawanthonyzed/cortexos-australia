"""SEO Agent — keyword discovery, content planning, and ranking strategy."""
from __future__ import annotations

from app.agents.base import BaseAgent, AgentState
from app.agents.registry import register_agent


@register_agent("seo")
class SEOAgent(BaseAgent):
    name = "SEO"
    purpose = "Keyword discovery, content planning, on-page SEO, and ranking strategy"
    agent_type = "seo"

    def _default_system_prompt(self) -> str:
        return (
            "You are the SEO Agent for CortexOS Australia.\n\n"
            "Your responsibilities:\n"
            "1. Keyword research (volume, competition, intent)\n"
            "2. Content gap analysis\n"
            "3. On-page SEO recommendations (title, meta, headings, schema)\n"
            "4. Internal linking strategy\n"
            "5. Etsy and marketplace SEO (tags, titles, attributes)\n\n"
            "Prioritise buyer-intent keywords. Structure output as:\n"
            "PRIMARY KEYWORDS → LONG-TAIL OPPORTUNITIES → CONTENT STRATEGY → "
            "ON-PAGE CHECKLIST → QUICK WINS."
        )

    async def _act(self, state: AgentState) -> AgentState:
        context = state.get("context", {})
        niche = context.get("niche", "digital products")

        state["tool_results"].append(
            {
                "tool": "keyword_research",
                "result": f"Keywords identified for: {niche}",
                "status": "complete",
            }
        )
        state["messages"].append(
            {
                "role": "user",
                "content": f"Provide the full SEO strategy and keyword list for: {niche}",
            }
        )
        return state
