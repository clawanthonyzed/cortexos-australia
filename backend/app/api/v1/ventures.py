"""Venture registry — multi-tenant workspace CRUD + per-venture health (SPEC-COS-04)."""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import Permission, require_permission
from app.dependencies import get_db
from app.models.user import User
from app.models.venture import Venture
from app.schemas.venture import VentureCreate, VentureRead
from app.services.venture_health import compute_venture_health

router = APIRouter()


def _error(msg: str, detail: Any = None) -> dict[str, Any]:
    return {"error": msg, "detail": detail or {}}


@router.get("", response_model=dict[str, Any], tags=["ventures"])
async def list_ventures(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.VENTURE_READ)),
) -> dict[str, Any]:
    """List all ventures in the empire registry."""
    result = await db.execute(select(Venture).order_by(Venture.name))
    ventures = result.scalars().all()
    return {
        "items": [VentureRead.model_validate(v) for v in ventures],
        "total": len(ventures),
    }


@router.post("", response_model=VentureRead, status_code=status.HTTP_201_CREATED, tags=["ventures"])
async def create_venture(
    payload: VentureCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.VENTURE_WRITE)),
) -> VentureRead:
    """Register a new venture."""
    existing = await db.execute(select(Venture).where(Venture.slug == payload.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_error("Venture slug already in use"),
        )

    venture = Venture(
        slug=payload.slug,
        name=payload.name,
        manager_name=payload.manager_name,
        category=payload.category,
    )
    db.add(venture)
    await db.flush()
    await db.refresh(venture)
    return VentureRead.model_validate(venture)


@router.get("/{venture_id}/health", response_model=dict[str, Any], tags=["ventures"])
async def venture_health(
    venture_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.VENTURE_READ)),
) -> dict[str, Any]:
    """Health score for a single venture (agents joined via venture_id FK)."""
    venture = await db.get(Venture, venture_id)
    if not venture:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_error("Venture not found"))
    return await compute_venture_health(db, venture)

@router.get("/registry", response_model=dict, tags=["ventures"])
async def list_ventures_from_registry(
    current_user: User = Depends(require_permission(Permission.VENTURE_READ)),
) -> dict:
    """List all ventures from the empire registry.json (live data, no DB needed)."""
    import json as _json
    import os as _os

    registry_path = "/opt/openclaw/orchestration/registry.json"
    if not _os.path.exists(registry_path):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "Registry not available"},
        )

    with open(registry_path) as f:
        data = _json.load(f)

    agents = data.get("agents", [])
    ventures: dict = {}

    for agent in agents:
        venture_slug = agent.get("venture", "")
        if not venture_slug or agent.get("is_specialist"):
            continue
        if venture_slug not in ventures:
            ventures[venture_slug] = {
                "id": venture_slug,
                "name": venture_slug.replace("-", " ").title(),
                "slug": venture_slug,
                "manager": None,
                "workers": [],
                "status": "active",
                "revenue_target": None,
            }
        if ventures[venture_slug]["manager"] is None:
            ventures[venture_slug]["manager"] = agent["name"]
        else:
            ventures[venture_slug]["workers"].append(agent["name"])

    items = sorted(ventures.values(), key=lambda v: v["name"])
    return {
        "items": items,
        "total": len(items),
        "source": "registry.json",
        "built": data.get("built"),
    }
