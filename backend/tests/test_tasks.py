"""Task queue tests."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


TASK_PAYLOAD = {
    "title": "Test task",
    "description": "A task created by tests",
    "priority": 5,
}


@pytest.mark.asyncio
async def test_create_task(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.post("/api/v1/tasks/", json=TASK_PAYLOAD, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test task"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_list_tasks(client: AsyncClient, auth_headers: dict) -> None:
    await client.post("/api/v1/tasks/", json=TASK_PAYLOAD, headers=auth_headers)
    response = await client.get("/api/v1/tasks/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_task(client: AsyncClient, auth_headers: dict) -> None:
    create = await client.post("/api/v1/tasks/", json=TASK_PAYLOAD, headers=auth_headers)
    task_id = create.json()["id"]
    response = await client.get(f"/api/v1/tasks/{task_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == task_id


@pytest.mark.asyncio
async def test_cancel_task(client: AsyncClient, auth_headers: dict) -> None:
    create = await client.post("/api/v1/tasks/", json=TASK_PAYLOAD, headers=auth_headers)
    task_id = create.json()["id"]
    response = await client.post(
        f"/api/v1/tasks/{task_id}/cancel", headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_task_filter_by_status(client: AsyncClient, auth_headers: dict) -> None:
    await client.post("/api/v1/tasks/", json=TASK_PAYLOAD, headers=auth_headers)
    response = await client.get(
        "/api/v1/tasks/?status=pending", headers=auth_headers
    )
    assert response.status_code == 200
    items = response.json()["items"]
    assert all(t["status"] == "pending" for t in items)


@pytest.mark.asyncio
async def test_task_priority_validation(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.post(
        "/api/v1/tasks/",
        json={**TASK_PAYLOAD, "priority": 99},
        headers=auth_headers,
    )
    assert response.status_code == 422
