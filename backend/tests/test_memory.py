"""Memory store/recall/prune tests."""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_list_memories(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.get("/api/v1/memory/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


@pytest.mark.asyncio
async def test_search_memory(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.post(
        "/api/v1/memory/search",
        json={"query": "revenue forecast", "limit": 5},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert isinstance(data["results"], list)


@pytest.mark.asyncio
async def test_add_memory(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.post(
        "/api/v1/memory/",
        json={
            "content": "The user prefers concise reports",
            "memory_type": "long_term",
            "tags": ["preference", "reports"],
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data


@pytest.mark.asyncio
async def test_delete_memory(client: AsyncClient, auth_headers: dict) -> None:
    create = await client.post(
        "/api/v1/memory/",
        json={"content": "Temporary memory", "memory_type": "short_term", "tags": []},
        headers=auth_headers,
    )
    mem_id = create.json()["id"]
    response = await client.delete(f"/api/v1/memory/{mem_id}", headers=auth_headers)
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_memory_stats(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.get("/api/v1/memory/stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_items" in data
    assert "by_type" in data
