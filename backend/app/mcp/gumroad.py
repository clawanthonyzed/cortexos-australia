"""Gumroad MCP — product and sale management."""
from __future__ import annotations

from typing import Any

import httpx
import structlog

from app.mcp.base import BaseMCPServer, MCPToolResult

logger = structlog.get_logger(__name__)

GUMROAD_API = "https://api.gumroad.com/v2"


class GumroadMCP(BaseMCPServer):
    name = "gumroad"
    description = "Gumroad product and sale management"

    def __init__(self, access_token: str) -> None:
        self.access_token = access_token

    async def health_check(self) -> bool:
        if not self.access_token:
            return False
        try:
            async with httpx.AsyncClient(timeout=10.0) as c:
                r = await c.get(
                    f"{GUMROAD_API}/user",
                    params={"access_token": self.access_token},
                )
                return r.status_code == 200
        except Exception:
            return False

    async def list_tools(self) -> list[dict[str, Any]]:
        return [
            {"name": "get_user", "description": "Get authenticated Gumroad user info"},
            {"name": "list_products", "description": "List all products"},
            {"name": "get_product", "description": "Get a specific product"},
            {"name": "list_sales", "description": "List sales with optional date filter"},
            {"name": "get_sale", "description": "Get a specific sale by ID"},
        ]

    async def call_tool(self, tool_name: str, params: dict[str, Any]) -> MCPToolResult:
        if not self.access_token:
            return MCPToolResult(success=False, error="Gumroad access token not configured")
        base_params = {"access_token": self.access_token}
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                match tool_name:
                    case "get_user":
                        r = await client.get(f"{GUMROAD_API}/user", params=base_params)
                        r.raise_for_status()
                        return MCPToolResult(success=True, data=r.json().get("user"))

                    case "list_products":
                        r = await client.get(f"{GUMROAD_API}/products", params=base_params)
                        r.raise_for_status()
                        return MCPToolResult(success=True, data=r.json().get("products", []))

                    case "get_product":
                        r = await client.get(
                            f"{GUMROAD_API}/products/{params['product_id']}",
                            params=base_params,
                        )
                        r.raise_for_status()
                        return MCPToolResult(success=True, data=r.json().get("product"))

                    case "list_sales":
                        query_params = {**base_params}
                        if after := params.get("after"):
                            query_params["after"] = after
                        if before := params.get("before"):
                            query_params["before"] = before
                        r = await client.get(f"{GUMROAD_API}/sales", params=query_params)
                        r.raise_for_status()
                        return MCPToolResult(success=True, data=r.json().get("sales", []))

                    case "get_sale":
                        r = await client.get(
                            f"{GUMROAD_API}/sales/{params['sale_id']}",
                            params=base_params,
                        )
                        r.raise_for_status()
                        return MCPToolResult(success=True, data=r.json().get("sale"))

                    case _:
                        return MCPToolResult(success=False, error=f"Unknown tool: {tool_name}")

        except httpx.HTTPStatusError as exc:
            return MCPToolResult(success=False, error=f"Gumroad error: {exc.response.status_code}")
        except Exception as exc:
            logger.error("Gumroad MCP error", tool=tool_name, error=str(exc))
            return MCPToolResult(success=False, error=str(exc))
