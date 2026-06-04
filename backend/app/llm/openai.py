"""OpenAI LLM implementation."""
from __future__ import annotations

from typing import Any

import structlog

from app.config import settings
from app.llm.base import BaseLLM, LLMMessage, LLMResponse, LLMUsage

logger = structlog.get_logger(__name__)

_PRICING: dict[str, dict[str, float]] = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "o1": {"input": 15.00, "output": 60.00},
    "o1-mini": {"input": 3.00, "output": 12.00},
}


class OpenAIUsage(LLMUsage):
    def __init__(self, model: str, prompt_tokens: int, completion_tokens: int) -> None:
        super().__init__(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        )
        self._model = model

    @property
    def cost_usd(self) -> float:
        pricing = _PRICING.get(self._model, _PRICING["gpt-4o"])
        return round(
            self.prompt_tokens * pricing["input"] / 1_000_000
            + self.completion_tokens * pricing["output"] / 1_000_000,
            6,
        )


class OpenAILLM(BaseLLM):
    """OpenAI GPT implementation."""

    provider = "openai"

    def __init__(self, model: str = "gpt-4o", **kwargs: Any) -> None:
        super().__init__(model, **kwargs)
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=settings.openai_api_key)
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

        openai_messages: list[dict[str, str]] = []
        if system:
            openai_messages.append({"role": "system", "content": system})
        openai_messages.extend(
            {"role": m.role, "content": m.content} for m in messages
        )

        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=openai_messages,  # type: ignore[arg-type]
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
        except Exception as exc:
            logger.error("OpenAI API error", model=self.model, error=str(exc))
            raise

        content = response.choices[0].message.content or ""
        usage = OpenAIUsage(
            model=self.model,
            prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
            completion_tokens=response.usage.completion_tokens if response.usage else 0,
        )

        return LLMResponse(
            content=content,
            usage=usage,
            model=self.model,
            provider=self.provider,
            raw=response,
            stop_reason=response.choices[0].finish_reason,
        )
