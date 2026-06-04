"""LemonSqueezy MCP — product and order management."""
from __future__ import annotations

from typing import Any

import httpx
import structlog

from app.mcp.base import BaseMCPServer, MCPToolResult

logger = structlog.get_logger(__name__)

LS_API = "https://api.lemonsqueezy.com/v1"


class LemonSqueezeMCP(BaseMCPServer):
    name = "lemonsqueezy"
    description = "LemonSqueezy product, order and subscription management"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/vnd.api+json",
        }

    async def health_check(self) -> bool:
        if not self.api_key:
            return False
        try:
            async with httpx.AsyncClient(timeout=10.0) as c:
                r = await c.get(f"{LS_API}/users/me", headers=self._headers)
                return r.status_code == 200
        except Exception:
            return False

    async def list_tools(self) -> list[dict[str, Any]]:
        return [
            {"name": "get_user", "description": "Get authenticated user"},
            {"name": "list_stores", "description": "List all stores"},
            {"name": "list_products", "description": "List products in a store"},
            {"name": "list_orders", "description": "List orders"},
            {"name": "get_order", "description": "Get a specific order"},
        ]

    async def call_tool(self, tool_name: str, params: dict[str, Any]) -> MCPToolResult:
        if not self.api_key:
            return MCPToolResult(success=False, error="LemonSqueezy API key not configured")
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                match tool_name:
                    case "get_user":
                        r = await client.get(f"{LS_API}/users/me", headers=self._headers)
                        r.raise_for_status()
                        return MCPToolResult(success=True, data=r.json())

                    case "list_stores":
                        r = await client.get(f"{LS_API}/stores", headers=self._headers)
                        r.raise_for_status()
                        return MCPToolResult(success=True, data=r.json().get("data", []))

                    case "list_products":
                        query = {}
                        if store_id := params.get("store_id"):
                            query["filter[store_id]"] = store_id
                        r = await client.get(
                            f"{LS_API}/products", headers=self._headers, params=query
                        )
                        r.raise_for_status()
                        return MCPToolResult(success=True, data=r.json().get("data", []))

                    case "list_orders":
                        query = {}
                        if store_id := params.get("store_id"):
                            query["filter[store_id]"] = store_id
                        r = await client.get(
                            f"{LS_API}/orders", headers=self._headers, params=query
                        )
                        r.raise_for_status()
                        return MCPToolResult(success=True, data=r.json().get("data", []))

                    case "get_order":
                        r = await client.get(
                            f"{LS_API}/orders/{params['order_id']}", headers=self._headers
                        )
                        r.raise_for_status()
                        return MCPToolResult(success=True, data=r.json().get("data"))

                    case _:
                        return MCPToolResult(success=False, error=f"Unknown tool: {tool_name}")

        except httpx.HTTPStatusError as exc:
            return MCPToolResult(success=False, error=f"LemonSqueezy error: {exc.response.status_code}")
        except Exception as exc:
            logger.error("LemonSqueezy MCP error", tool=tool_name, error=str(exc))
            return MCPToolResult(success=False, error=str(exc))
