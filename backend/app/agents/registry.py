"""AgentRegistry — register, lookup, and spawn agent classes."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import BaseAgent
from app.models.agent import Agent as AgentModel

logger = structlog.get_logger(__name__)

if TYPE_CHECKING:
    pass

# Registry: maps agent_type -> BaseAgent subclass
_REGISTRY: dict[str, type[BaseAgent]] = {}


def register_agent(agent_type: str) -> Any:
    """Class decorator to register an agent by type name."""
    def decorator(cls: type[BaseAgent]) -> type[BaseAgent]:
        _REGISTRY[agent_type] = cls
        logger.debug("Agent registered", type=agent_type, class_name=cls.__name__)
        return cls
    return decorator


class AgentRegistry:
    """
    Registry for agent classes and database-backed agent instances.
    """

    def __init__(self) -> None:
        # Ensure default agents are imported (which triggers registration)
        self._import_defaults()

    @staticmethod
    def _import_defaults() -> None:
        """Import all default agents to ensure they register themselves."""
        try:
            from app.agents.defaults import (  # noqa: F401
                ceo, research, product, seo, content, marketing, support, finance, operations
            )
        except ImportError as exc:
            logger.warning("Some default agents failed to import", error=str(exc))

    @staticmethod
    def get_class(agent_type: str) -> type[BaseAgent] | None:
        """Return the BaseAgent subclass registered for a given type."""
        return _REGISTRY.get(agent_type)

    @staticmethod
    def list_types() -> list[str]:
        """List all registered agent types."""
        return list(_REGISTRY.keys())

    @staticmethod
    async def spawn(
        db: AsyncSession,
        agent_type: str,
        model_provider: str = "claude",
        model_name: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        system_prompt: str | None = None,
        agent_db_id: uuid.UUID | None = None,
        config: dict[str, Any] | None = None,
    ) -> BaseAgent:
        """
        Instantiate an agent by type, using the DB record if available.

        Falls back to BaseAgent if the type is not in the registry.
        """
        cls = _REGISTRY.get(agent_type, BaseAgent)

        return cls(
            db=db,
            model_provider=model_provider,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt,
            agent_db_id=agent_db_id,
            config=config or {},
        )

    @staticmethod
    async def spawn_from_db(db: AsyncSession, agent_id: uuid.UUID) -> BaseAgent | None:
        """Load an Agent from the database and spawn a live instance."""
        import json
        result = await db.execute(select(AgentModel).where(AgentModel.id == agent_id))
        db_agent = result.scalar_one_or_none()
        if not db_agent:
            return None

        try:
            config = json.loads(db_agent.config_json)
        except (json.JSONDecodeError, TypeError):
            config = {}

        return await AgentRegistry.spawn(
            db=db,
            agent_type=db_agent.agent_type,
            model_provider=db_agent.model_provider,
            model_name=db_agent.model_name,
            temperature=db_agent.temperature,
            max_tokens=db_agent.max_tokens,
            system_prompt=db_agent.system_prompt,
            agent_db_id=db_agent.id,
            config=config,
        )
