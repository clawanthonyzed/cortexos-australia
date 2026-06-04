"""Discord MCP — send messages, manage channels via Discord webhooks."""
from __future__ import annotations

from typing import Any

import httpx
import structlog

from app.mcp.base import BaseMCPServer, MCPToolResult

logger = structlog.get_logger(__name__)


class DiscordMCP(BaseMCPServer):
    name = "discord"
    description = "Discord — send messages via webhooks, manage server interactions"

    def __init__(self, webhook_url: str = "") -> None:
        self.webhook_url = webhook_url

    async def health_check(self) -> bool:
        return bool(self.webhook_url)

    async def list_tools(self) -> list[dict[str, Any]]:
        return [
            {"name": "send_message", "description": "Send a message to a Discord webhook"},
            {"name": "send_embed", "description": "Send a rich embed message"},
        ]

    async def call_tool(self, tool_name: str, params: dict[str, Any]) -> MCPToolResult:
        webhook_url = params.get("webhook_url") or self.webhook_url
        if not webhook_url:
            return MCPToolResult(success=False, error="Discord webhook URL not configured")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                match tool_name:
                    case "send_message":
                        r = await client.post(
                            webhook_url,
                            json={"content": params.get("content", ""), "username": params.get("username", "CortexOS")},
                        )
                        r.raise_for_status()
                        return MCPToolResult(success=True, data={"status": "sent"})

                    case "send_embed":
                        embed = {
                            "title": params.get("title", ""),
                            "description": params.get("description", ""),
                            "color": params.get("color", 0x00ff00),
                            "fields": params.get("fields", []),
                        }
                        r = await client.post(
                            webhook_url,
                            json={"embeds": [embed], "username": params.get("username", "CortexOS")},
                        )
                        r.raise_for_status()
                        return MCPToolResult(success=True, data={"status": "sent"})

                    case _:
                        return MCPToolResult(success=False, error=f"Unknown tool: {tool_name}")

        except Exception as exc:
            logger.error("Discord MCP error", tool=tool_name, error=str(exc))
            return MCPToolResult(success=False, error=str(exc))
