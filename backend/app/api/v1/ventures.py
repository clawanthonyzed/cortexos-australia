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


# ── Cockpit: one-click work orders sent to the venture manager via the A2A hub ──────
# The executor daemon (a2a_executor.py) picks them up; while Anthropic credit is frozen it
# runs them as $0 free-route drafts, saves the deliverable to GitHub and writes the result
# back onto the EmpireOS task, so the Tasks tab updates live.
A2A_HUB = "http://172.25.0.1:8400"

PLAYBOOKS: dict[str, list[dict[str, str]]] = {
    "cudan-studio": [
        {"id": "gbp-week", "title": "This week's Google Business Profile post + 3 Instagram captions",
         "brief": ("Write one Google Business Profile post (under 1,500 characters, with a 'Book' call to action) and "
                   "3 Instagram captions for Cudan Studio this week. Facts you may use, nothing else: photography, video "
                   "and content studio for hire in Kenwick WA, 15 minutes from the Perth CBD; all Godox and Neewer "
                   "lighting included; 6m seamless cyclorama, black screen, green screen, stage with arch; free parking; "
                   "$50/hr weekdays, $60/hr weekends; 2-Hour Creator Block $100 weekdays. Target searches: photography "
                   "studio hire Perth, cyclorama studio Perth, studio hire south of the river. Australian English.")},
        {"id": "south-of-river", "title": "Draft the 'Studio Hire South of the River' landing page",
         "brief": ("Draft full page copy for a Cudan Studio landing page targeting 'studio hire Kenwick', 'studio hire "
                   "Cannington' and 'photography studio south of the river Perth': H1, 3 short sections, 4 FAQs, call to "
                   "action. Use only these facts: Kenwick WA, 15 min from CBD, lighting included, 6m cyclorama, black "
                   "and green screen, stage with arch, free parking, $50/hr weekday, $60/hr weekend.")},
        {"id": "review-replies", "title": "Write 6 Google review reply templates",
         "brief": "Write 6 short, warm reply templates for Cudan Studio Google reviews (2 for 5-star, 2 for 3-4 star, 2 for 1-2 star). No arguing, invite unhappy clients to email info@cudanstudio.com.au."},
    ],
    "data-forge": [
        {"id": "landing-copy", "title": "API landing page copy + pricing tiers",
         "brief": ("Write landing page copy and 3 pricing tiers for DataForge's Australian Public Holiday & Business Day "
                   "API. Facts: 2026 dataset covers NSW (12 holidays), VIC (14) and WA (13), validated with 0 schema "
                   "errors; NSW/VIC data is CC BY 3.0 AU licensed; WA dates are statutory. Buyers: payroll, logistics "
                   "and e-commerce shipping estimators. Do not claim states that are not covered.")},
        {"id": "next-states", "title": "Plan QLD, SA, TAS, NT and ACT coverage",
         "brief": "Write a research plan for adding QLD, SA, TAS, NT and ACT public holidays to DataForge: which official portals to check, what licence evidence to capture, and the order to do them in."},
    ],
}
GENERIC_PLAYBOOK = {"id": "next-deliverable", "title": "Draft this venture's next most valuable deliverable",
                    "brief": "Propose and draft the single most valuable next deliverable for this venture, with the reasoning in 3 bullet points."}


async def _venture_and_manager(venture_ref: str, db: AsyncSession):
    from app.models.agent import Agent
    try:
        cond = Venture.id == uuid.UUID(venture_ref)
    except ValueError:
        cond = Venture.slug == venture_ref
    venture = (await db.execute(select(Venture).where(cond))).scalar_one_or_none()
    if venture is None:
        raise HTTPException(status_code=404, detail=_error("Venture not found"))
    manager = (await db.execute(select(Agent).where(Agent.name.ilike(venture.manager_name or "")))).scalar_one_or_none()
    return venture, manager


@router.get("/{venture_ref}/playbooks", response_model=dict[str, Any], tags=["ventures"])
async def venture_playbooks(
    venture_ref: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.VENTURE_READ)),
) -> dict[str, Any]:
    venture, manager = await _venture_and_manager(venture_ref, db)
    return {
        "venture": venture.slug,
        "manager": manager.name if manager else None,
        "manager_id": str(manager.id) if manager else None,
        "playbooks": PLAYBOOKS.get(venture.slug, []) + [GENERIC_PLAYBOOK],
    }


@router.post("/{venture_ref}/dispatch", response_model=dict[str, Any], tags=["ventures"])
async def dispatch_venture_task(
    venture_ref: str,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.VENTURE_WRITE)),
) -> dict[str, Any]:
    """Create an EmpireOS task for the venture's manager and hand it to the A2A hub."""
    import json as _json
    import httpx
    from app.models.task import Task, TaskStatus

    venture, manager = await _venture_and_manager(venture_ref, db)
    if manager is None:
        raise HTTPException(status_code=409, detail=_error(f"{venture.name} has no manager agent to run this"))
    title = str(payload.get("title") or "").strip()[:200] or "Cockpit task"
    brief = str(payload.get("brief") or "").strip()[:6000]
    if not brief:
        raise HTTPException(status_code=422, detail=_error("A brief is required"))

    task = Task(
        title=f"[{venture.name}] {title}"[:255],
        description=brief,
        input_data=_json.dumps({"source": "cockpit", "venture": venture.slug, "playbook": payload.get("playbook_id")}),
        agent_id=manager.id,
        venture_id=venture.id,
        status=TaskStatus.QUEUED,
        priority=8,
    )
    db.add(task)
    await db.flush()

    prompt = (f"TITLE: {title}\nVENTURE: {venture.name} ({venture.slug})\nREQUESTED BY: Anthony via the EmpireOS cockpit\n\n{brief}")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(f"{A2A_HUB}/agents/{manager.name}/tasks/send",
                                  json={"task": prompt, "sessionId": f"cortexos:{task.id}"})
            r.raise_for_status()
            hub_id = r.json().get("id")
    except Exception as exc:
        task.status = TaskStatus.FAILED
        task.error_message = f"A2A hub unreachable: {exc}"[:500]
        await db.flush()
        raise HTTPException(status_code=502, detail=_error("Couldn't reach the A2A hub; task saved as failed"))

    task.celery_task_id = f"a2a:{hub_id}"
    await db.flush()
    return {"task_id": str(task.id), "a2a_task_id": hub_id, "status": task.status, "agent": manager.name}


# 2026-10-10: the Ventures page links every card to /ventures/{id}, but this route never
# existed, so every click showed "failed to load venture". Accepts the UUID or the slug.
# Declared last so it can't shadow /registry or /{id}/health.
@router.get("/{venture_ref}", response_model=VentureRead, tags=["ventures"])
async def get_venture(
    venture_ref: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.VENTURE_READ)),
) -> VentureRead:
    try:
        cond = Venture.id == uuid.UUID(venture_ref)
    except ValueError:
        cond = Venture.slug == venture_ref
    venture = (await db.execute(select(Venture).where(cond))).scalar_one_or_none()
    if venture is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_error("Venture not found"))
    return VentureRead.model_validate(venture)

