"""Knowledge graph (Graphiti) endpoints."""
from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.rbac import Permission, require_permission
from app.dependencies import get_db
from app.memory.manager import MemoryManager
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

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
