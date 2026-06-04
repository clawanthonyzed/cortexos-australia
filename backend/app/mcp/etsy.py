"""Etsy MCP — shop management, listing sync."""
from __future__ import annotations

from typing import Any

import httpx
import structlog

from app.mcp.base import BaseMCPServer, MCPToolResult

logger = structlog.get_logger(__name__)

ETSY_API = "https://openapi.etsy.com/v3"


class EtsyMCP(BaseMCPServer):
    name = "etsy"
    description = "Etsy shop management — listings, orders, inventory"

    def __init__(self, api_key: str, shared_secret: str = "") -> None:
        self.api_key = api_key
        self.shared_secret = shared_secret
        self._headers = {"x-api-key": api_key}

    async def health_check(self) -> bool:
        if not self.api_key:
            return False
        try:
            async with httpx.AsyncClient(timeout=10.0) as c:
                r = await c.get(f"{ETSY_API}/application/openapi-ping", headers=self._headers)
                return r.status_code == 200
        except Exception:
            return False

    async def list_tools(self) -> list[dict[str, Any]]:
        return [
            {"name": "get_shop", "description": "Get shop info by shop_id"},
            {"name": "list_listings", "description": "List active shop listings"},
            {"name": "get_listing", "description": "Get a specific listing by ID"},
            {"name": "create_listing", "description": "Create a new listing draft"},
            {"name": "update_listing", "description": "Update listing details"},
        ]

    async def call_tool(self, tool_name: str, params: dict[str, Any]) -> MCPToolResult:
        if not self.api_key:
            return MCPToolResult(success=False, error="Etsy API key not configured")
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                match tool_name:
                    case "get_shop":
                        r = await client.get(
                            f"{ETSY_API}/application/shops/{params['shop_id']}",
                            headers=self._headers,
                        )
                        r.raise_for_status()
                        return MCPToolResult(success=True, data=r.json())

                    case "list_listings":
                        shop_id = params["shop_id"]
                        r = await client.get(
                            f"{ETSY_API}/application/shops/{shop_id}/listings/active",
                            headers=self._headers,
                            params={"limit": params.get("limit", 25)},
                        )
                        r.raise_for_status()
                        return MCPToolResult(success=True, data=r.json())

                    case "get_listing":
                        r = await client.get(
                            f"{ETSY_API}/application/listings/{params['listing_id']}",
                            headers=self._headers,
                        )
                        r.raise_for_status()
                        return MCPToolResult(success=True, data=r.json())

                    case "create_listing":
                        shop_id = params.pop("shop_id")
                        r = await client.post(
                            f"{ETSY_API}/application/shops/{shop_id}/listings",
                            headers={**self._headers, "Content-Type": "application/json"},
                            json=params,
                        )
                        r.raise_for_status()
                        return MCPToolResult(success=True, data=r.json())

                    case "update_listing":
                        listing_id = params.pop("listing_id")
                        shop_id = params.pop("shop_id")
                        r = await client.patch(
                            f"{ETSY_API}/application/shops/{shop_id}/listings/{listing_id}",
                            headers={**self._headers, "Content-Type": "application/json"},
                            json=params,
                        )
                        r.raise_for_status()
                        return MCPToolResult(success=True, data=r.json())

                    case _:
                        return MCPToolResult(success=False, error=f"Unknown tool: {tool_name}")

        except httpx.HTTPStatusError as exc:
            return MCPToolResult(success=False, error=f"Etsy API error: {exc.response.status_code}")
        except Exception as exc:
            logger.error("Etsy MCP error", tool=tool_name, error=str(exc))
            return MCPToolResult(success=False, error=str(exc))
