"""Graphiti knowledge graph client wrapper."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import structlog

from app.config import settings

logger = structlog.get_logger(__name__)


class GraphitiClient:
    """
    Wrapper around graphiti-core for entity/relation knowledge graph.
    Falls back to no-op if graphiti-core not installed or Neo4j unavailable.
    """

    def __init__(self) -> None:
        self._client: Any = None
        self._initialised = False

    def _get_client(self) -> Any:
        if self._initialised:
            return self._client

        self._initialised = True
        try:
            from graphiti_core import Graphiti  # type: ignore[import]
            self._client = Graphiti(
                settings.graphiti_uri,
                settings.graphiti_user,
                settings.graphiti_password,
            )
            logger.info("Graphiti client initialised", uri=settings.graphiti_uri)
        except ImportError:
            logger.warning("graphiti-core not installed — knowledge graph disabled")
        except Exception as exc:
            logger.error("Graphiti init failed", error=str(exc))

        return self._client

    async def add_episode(
        self,
        name: str,
        content: str,
        source_description: str = "",
        episode_type: str = "text",
        reference_time: datetime | None = None,
        group_id: str = "default",
    ) -> bool:
        """Add an episode (fact/event) to the knowledge graph."""
        client = self._get_client()
        if not client:
            return False
        try:
            from graphiti_core.nodes import EpisodeType  # type: ignore[import]
            ep_type = getattr(EpisodeType, episode_type.upper(), EpisodeType.TEXT)
            ref_time = reference_time or datetime.now(tz=timezone.utc)

            await client.add_episode(
                name=name,
                episode_body=content,
                source_description=source_description,
                reference_time=ref_time,
                episode_type=ep_type,
                group_id=group_id,
            )
            return True
        except Exception as exc:
            logger.error("Graphiti add_episode failed", name=name, error=str(exc))
            return False

    async def search(
        self,
        query: str,
        num_results: int = 10,
        group_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Semantic search over the knowledge graph."""
        client = self._get_client()
        if not client:
            return []
        try:
            results = await client.search(query=query, num_results=num_results)
            output: list[dict[str, Any]] = []
            for r in results:
                output.append(
                    {
                        "uuid": str(getattr(r, "uuid", "")),
                        "name": getattr(r, "name", ""),
                        "fact": getattr(r, "fact", ""),
                        "score": float(getattr(r, "score", 0.0)),
                        "created_at": str(getattr(r, "created_at", "")),
                    }
                )
            return output
        except Exception as exc:
            logger.error("Graphiti search failed", query=query, error=str(exc))
            return []

    async def get_entity(self, entity_uuid: str) -> dict[str, Any] | None:
        """Fetch a node by UUID."""
        client = self._get_client()
        if not client:
            return None
        try:
            node = await client.get_node(uuid=entity_uuid)
            if node:
                return {
                    "uuid": str(node.uuid),
                    "name": node.name,
                    "summary": getattr(node, "summary", ""),
                    "created_at": str(node.created_at),
                }
            return None
        except Exception as exc:
            logger.error("Graphiti get_entity failed", uuid=entity_uuid, error=str(exc))
            return None

    async def close(self) -> None:
        """Close the Neo4j connection."""
        if self._client:
            try:
                await self._client.close()
            except Exception:
                pass
