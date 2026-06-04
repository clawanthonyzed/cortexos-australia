"""MCPRegistry — register and look up MCP server integrations."""
from __future__ import annotations

from typing import Any

import structlog

from app.mcp.base import BaseMCPServer, MCPToolResult

logger = structlog.get_logger(__name__)

_REGISTRY: dict[str, BaseMCPServer] = {}


class MCPRegistry:
    """
    Singleton-style registry for MCP server integrations.
    Servers are registered at startup and looked up by name.
    """

    @staticmethod
    def register(server: BaseMCPServer) -> None:
        """Register an MCP server instance."""
        _REGISTRY[server.name] = server
        logger.info("MCP server registered", name=server.name)

    @staticmethod
    def get(name: str) -> BaseMCPServer | None:
        """Look up an MCP server by name."""
        return _REGISTRY.get(name)

    @staticmethod
    def list_servers() -> list[dict[str, Any]]:
        """Return info about all registered servers."""
        return [
            {
                "name": name,
                "description": server.description,
                "class": server.__class__.__name__,
            }
            for name, server in _REGISTRY.items()
        ]

    @staticmethod
    async def call(
        server_name: str,
        tool_name: str,
        params: dict[str, Any] | None = None,
    ) -> MCPToolResult:
        """Call a tool on a named MCP server."""
        server = _REGISTRY.get(server_name)
        if not server:
            return MCPToolResult(
                success=False,
                error=f"MCP server '{server_name}' not registered",
            )
        return await server.call_tool(tool_name, params or {})

    @staticmethod
    async def health_check_all() -> dict[str, bool]:
        """Health-check all registered MCP servers."""
        results: dict[str, bool] = {}
        for name, server in _REGISTRY.items():
            try:
                results[name] = await server.health_check()
            except Exception as exc:
                logger.warning("MCP health check failed", server=name, error=str(exc))
                results[name] = False
        return results


def init_mcp_registry() -> None:
    """Import and register all MCP servers at startup."""
    from app.config import settings
    from app.mcp.github import GitHubMCP
    from app.mcp.etsy import EtsyMCP
    from app.mcp.gumroad import GumroadMCP
    from app.mcp.lemon_squeezy import LemonSqueezeMCP
    from app.mcp.google_drive import GoogleDriveMCP
    from app.mcp.gmail import GmailMCP
    from app.mcp.discord import DiscordMCP
    from app.mcp.reddit import RedditMCP
    from app.mcp.twitter import TwitterMCP
    from app.mcp.stripe import StripeMCP

    servers: list[BaseMCPServer] = [
        GitHubMCP(token=settings.github_token),
        EtsyMCP(api_key=settings.etsy_api_key, shared_secret=settings.etsy_shared_secret),
        GumroadMCP(access_token=settings.gumroad_access_token),
        LemonSqueezeMCP(api_key=settings.lemonsqueezy_api_key),
        GoogleDriveMCP(),
        GmailMCP(),
        DiscordMCP(),
        RedditMCP(),
        TwitterMCP(),
        StripeMCP(),
    ]

    for server in servers:
        MCPRegistry.register(server)

    logger.info("MCP registry initialised", count=len(servers))
