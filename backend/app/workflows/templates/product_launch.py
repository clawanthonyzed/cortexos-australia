"""Product Launch workflow template: research → create → list → market."""
from __future__ import annotations

from typing import Any


def get_product_launch_template(
    research_agent_id: str | None = None,
    product_agent_id: str | None = None,
    seo_agent_id: str | None = None,
    marketing_agent_id: str | None = None,
) -> dict[str, Any]:
    """
    Returns a React Flow-compatible graph_json for a product launch workflow.

    Nodes: market_research → product_creation → seo_optimise → marketing_campaign
    Includes a human approval gate before the marketing step.
    """
    return {
        "nodes": [
            {"id": "start", "type": "start", "data": {}},
            {
                "id": "market_research",
                "type": "agent_node",
                "data": {
                    "agent_id": research_agent_id,
                    "agent_type": "research",
                    "task_template": (
                        "Research the market for: {product_idea}. "
                        "Identify top competitors, pricing, and positioning opportunities."
                    ),
                },
            },
            {
                "id": "product_creation",
                "type": "agent_node",
                "data": {
                    "agent_id": product_agent_id,
                    "agent_type": "product",
                    "task_template": (
                        "Create a full product specification for: {product_idea}. "
                        "Research findings: {market_research_output}"
                    ),
                },
            },
            {
                "id": "seo_optimise",
                "type": "agent_node",
                "data": {
                    "agent_id": seo_agent_id,
                    "agent_type": "seo",
                    "task_template": (
                        "Create an SEO strategy for the product: {product_creation_output}. "
                        "Niche: {product_idea}"
                    ),
                },
            },
            {
                "id": "approval_gate",
                "type": "human_approval",
                "data": {
                    "message": (
                        "Product spec and SEO strategy ready. "
                        "Approve to launch marketing campaign."
                    ),
                },
            },
            {
                "id": "marketing_campaign",
                "type": "agent_node",
                "data": {
                    "agent_id": marketing_agent_id,
                    "agent_type": "marketing",
                    "task_template": (
                        "Create a full marketing campaign for: {product_creation_output}. "
                        "SEO strategy: {seo_optimise_output}"
                    ),
                },
            },
            {"id": "end", "type": "end", "data": {}},
        ],
        "edges": [
            {"id": "e1", "source": "start", "target": "market_research"},
            {"id": "e2", "source": "market_research", "target": "product_creation"},
            {"id": "e3", "source": "product_creation", "target": "seo_optimise"},
            {"id": "e4", "source": "seo_optimise", "target": "approval_gate"},
            {"id": "e5", "source": "approval_gate", "target": "marketing_campaign"},
            {"id": "e6", "source": "marketing_campaign", "target": "end"},
        ],
    }
