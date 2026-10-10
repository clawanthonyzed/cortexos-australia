"""Resources catalog API (2026-10-10).

Serves the holding company's resource inventory (skills, tools, MCP servers, AI models and routes,
databases) for the EmpireOS "Resources" tab. The catalog is built on the host every 6 hours by
/opt/openclaw/orchestration/build_resources_catalog.py (only the host can see docker, Ollama and
`claude mcp list`) and read here from the read-only /opt/openclaw mount. Never writes.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.auth.rbac import Permission, require_permission
from app.models.user import User

router = APIRouter()

CATALOG = Path("/opt/openclaw/orchestration/resources_catalog.json")


@router.get("", tags=["resources"])
async def list_resources(current_user: User = Depends(require_permission(Permission.AGENT_READ))) -> dict[str, Any]:
    if not CATALOG.exists():
        raise HTTPException(status_code=503, detail={"error": "Resources catalog not built yet"})
    try:
        data = json.loads(CATALOG.read_text())
    except (OSError, json.JSONDecodeError) as e:
        raise HTTPException(status_code=503, detail={"error": f"Resources catalog unreadable: {e}"})
    resources = data.get("resources", [])
    categories: dict[str, int] = {}
    for r in resources:
        categories[r.get("category", "Other")] = categories.get(r.get("category", "Other"), 0) + 1
    return {
        "generated_at": data.get("generated_at"),
        "total": len(resources),
        "counts": data.get("counts", {}),
        "categories": dict(sorted(categories.items(), key=lambda kv: -kv[1])),
        "resources": resources,
    }
