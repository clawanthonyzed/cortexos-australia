"""Gmail MCP — send/read emails via Gmail API."""
from __future__ import annotations

from typing import Any

import structlog

from app.mcp.base import BaseMCPServer, MCPToolResult

logger = structlog.get_logger(__name__)


class GmailMCP(BaseMCPServer):
    name = "gmail"
    description = "Gmail — send emails, read inbox, manage labels"

    async def health_check(self) -> bool:
        return False  # Requires OAuth2

    async def list_tools(self) -> list[dict[str, Any]]:
        return [
            {"name": "send_email", "description": "Send an email via Gmail"},
            {"name": "list_messages", "description": "List inbox messages"},
            {"name": "get_message", "description": "Get a specific message"},
            {"name": "search_messages", "description": "Search messages with query"},
        ]

    async def call_tool(self, tool_name: str, params: dict[str, Any]) -> MCPToolResult:
        return MCPToolResult(
            success=False,
            error="Gmail requires OAuth2 setup. Configure Google credentials first.",
        )
