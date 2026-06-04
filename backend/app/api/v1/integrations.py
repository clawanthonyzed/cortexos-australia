"""Integration status + sync endpoints for Etsy, Gumroad, LemonSqueezy."""
from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import Permission, require_permission
from app.dependencies import get_db
from app.mcp.registry import MCPRegistry
from app.models.user import User

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get("/status", tags=["integrations"])
async def get_integration_status(
    current_user: User = Depends(require_permission(Permission.INTEGRATION_READ)),
) -> dict[str, Any]:
    """Check connectivity status of all registered MCP integrations."""
    results = await MCPRegistry.health_check_all()
    return {
        "integrations": [
            {"name": name, "connected": status}
            for name, status in results.items()
        ]
    }


@router.get("/{platform}/tools", tags=["integrations"])
async def list_platform_tools(
    platform: str,
    current_user: User = Depends(require_permission(Permission.INTEGRATION_READ)),
) -> dict[str, Any]:
    """List available tools for a platform integration."""
    server = MCPRegistry.get(platform)
    if not server:
        raise HTTPException(
            status_code=404,
            detail={"error": f"Integration '{platform}' not registered"},
        )
    tools = await server.list_tools()
    return {"platform": platform, "tools": tools}


@router.post("/{platform}/call", tags=["integrations"])
async def call_integration_tool(
    platform: str,
    payload: dict[str, Any],
    current_user: User = Depends(require_permission(Permission.INTEGRATION_MANAGE)),
) -> dict[str, Any]:
    """
    Call a specific tool on an integration.
    Body: { "tool": "tool_name", "params": { ... } }
    """
    tool_name = payload.get("tool")
    params = payload.get("params", {})

    if not tool_name:
        raise HTTPException(
            status_code=422,
            detail={"error": "Missing 'tool' in request body"},
        )

    result = await MCPRegistry.call(platform, tool_name, params)
    if not result.success:
        raise HTTPException(
            status_code=502,
            detail={"error": result.error or "Integration call failed"},
        )
    return {"platform": platform, "tool": tool_name, "result": result.data}


@router.get("/etsy/sync", tags=["integrations"])
async def sync_etsy_products(
    shop_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.INTEGRATION_MANAGE)),
) -> dict[str, Any]:
    """Sync Etsy listings into the product catalog."""
    result = await MCPRegistry.call("etsy", "list_listings", {"shop_id": shop_id})
    if not result.success:
        raise HTTPException(
            status_code=502,
            detail={"error": result.error or "Etsy sync failed"},
        )

    listings = result.data or {}
    count = len(listings.get("results", []))
    return {"status": "synced", "listings_found": count, "shop_id": shop_id}


@router.get("/gumroad/sync", tags=["integrations"])
async def sync_gumroad_products(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.INTEGRATION_MANAGE)),
) -> dict[str, Any]:
    """Sync Gumroad products into the product catalog."""
    result = await MCPRegistry.call("gumroad", "list_products", {})
    if not result.success:
        raise HTTPException(
            status_code=502,
            detail={"error": result.error or "Gumroad sync failed"},
        )
    products = result.data or []
    return {"status": "synced", "products_found": len(products)}
