"""Workflow CRUD + execution tests."""
from __future__ import annotations

import json
import pytest
from httpx import AsyncClient


WORKFLOW_PAYLOAD = {
    "name": "Test workflow",
    "description": "Workflow created by tests",
    "trigger_type": "manual",
    "graph_json": json.dumps({
        "nodes": [
            {"id": "start", "type": "start", "position": {"x": 0, "y": 0}, "data": {}},
            {"id": "end", "type": "end", "position": {"x": 200, "y": 0}, "data": {}},
        ],
        "edges": [
            {"id": "e1", "source": "start", "target": "end"},
        ],
    }),
}


@pytest.mark.asyncio
async def test_create_workflow(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.post("/api/v1/workflows/", json=WORKFLOW_PAYLOAD, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test workflow"
    assert data["status"] == "inactive"


@pytest.mark.asyncio
async def test_list_workflows(client: AsyncClient, auth_headers: dict) -> None:
    await client.post("/api/v1/workflows/", json=WORKFLOW_PAYLOAD, headers=auth_headers)
    response = await client.get("/api/v1/workflows/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


@pytest.mark.asyncio
async def test_get_workflow(client: AsyncClient, auth_headers: dict) -> None:
    create = await client.post("/api/v1/workflows/", json=WORKFLOW_PAYLOAD, headers=auth_headers)
    wf_id = create.json()["id"]
    response = await client.get(f"/api/v1/workflows/{wf_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == wf_id


@pytest.mark.asyncio
async def test_update_workflow(client: AsyncClient, auth_headers: dict) -> None:
    create = await client.post("/api/v1/workflows/", json=WORKFLOW_PAYLOAD, headers=auth_headers)
    wf_id = create.json()["id"]
    response = await client.patch(
        f"/api/v1/workflows/{wf_id}",
        json={"name": "Updated workflow"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated workflow"


@pytest.mark.asyncio
async def test_delete_workflow(client: AsyncClient, auth_headers: dict) -> None:
    create = await client.post("/api/v1/workflows/", json=WORKFLOW_PAYLOAD, headers=auth_headers)
    wf_id = create.json()["id"]
    response = await client.delete(f"/api/v1/workflows/{wf_id}", headers=auth_headers)
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_trigger_workflow(client: AsyncClient, auth_headers: dict) -> None:
    create = await client.post("/api/v1/workflows/", json=WORKFLOW_PAYLOAD, headers=auth_headers)
    wf_id = create.json()["id"]
    response = await client.post(
        f"/api/v1/workflows/{wf_id}/trigger",
        json={"input": {"test": True}},
        headers=auth_headers,
    )
    # Either queued or completed for a trivial start→end workflow
    assert response.status_code in (200, 202)
