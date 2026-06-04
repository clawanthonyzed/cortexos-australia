"""Stripe MCP — payment and subscription management."""
from __future__ import annotations

from typing import Any

import structlog

from app.mcp.base import BaseMCPServer, MCPToolResult

logger = structlog.get_logger(__name__)

STRIPE_API = "https://api.stripe.com/v1"


class StripeMCP(BaseMCPServer):
    name = "stripe"
    description = "Stripe — payments, customers, subscriptions, payouts"

    def __init__(self, secret_key: str = "") -> None:
        self.secret_key = secret_key

    async def health_check(self) -> bool:
        if not self.secret_key:
            return False
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as c:
                r = await c.get(
                    f"{STRIPE_API}/account",
                    auth=(self.secret_key, ""),
                )
                return r.status_code == 200
        except Exception:
            return False

    async def list_tools(self) -> list[dict[str, Any]]:
        return [
            {"name": "list_products", "description": "List Stripe products"},
            {"name": "list_customers", "description": "List customers"},
            {"name": "get_balance", "description": "Get account balance"},
            {"name": "list_charges", "description": "List recent charges"},
            {"name": "create_payment_link", "description": "Create a payment link"},
        ]

    async def call_tool(self, tool_name: str, params: dict[str, Any]) -> MCPToolResult:
        if not self.secret_key:
            return MCPToolResult(success=False, error="Stripe secret key not configured")
        import httpx
        auth = (self.secret_key, "")

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                match tool_name:
                    case "list_products":
                        r = await client.get(
                            f"{STRIPE_API}/products",
                            auth=auth,
                            params={"limit": params.get("limit", 20), "active": "true"},
                        )
                        r.raise_for_status()
                        return MCPToolResult(success=True, data=r.json())

                    case "list_customers":
                        r = await client.get(
                            f"{STRIPE_API}/customers",
                            auth=auth,
                            params={"limit": params.get("limit", 20)},
                        )
                        r.raise_for_status()
                        return MCPToolResult(success=True, data=r.json())

                    case "get_balance":
                        r = await client.get(f"{STRIPE_API}/balance", auth=auth)
                        r.raise_for_status()
                        return MCPToolResult(success=True, data=r.json())

                    case "list_charges":
                        r = await client.get(
                            f"{STRIPE_API}/charges",
                            auth=auth,
                            params={"limit": params.get("limit", 20)},
                        )
                        r.raise_for_status()
                        return MCPToolResult(success=True, data=r.json())

                    case "create_payment_link":
                        r = await client.post(
                            f"{STRIPE_API}/payment_links",
                            auth=auth,
                            data={
                                "line_items[0][price]": params["price_id"],
                                "line_items[0][quantity]": str(params.get("quantity", 1)),
                            },
                        )
                        r.raise_for_status()
                        return MCPToolResult(success=True, data=r.json())

                    case _:
                        return MCPToolResult(success=False, error=f"Unknown tool: {tool_name}")

        except Exception as exc:
            logger.error("Stripe MCP error", tool=tool_name, error=str(exc))
            return MCPToolResult(success=False, error=str(exc))
