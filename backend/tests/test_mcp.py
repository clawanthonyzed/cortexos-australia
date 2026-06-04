"""MCP registry tests."""
from __future__ import annotations

import pytest

from app.mcp.registry import MCPRegistry


def test_registry_lists_registered_servers() -> None:
    registry = MCPRegistry()
    servers = registry.list_servers()
    assert isinstance(servers, list)


def test_registry_get_known_server() -> None:
    registry = MCPRegistry()
    # GitHub is always registered
    server = registry.get("github")
    assert server is not None
    assert server.name == "github"


def test_registry_get_unknown_returns_none() -> None:
    registry = MCPRegistry()
    server = registry.get("nonexistent_mcp_xyz")
    assert server is None


def test_registry_register_custom_server() -> None:
    from app.mcp.base import BaseMCPServer

    class MockMCP(BaseMCPServer):
        name = "mock_mcp"
        description = "Mock MCP for testing"

        async def execute(self, tool: str, params: dict) -> dict:
            return {"result": "ok"}

        def available_tools(self) -> list[str]:
            return ["tool_a", "tool_b"]

    registry = MCPRegistry()
    registry.register(MockMCP())
    server = registry.get("mock_mcp")
    assert server is not None
    assert "tool_a" in server.available_tools()


def test_etsy_mcp_available_tools() -> None:
    from app.mcp.etsy import EtsyMCP
    mcp = EtsyMCP()
    tools = mcp.available_tools()
    assert "list_products" in tools
    assert "create_listing" in tools


def test_gumroad_mcp_available_tools() -> None:
    from app.mcp.gumroad import GumroadMCP
    mcp = GumroadMCP()
    tools = mcp.available_tools()
    assert "list_products" in tools
    assert "create_product" in tools


def test_lemon_squeezy_mcp_available_tools() -> None:
    from app.mcp.lemon_squeezy import LemonSqueezyMCP
    mcp = LemonSqueezyMCP()
    tools = mcp.available_tools()
    assert "list_products" in tools
