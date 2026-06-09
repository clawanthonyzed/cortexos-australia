"""Anthropic Claude LLM implementation with prompt caching support."""
from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

import structlog

from app.config import settings
from app.llm.base import BaseLLM, LLMMessage, LLMResponse, LLMUsage

logger = structlog.get_logger(__name__)

# Pricing per million tokens (USD) — claude-sonnet-4-6
_PRICING: dict[str, dict[str, float]] = {
    "claude-sonnet-4-6": {
        "input": 3.00,
        "output": 15.00,
        "cache_write": 3.75,
        "cache_read": 0.30,
    },
    "claude-opus-4-5": {
        "input": 15.00,
        "output": 75.00,
        "cache_write": 18.75,
        "cache_read": 1.50,
    },
    "claude-haiku-3-5": {
        "input": 0.80,
        "output": 4.00,
        "cache_write": 1.00,
        "cache_read": 0.08,
    },
}


def _compute_cost(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    cache_creation_tokens: int = 0,
    cache_read_tokens: int = 0,
) -> float:
    pricing = _PRICING.get(model, _PRICING["claude-sonnet-4-6"])
    cost = (
        prompt_tokens * pricing["input"] / 1_000_000
        + completion_tokens * pricing["output"] / 1_000_000
        + cache_creation_tokens * pricing["cache_write"] / 1_000_000
        + cache_read_tokens * pricing["cache_read"] / 1_000_000
    )
    return round(cost, 6)


class ClaudeUsage(LLMUsage):
    def __init__(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cache_creation_tokens: int = 0,
        cache_read_tokens: int = 0,
    ) -> None:
        super().__init__(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            cache_creation_tokens=cache_creation_tokens,
            cache_read_tokens=cache_read_tokens,
        )
        self._model = model

    @property
    def cost_usd(self) -> float:
        return _compute_cost(
            self._model,
            self.prompt_tokens,
            self.completion_tokens,
            self.cache_creation_tokens,
            self.cache_read_tokens,
        )


class ClaudeLLM(BaseLLM):
    """Anthropic Claude implementation."""

    provider = "claude"

    def __init__(self, model: str = "claude-sonnet-4-6", **kwargs: Any) -> None:
        super().__init__(model, **kwargs)
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            import anthropic
            self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        return self._client

    async def complete(
        self,
        messages: list[LLMMessage],
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> LLMResponse:
        client = self._get_client()

        # Convert to Anthropic message format
        anthropic_messages = [
            {"role": m.role, "content": m.content}
            for m in messages
            if m.role in ("user", "assistant")
        ]

        params: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": anthropic_messages,
        }

        if system:
            # Use prompt caching for long system prompts
            if len(system) > 1000:
                params["system"] = [
                    {
                        "type": "text",
                        "text": system,
                        "cache_control": {"type": "ephemeral"},
                    }
                ]
            else:
                params["system"] = system

        params.update(kwargs)

        try:
            import anthropic
            response = await client.messages.create(**params)
        except Exception as exc:
            logger.error("Claude API error", model=self.model, error=str(exc))
            raise

        content = response.content[0].text if response.content else ""
        usage_data = response.usage

        cache_creation = getattr(usage_data, "cache_creation_input_tokens", 0) or 0
        cache_read = getattr(usage_data, "cache_read_input_tokens", 0) or 0

        usage = ClaudeUsage(
            model=self.model,
            prompt_tokens=usage_data.input_tokens,
            completion_tokens=usage_data.output_tokens,
            cache_creation_tokens=cache_creation,
            cache_read_tokens=cache_read,
        )

        logger.debug(
            "Claude completion",
            model=self.model,
            tokens=usage.total_tokens,
            cost_usd=usage.cost_usd,
        )

        return LLMResponse(
            content=content,
            usage=usage,
            model=self.model,
            provider=self.provider,
            raw=response,
            stop_reason=response.stop_reason,
        )

    async def stream(
        self,
        messages: list[LLMMessage],
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """Stream token deltas from Claude via streaming API."""
        client = self._get_client()

        anthropic_messages = [
            {"role": m.role, "content": m.content}
            for m in messages
            if m.role in ("user", "assistant")
        ]

        params: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": anthropic_messages,
        }

        if system:
            if len(system) > 1000:
                params["system"] = [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]
            else:
                params["system"] = system

        params.update(kwargs)

        import anthropic
        async with client.messages.stream(**params) as stream:
            async for text in stream.text_stream:
                yield text
