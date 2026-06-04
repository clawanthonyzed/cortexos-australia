"""Health, readiness, and metrics endpoints."""
from __future__ import annotations

import time
from typing import Any

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db

logger = structlog.get_logger(__name__)
router = APIRouter()

_START_TIME = time.time()


@router.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Basic liveness check."""
    return {"status": "ok", "service": "CortexOS Australia"}


@router.get("/ready", tags=["health"])
async def readiness(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """
    Readiness check — verifies DB connectivity.
    Returns 200 if all critical services are reachable.
    """
    checks: dict[str, Any] = {}

    # DB check
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {exc}"

    # Redis check
    try:
        import redis.asyncio as aioredis
        from app.config import settings
        r = aioredis.from_url(settings.redis_url)
        await r.ping()
        await r.aclose()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = f"error: {exc}"

    all_ok = all(v == "ok" for v in checks.values())

    return {
        "status": "ready" if all_ok else "degraded",
        "checks": checks,
        "uptime_seconds": round(time.time() - _START_TIME, 1),
    }


@router.get("/metrics", tags=["health"])
async def metrics() -> dict[str, Any]:
    """Prometheus-style metrics endpoint."""
    try:
        from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
        from fastapi.responses import Response
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
    except ImportError:
        return {"error": "prometheus_client not installed"}
