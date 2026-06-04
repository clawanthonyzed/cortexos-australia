"""X/Twitter MCP — tweet management and trend monitoring."""
from __future__ import annotations

from typing import Any

import structlog

from app.mcp.base import BaseMCPServer, MCPToolResult

logger = structlog.get_logger(__name__)


class TwitterMCP(BaseMCPServer):
    name = "twitter"
    description = "X/Twitter — post tweets, monitor mentions, search trends"

    def __init__(self, bearer_token: str = "", api_key: str = "", api_secret: str = "") -> None:
        self.bearer_token = bearer_token
        self.api_key = api_key
        self.api_secret = api_secret

    async def health_check(self) -> bool:
        return bool(self.bearer_token)

    async def list_tools(self) -> list[dict[str, Any]]:
        return [
            {"name": "post_tweet", "description": "Post a tweet"},
            {"name": "search_tweets", "description": "Search recent tweets"},
            {"name": "get_user_tweets", "description": "Get tweets from a user"},
            {"name": "get_trending", "description": "Get trending topics"},
        ]

    async def call_tool(self, tool_name: str, params: dict[str, Any]) -> MCPToolResult:
        if not self.bearer_token:
            return MCPToolResult(
                success=False,
                error="Twitter/X API credentials not configured",
            )
        import httpx
        headers = {"Authorization": f"Bearer {self.bearer_token}"}
        twitter_api = "https://api.twitter.com/2"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                match tool_name:
                    case "search_tweets":
                        r = await client.get(
                            f"{twitter_api}/tweets/search/recent",
                            headers=headers,
                            params={
                                "query": params["query"],
                                "max_results": min(params.get("max_results", 10), 100),
                                "tweet.fields": "author_id,created_at,public_metrics",
                            },
                        )
                        r.raise_for_status()
                        return MCPToolResult(success=True, data=r.json())

                    case "post_tweet":
                        r = await client.post(
                            f"{twitter_api}/tweets",
                            headers={**headers, "Content-Type": "application/json"},
                            json={"text": params["text"]},
                        )
                        r.raise_for_status()
                        return MCPToolResult(success=True, data=r.json())

                    case "get_user_tweets":
                        user_id = params["user_id"]
                        r = await client.get(
                            f"{twitter_api}/users/{user_id}/tweets",
                            headers=headers,
                            params={"max_results": min(params.get("max_results", 10), 100)},
                        )
                        r.raise_for_status()
                        return MCPToolResult(success=True, data=r.json())

                    case _:
                        return MCPToolResult(success=False, error=f"Unknown tool: {tool_name}")

        except Exception as exc:
            logger.error("Twitter MCP error", tool=tool_name, error=str(exc))
            return MCPToolResult(success=False, error=str(exc))
