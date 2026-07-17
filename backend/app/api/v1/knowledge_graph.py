"""Knowledge graph endpoints."""
from __future__ import annotations

import json
import random
from datetime import datetime, timezone
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.agent_auth import WriterContext, require_writer
from app.auth.rbac import Permission, require_permission
from app.dependencies import get_db
from app.memory.manager import MemoryManager
from app.models.user import User
from app.services.agent_write_guard import enforce_rate_limit, is_recent_duplicate

logger = structlog.get_logger(__name__)
router = APIRouter()


class EpisodeCreate(BaseModel):
    name: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1, max_length=8000)
    source_description: str = ""
    episode_type: str = "text"
    # None = "use the caller's own venture" (agents) or "default" (dashboard).
    # Specialists may pass an explicit group_id to target another venture.
    group_id: str | None = None


class GraphSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    num_results: int = Field(default=10, ge=1, le=100)
    group_id: str | None = None


@router.get("", tags=["knowledge_graph"])
async def get_knowledge_graph(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.MEMORY_READ)),
) -> dict[str, Any]:
    """Synthetic knowledge graph: ventures + agents + memory."""
    from app.models.agent import Agent
    from app.models.memory_item import MemoryItem
    from app.models.venture import Venture

    nodes: list[dict] = []
    edges: list[dict] = []
    node_ids: set[str] = set()

    ventures = (await db.execute(select(Venture).limit(60))).scalars().all()
    venture_slug_to_nid: dict[str, str] = {}
    for v in ventures:
        nid = f"venture:{v.id}"
        venture_slug_to_nid[v.slug] = nid
        nodes.append({"id": nid, "label": v.name[:20], "type": "venture",
            "properties": {"slug": v.slug, "manager": v.manager_name, "category": v.category},
            "connections": 0, "x": random.randint(80, 920), "y": random.randint(80, 680)})
        node_ids.add(nid)

    empire_nid = "venture:empire"
    nodes.append({"id": empire_nid, "label": "Empire Hub", "type": "business",
        "properties": {"ventures": len(ventures), "target": "AUD 50k/month"},
        "connections": 0, "x": 500, "y": 350})
    node_ids.add(empire_nid)
    for v in ventures:
        edges.append({"id": f"edge:emp:{v.id}", "source": empire_nid,
            "target": f"venture:{v.id}", "label": "contains", "weight": 0.5})

    agents = (await db.execute(select(Agent).limit(200))).scalars().all()
    agent_node_map: dict[str, str] = {}
    for a in agents:
        nid = f"agent:{a.id}"
        agent_node_map[str(a.id)] = nid
        nodes.append({"id": nid, "label": a.name[:18], "type": "agent",
            "properties": {"status": a.status, "model": a.model_name,
                "successCount": a.success_count, "errorCount": a.error_count},
            "connections": 0, "x": random.randint(80, 920), "y": random.randint(80, 680)})
        node_ids.add(nid)
        raw_tags = a.tags or "[]"
        try:
            parsed = json.loads(raw_tags) if isinstance(raw_tags, str) else raw_tags
            tags = parsed if isinstance(parsed, list) else [str(parsed)]
        except Exception:
            # Plain string — treat as single tag (e.g. "sage-ai")
            tags = [raw_tags.strip()] if raw_tags.strip() and raw_tags.strip() != "[]" else []
        linked = False
        for tag in tags:
            vnid = venture_slug_to_nid.get(str(tag))
            if vnid:
                edges.append({"id": f"edge:av:{a.id}:{tag}", "source": vnid,
                    "target": nid, "label": "employs", "weight": 1.0})
                linked = True
                break
        if not linked and a.venture_id:
            vnid = f"venture:{a.venture_id}"
            if vnid in node_ids:
                edges.append({"id": f"edge:av2:{a.id}", "source": vnid,
                    "target": nid, "label": "employs", "weight": 1.0})
                linked = True
        if not linked:
            # Specialists link to empire hub
            edges.append({"id": f"edge:specialist:{a.id}", "source": empire_nid,
                "target": nid, "label": "employs", "weight": 0.3})

    # Workflows
    from app.models.workflow import Workflow
    workflows = (await db.execute(select(Workflow).limit(30))).scalars().all()
    for wf in workflows:
        nid = f"workflow:{wf.id}"
        nodes.append({"id": nid, "label": wf.name[:18], "type": "campaign",
            "properties": {"status": wf.status, "trigger": wf.trigger_type,
                "venture": wf.venture, "runCount": wf.run_count},
            "connections": 0, "x": random.randint(80, 920), "y": random.randint(80, 680)})
        node_ids.add(nid)
        if wf.venture:
            vnid = venture_slug_to_nid.get(wf.venture)
            if vnid:
                edges.append({"id": f"edge:wfv:{wf.id}", "source": vnid,
                    "target": nid, "label": "runs", "weight": 0.8})
            else:
                edges.append({"id": f"edge:wfhub:{wf.id}", "source": empire_nid,
                    "target": nid, "label": "runs", "weight": 0.6})
        else:
            edges.append({"id": f"edge:wfhub:{wf.id}", "source": empire_nid,
                "target": nid, "label": "runs", "weight": 0.6})

    # Memory items — top importance, filter by category for variety
    mem_items = (await db.execute(
        select(MemoryItem)
        .where(MemoryItem.category.in_(["empire", "financial", "ventures", "workflows"]))
        .order_by(MemoryItem.importance_score.desc())
        .limit(40)
    )).scalars().all()
    for m in mem_items:
        nid = f"memory:{m.id}"
        lbl = m.summary or (m.content[:30] + "..." if len(m.content) > 30 else m.content)
        nodes.append({"id": nid, "label": lbl[:22], "type": "research",
            "properties": {"memoryType": m.memory_type, "category": m.category,
                "importance": m.importance_score},
            "connections": 0, "x": random.randint(80, 920), "y": random.randint(80, 680)})
        node_ids.add(nid)
        # Link to venture if external_id has venture slug
        linked_mem = False
        if m.external_id and m.external_id.startswith("venture:fact:"):
            slug = m.external_id.replace("venture:fact:", "")
            vnid = venture_slug_to_nid.get(slug)
            if vnid:
                edges.append({"id": f"edge:mfact:{m.id}", "source": vnid,
                    "target": nid, "label": "describes", "weight": 0.9})
                linked_mem = True
        if not linked_mem:
            if m.agent_id:
                src = agent_node_map.get(str(m.agent_id))
                if src:
                    edges.append({"id": f"edge:mem:{m.id}", "source": src,
                        "target": nid, "label": "observed", "weight": float(m.importance_score or 0.5)})
                    linked_mem = True
            if not linked_mem and (m.importance_score or 0) >= 0.8:
                edges.append({"id": f"edge:memhub:{m.id}", "source": empire_nid,
                    "target": nid, "label": "knows", "weight": float(m.importance_score or 0.5)})

    conn: dict[str, int] = {}
    for e in edges:
        conn[e["source"]] = conn.get(e["source"], 0) + 1
        conn[e["target"]] = conn.get(e["target"], 0) + 1
    for n in nodes:
        n["connections"] = conn.get(n["id"], 0)

    return {"nodes": nodes, "edges": edges,
        "stats": {"nodeCount": len(nodes), "edgeCount": len(edges),
            "lastUpdatedAt": datetime.now(tz=timezone.utc).isoformat()}}


@router.post("/episodes", tags=["knowledge_graph"])
async def add_episode(
    payload: EpisodeCreate,
    db: AsyncSession = Depends(get_db),
    writer: WriterContext = Depends(require_writer(Permission.MEMORY_WRITE)),
) -> dict[str, Any]:
    group_id = payload.group_id
    source_description = payload.source_description

    if writer.agent is not None:
        agent = writer.agent
        await enforce_rate_limit(f"kg:{agent.agent_id}")
        if await is_recent_duplicate(f"kg:{agent.agent_id}", payload.content):
            return {"status": "skipped_duplicate", "name": payload.name}

        if group_id is None:
            group_id = agent.venture_slug if not agent.is_specialist else "default"
        elif not agent.is_specialist:
            # Non-specialist agents can't target another venture's graph —
            # ignore the override, same rule as memory writes.
            group_id = agent.venture_slug or "default"
        if not source_description:
            source_description = f"agent:{agent.name}"
    elif group_id is None:
        group_id = "default"

    manager = MemoryManager(db)
    success = await manager.add_to_knowledge_graph(
        name=payload.name, content=payload.content,
        source=source_description, group_id=group_id,
    )
    if not success:
        raise HTTPException(status_code=503, detail={"error": "Knowledge graph unavailable"})
    return {"status": "added", "name": payload.name, "group_id": group_id}


@router.post("/search", tags=["knowledge_graph"])
async def search_graph(
    payload: GraphSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.MEMORY_READ)),
) -> dict[str, Any]:
    manager = MemoryManager(db)
    results = await manager.search_knowledge_graph(query=payload.query, num_results=payload.num_results)
    return {"results": results, "query": payload.query, "total": len(results)}


@router.get("/entities/{entity_uuid}", tags=["knowledge_graph"])
async def get_entity(
    entity_uuid: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.MEMORY_READ)),
) -> dict[str, Any]:
    manager = MemoryManager(db)
    entity = await manager.graphiti.get_entity(entity_uuid)
    if not entity:
        raise HTTPException(status_code=404, detail={"error": "Entity not found"})
    return entity
