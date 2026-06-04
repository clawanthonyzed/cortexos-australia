"""Product Agent — digital product creation, packaging, and asset generation."""
from __future__ import annotations

from app.agents.base import BaseAgent, AgentState
from app.agents.registry import register_agent


@register_agent("product")
class ProductAgent(BaseAgent):
    name = "Product"
    purpose = "Digital product creation, packaging, pricing strategy, and marketplace listing"
    agent_type = "product"

    def _default_system_prompt(self) -> str:
        return (
            "You are the Product Agent for CortexOS Australia.\n\n"
            "Your responsibilities:\n"
            "1. Defining digital product specs (eBooks, templates, tools, courses)\n"
            "2. Pricing strategy (AUD market, competitive positioning)\n"
            "3. Product descriptions optimised for Etsy, Gumroad, LemonSqueezy\n"
            "4. Asset creation briefs (cover images, mockups, demos)\n"
            "5. Product line expansion planning\n\n"
            "Structure product definitions as:\n"
            "PRODUCT NAME → VALUE PROPOSITION → TARGET CUSTOMER → PRICING → "
            "DIFFERENTIATORS → LISTING COPY → ASSETS NEEDED."
        )

    async def _act(self, state: AgentState) -> AgentState:
        state["tool_results"].append(
            {
                "tool": "product_creation",
                "result": "Product specification generated",
                "status": "complete",
            }
        )
        state["messages"].append(
            {
                "role": "user",
                "content": "Finalise the product spec with pricing and listing copy.",
            }
        )
        return state
