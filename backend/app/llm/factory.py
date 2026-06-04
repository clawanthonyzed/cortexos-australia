"""LLM factory — create the right LLM from provider name."""
from __future__ import annotations

from app.llm.base import BaseLLM
from app.llm.claude import ClaudeLLM
from app.llm.gemini import GeminiLLM
from app.llm.openai import OpenAILLM
from app.llm.openrouter import OpenRouterLLM


class LLMFactory:
    """Create LLM instances by provider name."""

    _DEFAULT_MODELS: dict[str, str] = {
        "claude": "claude-sonnet-4-6",
        "openai": "gpt-4o",
        "gemini": "gemini-2.5-flash",
        "openrouter": "anthropic/claude-sonnet-4-6",
    }

    @staticmethod
    def create(provider: str, model: str | None = None) -> BaseLLM:
        """
        Create an LLM instance.

        Args:
            provider: One of "claude", "openai", "gemini", "openrouter"
            model: Specific model name (uses provider default if omitted)

        Returns:
            A BaseLLM instance ready to call.

        Raises:
            ValueError: If the provider is not recognised.
        """
        resolved_model = model or LLMFactory._DEFAULT_MODELS.get(provider)
        if resolved_model is None:
            raise ValueError(f"Unknown LLM provider: {provider!r}")

        match provider:
            case "claude":
                return ClaudeLLM(model=resolved_model)
            case "openai":
                return OpenAILLM(model=resolved_model)
            case "gemini":
                return GeminiLLM(model=resolved_model)
            case "openrouter":
                return OpenRouterLLM(model=resolved_model)
            case _:
                raise ValueError(f"Unknown LLM provider: {provider!r}")

    @staticmethod
    def list_providers() -> list[str]:
        return ["claude", "openai", "gemini", "openrouter"]

    @staticmethod
    def default_model(provider: str) -> str:
        return LLMFactory._DEFAULT_MODELS.get(provider, "")
