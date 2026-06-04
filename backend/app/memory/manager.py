"""MemoryManager — unified interface for Mem0 + Graphiti + DB."""
from __future__ import annotations

import json
import uuid
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.graphiti_client import GraphitiClient
from app.memory.mem0_client import Mem0Client
from app.models.memory_item import MemoryItem, MemoryType

logger = structlog.get_logger(__name__)

# Module-level singletons
_mem0: Mem0Client | None = None
_graphiti: GraphitiClient | None = None


def get_mem0() -> Mem0Client:
    global _mem0
    if _mem0 is None:
        _mem0 = Mem0Client()
    return _mem0


def get_graphiti() -> GraphitiClient:
    global _graphiti
    if _graphiti is None:
        _graphiti = GraphitiClient()
    return _graphiti


class MemoryManager:
    """
    Unified memory interface:
    - short_term → Mem0 (fast, contextual recall)
    - long_term → Mem0 + PostgreSQL MemoryItem
    - knowledge → Graphiti (entity/relation graph)
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.mem0 = get_mem0()
        self.graphiti = get_graphiti()

    async def remember(
        self,
        content: str,
        agent_id: str | None = None,
        user_id: str | None = None,
        memory_type: str = MemoryType.SHORT_TERM,
        category: str | None = None,
        tags: list[str] | None = None,
        importance: float = 0.5,
        persist_to_db: bool = True,
    ) -> MemoryItem | None:
        """
        Store a memory entry across all relevant backends.
        Returns the DB MemoryItem if persist_to_db=True.
        """
        # 1. Push to Mem0
        mem0_result = await self.mem0.add(
            content=content,
            agent_id=agent_id,
            user_id=user_id,
            metadata={
                "memory_type": memory_type,
                "category": category,
                "tags": tags or [],
                "importance": importance,
            },
        )
        external_id: str | None = None
        if mem0_result and isinstance(mem0_result, dict):
            external_id = mem0_result.get("id") or mem0_result.get("memory_id")
        elif isinstance(mem0_result, list) and mem0_result:
            external_id = mem0_result[0].get("id")

        if not persist_to_db:
            return None

        # 2. Persist to PostgreSQL
        item = MemoryItem(
            content=content,
            memory_type=memory_type,
            category=category,
            tags=json.dumps(tags or []),
            importance_score=importance,
            agent_id=uuid.UUID(agent_id) if agent_id else None,
            user_id=uuid.UUID(user_id) if user_id else None,
            external_id=external_id,
        )
        self.db.add(item)
        await self.db.flush()
        logger.debug("Memory stored", item_id=str(item.id), type=memory_type)
        return item

    async def recall(
        self,
        query: str,
        agent_id: str | None = None,
        user_id: str | None = None,
        limit: int = 10,
        memory_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search memory across Mem0 and return ranked results.
        Falls back to DB full-text if Mem0 unavailable.
        """
        results = await self.mem0.search(
            query=query,
            agent_id=agent_id,
            user_id=user_id,
            limit=limit,
        )

        if results:
            return results

        # Fallback: naive DB search by content substring
        stmt = select(MemoryItem).where(MemoryItem.content.ilike(f"%{query}%"))
        if agent_id:
            stmt = stmt.where(MemoryItem.agent_id == uuid.UUID(agent_id))
        if user_id:
            stmt = stmt.where(MemoryItem.user_id == uuid.UUID(user_id))
        if memory_type:
            stmt = stmt.where(MemoryItem.memory_type == memory_type)
        stmt = stmt.limit(limit).order_by(MemoryItem.importance_score.desc())

        db_results = await self.db.execute(stmt)
        items = db_results.scalars().all()
        return [
            {
                "id": str(item.id),
                "memory": item.content,
                "score": item.importance_score,
                "metadata": {
                    "memory_type": item.memory_type,
                    "category": item.category,
                    "tags": json.loads(item.tags),
                },
            }
            for item in items
        ]

    async def add_to_knowledge_graph(
        self,
        name: str,
        content: str,
        source: str = "",
        group_id: str = "default",
    ) -> bool:
        """Add a fact to the Graphiti knowledge graph."""
        return await self.graphiti.add_episode(
            name=name,
            content=content,
            source_description=source,
            group_id=group_id,
        )

    async def search_knowledge_graph(
        self,
        query: str,
        num_results: int = 10,
    ) -> list[dict[str, Any]]:
        """Search the Graphiti knowledge graph."""
        return await self.graphiti.search(query=query, num_results=num_results)

    async def forget(self, memory_id: str) -> bool:
        """Delete a memory from Mem0 and the database."""
        await self.mem0.delete(memory_id)
        try:
            item_uuid = uuid.UUID(memory_id)
            item = await self.db.get(MemoryItem, item_uuid)
            if item:
                await self.db.delete(item)
        except ValueError:
            # memory_id is an external ID not a UUID
            pass
        return True
