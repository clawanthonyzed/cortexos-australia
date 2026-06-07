"""Memory read/search/prune endpoints."""
from __future__ import annotations

import json
import uuid
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import Permission, require_permission
from app.dependencies import get_db, paginate
from app.memory.manager import MemoryManager
from app.models.memory_item import MemoryItem
from app.models.user import User
from app.schemas.memory import (
    MemoryItemCreate,
    MemoryItemRead,
    MemoryItemUpdate,
    MemorySearchRequest,
    MemorySearchResponse,
    MemorySearchResult,
)

logger = structlog.get_logger(__name__)
router = APIRouter()


def _error(msg: str, detail: Any = None) -> dict[str, Any]:
    return {"error": msg, "detail": detail or {}}


def _item_to_schema(item: MemoryItem) -> MemoryItemRead:
    try:
        tags = json.loads(item.tags)
    except (json.JSONDecodeError, TypeError):
        tags = []
    return MemoryItemRead(
        id=item.id,
        content=item.content,
        summary=item.summary,
        memory_type=item.memory_type,
        category=item.category,
        tags=tags,
        importance_score=item.importance_score,
        access_count=item.access_count,
        agent_id=item.agent_id,
        user_id=item.user_id,
        external_id=item.external_id,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.get("", response_model=dict[str, Any], tags=["memory"])
async def list_memory(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.MEMORY_READ)),
    pagination: dict = Depends(paginate),
    agent_id: uuid.UUID | None = Query(None),
    memory_type: str | None = Query(None),
    category: str | None = Query(None),
) -> dict[str, Any]:
    """List memory items with pagination."""
    stmt = select(MemoryItem)
    if agent_id:
        stmt = stmt.where(MemoryItem.agent_id == agent_id)
    if memory_type:
        stmt = stmt.where(MemoryItem.memory_type == memory_type)
    if category:
        stmt = stmt.where(MemoryItem.category == category)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.offset(pagination["offset"]).limit(pagination["limit"]).order_by(
        MemoryItem.importance_score.desc(), MemoryItem.created_at.desc()
    )
    result = await db.execute(stmt)
    items = result.scalars().all()

    return {
        "items": [_item_to_schema(i) for i in items],
        "total": total,
        "page": pagination["page"],
        "page_size": pagination["page_size"],
    }


@router.get("/stats", response_model=dict[str, Any], tags=["memory"])
async def memory_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.MEMORY_READ)),
) -> dict[str, Any]:
    """Aggregate memory statistics for dashboard widgets."""
    total = (await db.execute(select(func.count()).select_from(MemoryItem))).scalar_one()
    total_size = (
        await db.execute(select(func.coalesce(func.sum(func.length(MemoryItem.content)), 0)))
    ).scalar_one()

    type_rows = await db.execute(
        select(MemoryItem.memory_type, func.count(MemoryItem.id).label("cnt"))
        .group_by(MemoryItem.memory_type)
    )
    by_type = {row.memory_type: row.cnt for row in type_rows}

    oldest = (await db.execute(select(func.min(MemoryItem.created_at)))).scalar_one()
    newest = (await db.execute(select(func.max(MemoryItem.created_at)))).scalar_one()

    return {
        "totalEntries": total,
        "totalSizeBytes": int(total_size),
        "byType": by_type,
        "byAgent": [],
        "oldestEntryAt": oldest.isoformat() if oldest else None,
        "newestEntryAt": newest.isoformat() if newest else None,
    }


@router.post("/search", response_model=MemorySearchResponse, tags=["memory"])
async def search_memory(
    payload: MemorySearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.MEMORY_READ)),
) -> MemorySearchResponse:
    """Semantic search over memory."""
    manager = MemoryManager(db)
    raw_results = await manager.recall(
        query=payload.query,
        agent_id=str(payload.agent_id) if payload.agent_id else None,
        user_id=str(payload.user_id) if payload.user_id else None,
        limit=payload.limit,
        memory_type=payload.memory_type,
    )

    results: list[MemorySearchResult] = []
    for r in raw_results:
        # mem0 returns dict; build a MemoryItemRead from it
        content = r.get("memory", r.get("content", ""))
        score = float(r.get("score", 0.5))
        external_id = r.get("id")

        # Try to find the DB record
        db_item: MemoryItem | None = None
        if external_id:
            try:
                ext_result = await db.execute(
                    select(MemoryItem).where(MemoryItem.external_id == str(external_id))
                )
                db_item = ext_result.scalar_one_or_none()
            except Exception:
                pass

        if db_item:
            item_schema = _item_to_schema(db_item)
        else:
            from datetime import datetime, timezone
            item_schema = MemoryItemRead(
                id=uuid.uuid4(),
                content=content,
                summary=None,
                memory_type=r.get("metadata", {}).get("memory_type", "short_term"),
                category=r.get("metadata", {}).get("category"),
                tags=r.get("metadata", {}).get("tags", []),
                importance_score=score,
                access_count=0,
                agent_id=payload.agent_id,
                user_id=payload.user_id,
                external_id=str(external_id) if external_id else None,
                created_at=datetime.now(tz=timezone.utc),
                updated_at=datetime.now(tz=timezone.utc),
            )

        results.append(MemorySearchResult(item=item_schema, score=score))

    return MemorySearchResponse(results=results, query=payload.query, total=len(results))


@router.post("", response_model=MemoryItemRead, status_code=status.HTTP_201_CREATED, tags=["memory"])
async def create_memory(
    payload: MemoryItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.MEMORY_WRITE)),
) -> MemoryItemRead:
    """Store a new memory item."""
    manager = MemoryManager(db)
    item = await manager.remember(
        content=payload.content,
        agent_id=str(payload.agent_id) if payload.agent_id else None,
        user_id=str(payload.user_id) if payload.user_id else None,
        memory_type=payload.memory_type,
        category=payload.category,
        tags=payload.tags,
        importance=payload.importance_score,
        persist_to_db=True,
    )
    if not item:
        raise HTTPException(status_code=500, detail=_error("Failed to store memory"))
    return _item_to_schema(item)


@router.get("/{memory_id}", response_model=MemoryItemRead, tags=["memory"])
async def get_memory(
    memory_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.MEMORY_READ)),
) -> MemoryItemRead:
    """Get a specific memory item."""
    item = await db.get(MemoryItem, memory_id)
    if not item:
        raise HTTPException(status_code=404, detail=_error("Memory item not found"))
    item.access_count += 1
    await db.flush()
    return _item_to_schema(item)


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None, tags=["memory"])
async def delete_memory(
    memory_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.MEMORY_DELETE)),
) -> None:
    """Delete a memory item."""
    item = await db.get(MemoryItem, memory_id)
    if not item:
        raise HTTPException(status_code=404, detail=_error("Memory item not found"))
    manager = MemoryManager(db)
    if item.external_id:
        await manager.mem0.delete(item.external_id)
    await db.delete(item)


@router.delete("/agent/{agent_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None, tags=["memory"])
async def prune_agent_memory(
    agent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.MEMORY_DELETE)),
) -> None:
    """Delete all memory for a specific agent."""
    manager = MemoryManager(db)
    await manager.mem0.delete_all(agent_id=str(agent_id))

    result = await db.execute(select(MemoryItem).where(MemoryItem.agent_id == agent_id))
    items = result.scalars().all()
    for item in items:
        await db.delete(item)
