"""Base MCP server interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MCPToolResult:
    success: bool
    data: Any = None
    error: str | None = None
    raw: Any = field(default=None, repr=False)


class BaseMCPServer(ABC):
    """Abstract base for all MCP server integrations."""

    name: str = "base"
    description: str = ""

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the MCP server is reachable and authenticated."""

    @abstractmethod
    async def list_tools(self) -> list[dict[str, Any]]:
        """Return a list of available tool definitions."""

    @abstractmethod
    async def call_tool(self, tool_name: str, params: dict[str, Any]) -> MCPToolResult:
        """Invoke a tool on the MCP server."""

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name}>"
