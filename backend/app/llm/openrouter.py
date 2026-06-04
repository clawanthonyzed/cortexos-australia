"""OpenRouter multi-model proxy LLM implementation."""
from __future__ import annotations

from typing import Any

import httpx
import structlog

from app.config import settings
from app.llm.base import BaseLLM, LLMMessage, LLMResponse, LLMUsage

logger = structlog.get_logger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterLLM(BaseLLM):
    """
    OpenRouter proxy — supports any model available on openrouter.ai.
    Uses the OpenAI-compatible chat completions API.
    """

    provider = "openrouter"

    def __init__(self, model: str = "anthropic/claude-sonnet-4-6", **kwargs: Any) -> None:
        super().__init__(model, **kwargs)

    async def complete(
        self,
        messages: list[LLMMessage],
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> LLMResponse:
        openai_messages: list[dict[str, str]] = []
        if system:
            openai_messages.append({"role": "system", "content": system})
        openai_messages.extend(
            {"role": m.role, "content": m.content} for m in messages
        )

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": openai_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs,
        }

        headers = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "HTTP-Referer": "https://cortexos.au",
            "X-Title": "CortexOS Australia",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{OPENROUTER_BASE_URL}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "OpenRouter API error",
                status=exc.response.status_code,
                model=self.model,
                body=exc.response.text[:500],
            )
            raise
        except Exception as exc:
            logger.error("OpenRouter request failed", model=self.model, error=str(exc))
            raise

        content = data["choices"][0]["message"]["content"] or ""
        usage_data = data.get("usage", {})
        usage = LLMUsage(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
        )

        return LLMResponse(
            content=content,
            usage=usage,
            model=self.model,
            provider=self.provider,
            raw=data,
            stop_reason=data["choices"][0].get("finish_reason"),
        )
