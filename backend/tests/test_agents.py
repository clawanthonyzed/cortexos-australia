"""Agent CRUD + execution tests."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


AGENT_PAYLOAD = {
    "name": "test-agent",
    "purpose": "Test agent for unit tests",
    "model_provider": "claude",
    "model_name": "claude-sonnet-4-6",
    "temperature": 0.7,
    "max_tokens": 2048,
    "agent_type": "custom",
}


@pytest.mark.asyncio
async def test_create_agent(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.post("/api/v1/agents/", json=AGENT_PAYLOAD, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test-agent"
    assert data["status"] == "idle"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_agents(client: AsyncClient, auth_headers: dict) -> None:
    # Create one first
    await client.post("/api/v1/agents/", json=AGENT_PAYLOAD, headers=auth_headers)
    response = await client.get("/api/v1/agents/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_agent(client: AsyncClient, auth_headers: dict) -> None:
    create = await client.post("/api/v1/agents/", json=AGENT_PAYLOAD, headers=auth_headers)
    agent_id = create.json()["id"]
    response = await client.get(f"/api/v1/agents/{agent_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == agent_id


@pytest.mark.asyncio
async def test_get_agent_not_found(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.get(
        "/api/v1/agents/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_agent(client: AsyncClient, auth_headers: dict) -> None:
    create = await client.post("/api/v1/agents/", json=AGENT_PAYLOAD, headers=auth_headers)
    agent_id = create.json()["id"]
    response = await client.patch(
        f"/api/v1/agents/{agent_id}",
        json={"purpose": "Updated purpose"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["purpose"] == "Updated purpose"


@pytest.mark.asyncio
async def test_delete_agent(client: AsyncClient, auth_headers: dict) -> None:
    create = await client.post("/api/v1/agents/", json=AGENT_PAYLOAD, headers=auth_headers)
    agent_id = create.json()["id"]
    response = await client.delete(f"/api/v1/agents/{agent_id}", headers=auth_headers)
    assert response.status_code == 204
    # Verify gone
    get = await client.get(f"/api/v1/agents/{agent_id}", headers=auth_headers)
    assert get.status_code == 404


@pytest.mark.asyncio
async def test_duplicate_agent_name(client: AsyncClient, auth_headers: dict) -> None:
    await client.post("/api/v1/agents/", json=AGENT_PAYLOAD, headers=auth_headers)
    response = await client.post("/api/v1/agents/", json=AGENT_PAYLOAD, headers=auth_headers)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_agent_pagination(client: AsyncClient, auth_headers: dict) -> None:
    for i in range(5):
        payload = {**AGENT_PAYLOAD, "name": f"agent-pagination-{i}"}
        await client.post("/api/v1/agents/", json=payload, headers=auth_headers)
    response = await client.get(
        "/api/v1/agents/?page=1&page_size=2", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) <= 2
