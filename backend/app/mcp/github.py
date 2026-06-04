"""GitHub MCP — repository management, issues, PRs."""
from __future__ import annotations

from typing import Any

import httpx
import structlog

from app.mcp.base import BaseMCPServer, MCPToolResult

logger = structlog.get_logger(__name__)

GITHUB_API = "https://api.github.com"


class GitHubMCP(BaseMCPServer):
    name = "github"
    description = "GitHub repository management — issues, PRs, files, releases"

    def __init__(self, token: str) -> None:
        self.token = token
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def health_check(self) -> bool:
        if not self.token:
            return False
        try:
            async with httpx.AsyncClient(timeout=10.0) as c:
                r = await c.get(f"{GITHUB_API}/user", headers=self._headers)
                return r.status_code == 200
        except Exception:
            return False

    async def list_tools(self) -> list[dict[str, Any]]:
        return [
            {"name": "list_repos", "description": "List repositories for authenticated user"},
            {"name": "create_issue", "description": "Create a GitHub issue"},
            {"name": "list_issues", "description": "List issues in a repository"},
            {"name": "create_file", "description": "Create or update a file in a repository"},
            {"name": "get_file", "description": "Get file content from a repository"},
            {"name": "create_pr", "description": "Create a pull request"},
        ]

    async def call_tool(self, tool_name: str, params: dict[str, Any]) -> MCPToolResult:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                match tool_name:
                    case "list_repos":
                        r = await client.get(
                            f"{GITHUB_API}/user/repos",
                            headers=self._headers,
                            params={"per_page": params.get("per_page", 30), "sort": "updated"},
                        )
                        r.raise_for_status()
                        return MCPToolResult(success=True, data=r.json())

                    case "create_issue":
                        owner = params["owner"]
                        repo = params["repo"]
                        r = await client.post(
                            f"{GITHUB_API}/repos/{owner}/{repo}/issues",
                            headers=self._headers,
                            json={
                                "title": params["title"],
                                "body": params.get("body", ""),
                                "labels": params.get("labels", []),
                            },
                        )
                        r.raise_for_status()
                        return MCPToolResult(success=True, data=r.json())

                    case "list_issues":
                        owner, repo = params["owner"], params["repo"]
                        r = await client.get(
                            f"{GITHUB_API}/repos/{owner}/{repo}/issues",
                            headers=self._headers,
                            params={"state": params.get("state", "open"), "per_page": 50},
                        )
                        r.raise_for_status()
                        return MCPToolResult(success=True, data=r.json())

                    case "create_file":
                        import base64
                        owner, repo = params["owner"], params["repo"]
                        path = params["path"]
                        content_b64 = base64.b64encode(
                            params["content"].encode()
                        ).decode()
                        payload: dict[str, Any] = {
                            "message": params.get("message", "Update file"),
                            "content": content_b64,
                        }
                        if sha := params.get("sha"):
                            payload["sha"] = sha
                        r = await client.put(
                            f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}",
                            headers=self._headers,
                            json=payload,
                        )
                        r.raise_for_status()
                        return MCPToolResult(success=True, data=r.json())

                    case "get_file":
                        owner, repo = params["owner"], params["repo"]
                        r = await client.get(
                            f"{GITHUB_API}/repos/{owner}/{repo}/contents/{params['path']}",
                            headers=self._headers,
                        )
                        r.raise_for_status()
                        return MCPToolResult(success=True, data=r.json())

                    case "create_pr":
                        owner, repo = params["owner"], params["repo"]
                        r = await client.post(
                            f"{GITHUB_API}/repos/{owner}/{repo}/pulls",
                            headers=self._headers,
                            json={
                                "title": params["title"],
                                "head": params["head"],
                                "base": params.get("base", "main"),
                                "body": params.get("body", ""),
                            },
                        )
                        r.raise_for_status()
                        return MCPToolResult(success=True, data=r.json())

                    case _:
                        return MCPToolResult(success=False, error=f"Unknown tool: {tool_name}")

        except httpx.HTTPStatusError as exc:
            return MCPToolResult(success=False, error=f"GitHub API error: {exc.response.status_code} {exc.response.text[:200]}")
        except Exception as exc:
            logger.error("GitHub MCP error", tool=tool_name, error=str(exc))
            return MCPToolResult(success=False, error=str(exc))
