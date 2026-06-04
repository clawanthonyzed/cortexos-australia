"""Content Agent — blog posts, product descriptions, landing pages, email copy."""
from __future__ import annotations

from app.agents.base import BaseAgent, AgentState
from app.agents.registry import register_agent


@register_agent("content")
class ContentAgent(BaseAgent):
    name = "Content"
    purpose = "Blog posts, product descriptions, landing page copy, and email sequences"
    agent_type = "content"

    def _default_system_prompt(self) -> str:
        return (
            "You are the Content Agent for CortexOS Australia.\n\n"
            "Your responsibilities:\n"
            "1. Long-form blog content (SEO-optimised, 1500–3000 words)\n"
            "2. Product descriptions for Etsy, Gumroad, LemonSqueezy\n"
            "3. Landing page copy (hero, features, social proof, CTA)\n"
            "4. Email sequences (welcome, nurture, promotional)\n"
            "5. Social media captions and ad copy\n\n"
            "Write in a clear, Australian-friendly voice. Avoid AI clichés. "
            "Focus on benefits over features. Always include a strong CTA."
        )

    async def _act(self, state: AgentState) -> AgentState:
        context = state.get("context", {})
        content_type = context.get("type", "blog_post")

        state["tool_results"].append(
            {
                "tool": "content_generation",
                "result": f"Content draft created: {content_type}",
                "status": "draft",
            }
        )
        state["messages"].append(
            {
                "role": "user",
                "content": "Refine and finalise the content. Ensure it's engaging and on-brand.",
            }
        )
        return state
