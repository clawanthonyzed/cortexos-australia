"""Knowledge graph (Graphiti) endpoints."""
from __future__ import annotations

import random
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import Permission, require_permission
from app.dependencies import get_db
from app.memory.manager import MemoryManager
from app.models.user import User

logger = structlog.get_logger(__name__)
router = APIRouter()


class EpisodeCreate(BaseModel):
    name: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    source_description: str = ""
    episode_type: str = "text"
    group_id: str = "default"


class GraphSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    num_results: int = Field(default=10, ge=1, le=100)
    group_id: str | None = None


@router.get("", tags=["knowledge_graph"])
async def get_knowledge_graph(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.MEMORY_READ)),
) -> dict[str, Any]:
    """Synthetic knowledge graph built from DB entities (Agents, Products, Memory)."""
    from app.models.agent import Agent
    from app.models.memory_item import MemoryItem
    from app.models.product import Product
    from app.models.task import Task

    nodes: list[dict] = []
    edges: list[dict] = []
    node_ids: set[str] = set()

    def _pos() -> dict[str, int]:
        return {"x": random.randint(80, 920), "y": random.randint(80, 680)}

    # Agents
    agents = (await db.execute(select(Agent).limit(50))).scalars().all()
    agent_node_map: dict[str, str] = {}
    for a in agents:
        nid = f"agent:{a.id}"
        agent_node_map[str(a.id)] = nid
        nodes.append({
            "id": nid,
            "label": a.name,
            "type": "agent",
            "properties": {
                "status": a.status,
                "model": a.model_name,
                "totalCostUsd": a.total_cost_usd,
                "successCount": a.success_count,
                "errorCount": a.error_count,
            },
            "connections": 0,
            **_pos(),
        })
        node_ids.add(nid)

    # Products
    products = (await db.execute(select(Product).limit(30))).scalars().all()
    for p in products:
        nid = f"product:{p.id}"
        nodes.append({
            "id": nid,
            "label": p.name,
            "type": "product",
            "properties": {
                "status": p.status,
                "priceAud": p.price_aud,
                "totalSales": p.total_sales,
                "revenueAud": p.total_revenue_aud,
            },
            "connections": 0,
            **_pos(),
        })
        node_ids.add(nid)

    # Memory items — sampled, rendered as research nodes
    mem_items = (await db.execute(select(MemoryItem).limit(20))).scalars().all()
    for m in mem_items:
        nid = f"memory:{m.id}"
        label = m.summary or (m.content[:60] + "…" if len(m.content) > 60 else m.content)
        nodes.append({
            "id": nid,
            "label": label,
            "type": "research",
            "properties": {
                "memoryType": m.memory_type,
                "category": m.category,
                "importanceScore": m.importance_score,
            },
            "connections": 0,
            **_pos(),
        })
        node_ids.add(nid)
        if m.agent_id:
            src = agent_node_map.get(str(m.agent_id))
            if src:
                edges.append({
                    "id": f"edge:mem:{m.id}",
                    "source": src,
                    "target": nid,
                    "label": "has_memory",
                    "weight": float(m.importance_score),
                })

    # Tasks — agents active in the system get linked to a central venture node
    tasks = (
        await db.execute(select(Task).where(Task.agent_id.isnot(None)).limit(100))
    ).scalars().all()
    seen_venture_edges: set[str] = set()
    for t in tasks:
        aid = agent_node_map.get(str(t.agent_id))
        if not aid:
            continue
        venture_nid = "venture:cortexos"
        if venture_nid not in node_ids:
            nodes.append({
                "id": venture_nid,
                "label": "CortexOS",
                "type": "venture",
                "properties": {"totalAgents": len(agents), "totalProducts": len(products)},
                "connections": 0,
                "x": 500,
                "y": 380,
            })
            node_ids.add(venture_nid)
        eid = f"edge:venture:{t.agent_id}"
        if eid not in seen_venture_edges:
            seen_venture_edges.add(eid)
            edges.append({"id": eid, "source": aid, "target": venture_nid, "label": "operates_in", "weight": 1.0})

    # Update connection counts
    conn: dict[str, int] = {}
    for e in edges:
        conn[e["source"]] = conn.get(e["source"], 0) + 1
        conn[e["target"]] = conn.get(e["target"], 0) + 1
    for n in nodes:
        n["connections"] = conn.get(n["id"], 0)

    from datetime import datetime, timezone
    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "nodeCount": len(nodes),
            "edgeCount": len(edges),
            "lastUpdatedAt": datetime.now(tz=timezone.utc).isoformat(),
        },
    }


@router.post("/episodes", tags=["knowledge_graph"])
async def add_episode(
    payload: EpisodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.MEMORY_WRITE)),
) -> dict[str, Any]:
    """Add an episode (fact/event) to the knowledge graph."""
    manager = MemoryManager(db)
    success = await manager.add_to_knowledge_graph(
        name=payload.name,
        content=payload.content,
        source=payload.source_description,
        group_id=payload.group_id,
    )
    if not success:
        raise HTTPException(
            status_code=503,
            detail={"error": "Knowledge graph unavailable — check Neo4j connection"},
        )
    return {"status": "added", "name": payload.name}


@router.post("/search", tags=["knowledge_graph"])
async def search_graph(
    payload: GraphSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.MEMORY_READ)),
) -> dict[str, Any]:
    """Semantic search over the knowledge graph."""
    manager = MemoryManager(db)
    results = await manager.search_knowledge_graph(
        query=payload.query,
        num_results=payload.num_results,
    )
    return {"results": results, "query": payload.query, "total": len(results)}


@router.get("/entities/{entity_uuid}", tags=["knowledge_graph"])
async def get_entity(
    entity_uuid: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.MEMORY_READ)),
) -> dict[str, Any]:
    """Get a knowledge graph entity by UUID."""
    manager = MemoryManager(db)
    entity = await manager.graphiti.get_entity(entity_uuid)
    if not entity:
        raise HTTPException(status_code=404, detail={"error": "Entity not found"})
    return entity
