"""Health endpoint tests."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_ok(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ok", "degraded")
    assert "version" in data
    assert "environment" in data


@pytest.mark.asyncio
async def test_readiness(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health/ready")
    assert response.status_code in (200, 503)


@pytest.mark.asyncio
async def test_metrics(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "uptime_seconds" in data
    assert "request_count" in data
