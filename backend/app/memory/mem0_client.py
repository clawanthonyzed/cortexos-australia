"""Mem0 client wrapper for short and long-term agent memory."""
from __future__ import annotations

import json
import uuid
from typing import Any

import structlog

from app.config import settings

logger = structlog.get_logger(__name__)

_ANTHROPIC_PATCHED = False


def _patch_anthropic_llm() -> None:
    # mem0ai==0.1.32's AnthropicLLM always sends both temperature and top_p.
    # Current Anthropic models reject that combination (400: only one of
    # temperature/top_p may be set). Drop top_p — deterministic fact
    # extraction only needs temperature=0. Patched here rather than editing
    # the vendored package so the fix survives image rebuilds. Safe to
    # remove once mem0ai is upgraded past this bug.
    global _ANTHROPIC_PATCHED
    if _ANTHROPIC_PATCHED:
        return
    try:
        from mem0.llms.anthropic import AnthropicLLM

        def generate_response(self, messages, response_format=None, tools=None, tool_choice="auto"):
            system_message = ""
            filtered_messages = []
            for message in messages:
                if message["role"] == "system":
                    system_message = message["content"]
                else:
                    filtered_messages.append(message)

            params = {
                "model": self.config.model,
                "messages": filtered_messages,
                "system": system_message,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
            }
            if tools:
                params["tools"] = tools
                params["tool_choice"] = tool_choice

            response = self.client.messages.create(**params)
            text_out = response.content[0].text.strip()
            # claude-haiku-4-5 often wraps JSON replies in markdown fences
            # and/or appends trailing prose; mem0's json.loads() callers
            # expect a bare JSON string with nothing else. Extract just the
            # first complete JSON value and discard everything around it.
            first_brace = text_out.find("{")
            if first_brace != -1:
                decoder = json.JSONDecoder()
                try:
                    _, end = decoder.raw_decode(text_out, first_brace)
                    text_out = text_out[first_brace:end]
                except (json.JSONDecodeError, ValueError):
                    pass
            return text_out

        AnthropicLLM.generate_response = generate_response
        _ANTHROPIC_PATCHED = True
        logger.info("Patched mem0 AnthropicLLM to drop top_p (SPEC fix, mem0ai==0.1.32 bug)")
    except ImportError:
        pass


class Mem0Client:
    """
    Thin wrapper around mem0ai.
    Falls back to a no-op stub if mem0ai is not installed or no API key is set.
    """

    def __init__(self) -> None:
        self._client: Any = None
        self._initialised = False

    def _get_client(self) -> Any:
        if self._initialised:
            return self._client

        self._initialised = True
        try:
            if settings.mem0_api_key:
                from mem0 import MemoryClient  # type: ignore[import]
                self._client = MemoryClient(api_key=settings.mem0_api_key)
                logger.info("Mem0 cloud client initialised")
            elif not settings.mem0_use_local:
                logger.warning("No MEM0_API_KEY set and local mode disabled — memory disabled")
            else:
                # Local mode: Qdrant vector store + Ollama embeddings (no OpenAI key needed)
                from mem0 import Memory  # type: ignore[import]
                _patch_anthropic_llm()
                mem0_config = {
                    "embedder": {
                        "provider": "ollama",
                        "config": {
                            "model": settings.mem0_embed_model,
                            "ollama_base_url": settings.mem0_ollama_url,
                        },
                    },
                    "llm": {
                        "provider": "anthropic",
                        "config": {
                            "model": "claude-haiku-4-5-20251001",
                            "api_key": settings.anthropic_api_key,
                        },
                    },
                }
                self._client = Memory.from_config(mem0_config)
                logger.info("Mem0 local client initialised", embed_model=settings.mem0_embed_model)
        except ImportError:
            logger.warning("mem0ai not installed — memory disabled")
        except Exception as exc:
            logger.error("Mem0 init failed", error=str(exc))

        return self._client

    async def add(
        self,
        content: str,
        agent_id: str | None = None,
        user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Store a memory entry."""
        client = self._get_client()
        if not client:
            return None
        try:
            import asyncio
            messages = [{"role": "user", "content": content}]
            kwargs: dict[str, Any] = {"messages": messages, "metadata": metadata or {}}
            if agent_id:
                kwargs["agent_id"] = agent_id
            elif user_id:
                kwargs["user_id"] = user_id

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: client.add(**kwargs))
            return result
        except Exception as exc:
            logger.error("Mem0 add failed", error=str(exc))
            return None

    async def search(
        self,
        query: str,
        agent_id: str | None = None,
        user_id: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search memory for relevant entries."""
        client = self._get_client()
        if not client:
            return []
        try:
            import asyncio
            kwargs: dict[str, Any] = {"query": query, "limit": limit}
            if agent_id:
                kwargs["agent_id"] = agent_id
            elif user_id:
                kwargs["user_id"] = user_id

            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, lambda: client.search(**kwargs))
            return results if isinstance(results, list) else results.get("results", [])
        except Exception as exc:
            logger.error("Mem0 search failed", error=str(exc))
            return []

    async def get_all(
        self,
        agent_id: str | None = None,
        user_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve all stored memories for an agent or user."""
        client = self._get_client()
        if not client:
            return []
        try:
            import asyncio
            kwargs: dict[str, Any] = {}
            if agent_id:
                kwargs["agent_id"] = agent_id
            elif user_id:
                kwargs["user_id"] = user_id

            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, lambda: client.get_all(**kwargs))
            return results if isinstance(results, list) else results.get("results", [])
        except Exception as exc:
            logger.error("Mem0 get_all failed", error=str(exc))
            return []

    async def delete(self, memory_id: str) -> bool:
        """Delete a specific memory entry by ID."""
        client = self._get_client()
        if not client:
            return False
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: client.delete(memory_id=memory_id))
            return True
        except Exception as exc:
            logger.error("Mem0 delete failed", memory_id=memory_id, error=str(exc))
            return False

    async def delete_all(
        self,
        agent_id: str | None = None,
        user_id: str | None = None,
    ) -> bool:
        """Delete all memories for an agent or user."""
        client = self._get_client()
        if not client:
            return False
        try:
            import asyncio
            kwargs: dict[str, Any] = {}
            if agent_id:
                kwargs["agent_id"] = agent_id
            elif user_id:
                kwargs["user_id"] = user_id

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: client.delete_all(**kwargs))
            return True
        except Exception as exc:
            logger.error("Mem0 delete_all failed", error=str(exc))
            return False
