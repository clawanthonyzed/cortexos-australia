"""Google Drive MCP — file management stub (OAuth flow required for full use)."""
from __future__ import annotations

from typing import Any

import structlog

from app.mcp.base import BaseMCPServer, MCPToolResult

logger = structlog.get_logger(__name__)


class GoogleDriveMCP(BaseMCPServer):
    name = "google_drive"
    description = "Google Drive file management — list, read, create, upload"

    async def health_check(self) -> bool:
        # Would check OAuth token validity
        return False  # Requires OAuth setup

    async def list_tools(self) -> list[dict[str, Any]]:
        return [
            {"name": "list_files", "description": "List files in Google Drive"},
            {"name": "get_file", "description": "Get file metadata and content"},
            {"name": "create_file", "description": "Create a new Google Doc/Sheet"},
            {"name": "upload_file", "description": "Upload a file to Drive"},
            {"name": "share_file", "description": "Share a file with a user"},
        ]

    async def call_tool(self, tool_name: str, params: dict[str, Any]) -> MCPToolResult:
        return MCPToolResult(
            success=False,
            error="Google Drive requires OAuth2 setup. Configure credentials.json first.",
        )
