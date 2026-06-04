"""Reddit MCP — subreddit monitoring and post management."""
from __future__ import annotations

from typing import Any

import httpx
import structlog

from app.mcp.base import BaseMCPServer, MCPToolResult

logger = structlog.get_logger(__name__)

REDDIT_API = "https://www.reddit.com"


class RedditMCP(BaseMCPServer):
    name = "reddit"
    description = "Reddit — monitor subreddits, search posts, track trends"

    def __init__(self, client_id: str = "", client_secret: str = "", user_agent: str = "CortexOS/1.0") -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as c:
                r = await c.get(
                    f"{REDDIT_API}/r/all/hot.json",
                    headers={"User-Agent": self.user_agent},
                    params={"limit": 1},
                )
                return r.status_code == 200
        except Exception:
            return False

    async def list_tools(self) -> list[dict[str, Any]]:
        return [
            {"name": "get_hot_posts", "description": "Get hot posts from a subreddit"},
            {"name": "search_reddit", "description": "Search Reddit for posts/comments"},
            {"name": "get_subreddit_info", "description": "Get subreddit metadata"},
        ]

    async def call_tool(self, tool_name: str, params: dict[str, Any]) -> MCPToolResult:
        headers = {"User-Agent": self.user_agent}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                match tool_name:
                    case "get_hot_posts":
                        subreddit = params.get("subreddit", "all")
                        r = await client.get(
                            f"{REDDIT_API}/r/{subreddit}/hot.json",
                            headers=headers,
                            params={"limit": params.get("limit", 25)},
                        )
                        r.raise_for_status()
                        posts = r.json()["data"]["children"]
                        return MCPToolResult(
                            success=True,
                            data=[p["data"] for p in posts],
                        )

                    case "search_reddit":
                        r = await client.get(
                            f"{REDDIT_API}/search.json",
                            headers=headers,
                            params={
                                "q": params["query"],
                                "sort": params.get("sort", "relevance"),
                                "limit": params.get("limit", 25),
                                "type": params.get("type", "link"),
                            },
                        )
                        r.raise_for_status()
                        results = r.json()["data"]["children"]
                        return MCPToolResult(
                            success=True,
                            data=[p["data"] for p in results],
                        )

                    case "get_subreddit_info":
                        subreddit = params["subreddit"]
                        r = await client.get(
                            f"{REDDIT_API}/r/{subreddit}/about.json",
                            headers=headers,
                        )
                        r.raise_for_status()
                        return MCPToolResult(success=True, data=r.json()["data"])

                    case _:
                        return MCPToolResult(success=False, error=f"Unknown tool: {tool_name}")

        except Exception as exc:
            logger.error("Reddit MCP error", tool=tool_name, error=str(exc))
            return MCPToolResult(success=False, error=str(exc))
