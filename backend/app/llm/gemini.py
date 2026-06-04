"""Google Gemini LLM implementation."""
from __future__ import annotations

from typing import Any

import structlog

from app.config import settings
from app.llm.base import BaseLLM, LLMMessage, LLMResponse, LLMUsage

logger = structlog.get_logger(__name__)

_PRICING: dict[str, dict[str, float]] = {
    "gemini-2.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-2.5-pro": {"input": 1.25, "output": 5.00},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
}


class GeminiUsage(LLMUsage):
    def __init__(self, model: str, prompt_tokens: int, completion_tokens: int) -> None:
        super().__init__(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        )
        self._model = model

    @property
    def cost_usd(self) -> float:
        pricing = _PRICING.get(self._model, _PRICING["gemini-2.5-flash"])
        return round(
            self.prompt_tokens * pricing["input"] / 1_000_000
            + self.completion_tokens * pricing["output"] / 1_000_000,
            6,
        )


class GeminiLLM(BaseLLM):
    """Google Gemini implementation."""

    provider = "gemini"

    def __init__(self, model: str = "gemini-2.5-flash", **kwargs: Any) -> None:
        super().__init__(model, **kwargs)
        self._configured = False

    def _configure(self) -> None:
        if not self._configured:
            import google.generativeai as genai
            genai.configure(api_key=settings.google_api_key)
            self._configured = True

    async def complete(
        self,
        messages: list[LLMMessage],
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> LLMResponse:
        import asyncio
        import google.generativeai as genai
        from google.generativeai.types import GenerationConfig

        self._configure()

        model_obj = genai.GenerativeModel(
            model_name=self.model,
            system_instruction=system,
        )

        # Build parts from messages
        parts: list[str] = []
        for m in messages:
            prefix = "User: " if m.role == "user" else "Assistant: "
            parts.append(f"{prefix}{m.content}")
        prompt = "\n".join(parts)

        config = GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        try:
            # google-generativeai is sync — run in executor
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: model_obj.generate_content(prompt, generation_config=config),
            )
        except Exception as exc:
            logger.error("Gemini API error", model=self.model, error=str(exc))
            raise

        content = response.text if hasattr(response, "text") else ""
        metadata = response.usage_metadata if hasattr(response, "usage_metadata") else None
        prompt_tokens = getattr(metadata, "prompt_token_count", 0) or 0
        completion_tokens = getattr(metadata, "candidates_token_count", 0) or 0

        usage = GeminiUsage(
            model=self.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

        return LLMResponse(
            content=content,
            usage=usage,
            model=self.model,
            provider=self.provider,
            raw=response,
        )
