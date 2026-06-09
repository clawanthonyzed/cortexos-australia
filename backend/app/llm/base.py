"""Abstract base class for all LLM providers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class LLMUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0

    @property
    def cost_usd(self) -> float:
        """Subclasses may override to compute actual costs."""
        return 0.0


@dataclass
class LLMResponse:
    content: str
    usage: LLMUsage
    model: str
    provider: str
    raw: Any = field(default=None, repr=False)
    stop_reason: str | None = None

    @property
    def total_tokens(self) -> int:
        return self.usage.total_tokens

    @property
    def cost_usd(self) -> float:
        return self.usage.cost_usd


class BaseLLM(ABC):
    """Abstract interface for all LLM providers."""

    provider: str = "base"
    model: str = ""

    def __init__(self, model: str, **kwargs: Any) -> None:
        self.model = model
        self._kwargs = kwargs

    @abstractmethod
    async def complete(
        self,
        messages: list[LLMMessage],
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> LLMResponse:
        """Send messages and return a single completion."""

    async def stream(
        self,
        messages: list[LLMMessage],
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """Stream token deltas. Default: fall back to single completion."""
        response = await self.complete(
            messages=messages,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        yield response.content

    async def complete_simple(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """Convenience method for single-turn completion."""
        response = await self.complete(
            messages=[LLMMessage(role="user", content=prompt)],
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.content

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} model={self.model}>"
