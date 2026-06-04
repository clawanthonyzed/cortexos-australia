"""LLM factory + provider tests (all external calls mocked)."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.llm.factory import LLMFactory
from app.llm.base import BaseLLM, LLMResponse


def test_factory_creates_claude() -> None:
    llm = LLMFactory.create("claude")
    assert llm is not None
    assert llm.provider == "claude"


def test_factory_creates_openai() -> None:
    llm = LLMFactory.create("openai")
    assert llm.provider == "openai"


def test_factory_creates_gemini() -> None:
    llm = LLMFactory.create("gemini")
    assert llm.provider == "gemini"


def test_factory_creates_openrouter() -> None:
    llm = LLMFactory.create("openrouter")
    assert llm.provider == "openrouter"


def test_factory_unknown_provider_raises() -> None:
    with pytest.raises(ValueError, match="Unknown provider"):
        LLMFactory.create("fakeprovider")


def test_factory_custom_model() -> None:
    llm = LLMFactory.create("claude", model="claude-opus-4-7")
    assert llm.model == "claude-opus-4-7"


@pytest.mark.asyncio
async def test_claude_complete_mocked() -> None:
    from app.llm.claude import ClaudeLLM

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Hello from Claude")]
    mock_response.usage.input_tokens = 10
    mock_response.usage.output_tokens = 5
    mock_response.model = "claude-sonnet-4-6"

    with patch("anthropic.AsyncAnthropic") as mock_client_cls:
        instance = mock_client_cls.return_value
        instance.messages.create = AsyncMock(return_value=mock_response)

        llm = ClaudeLLM(model="claude-sonnet-4-6")
        llm._client = instance
        result = await llm.complete(messages=[{"role": "user", "content": "Hello"}])

    assert isinstance(result, LLMResponse)
    assert result.content == "Hello from Claude"
    assert result.input_tokens == 10
    assert result.output_tokens == 5


@pytest.mark.asyncio
async def test_openai_complete_mocked() -> None:
    from app.llm.openai import OpenAILLM

    mock_message = MagicMock()
    mock_message.content = "Hello from OpenAI"
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_usage = MagicMock()
    mock_usage.prompt_tokens = 8
    mock_usage.completion_tokens = 4
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage = mock_usage
    mock_response.model = "gpt-4o"

    with patch("openai.AsyncOpenAI") as mock_client_cls:
        instance = mock_client_cls.return_value
        instance.chat.completions.create = AsyncMock(return_value=mock_response)

        llm = OpenAILLM(model="gpt-4o")
        llm._client = instance
        result = await llm.complete(messages=[{"role": "user", "content": "Hello"}])

    assert isinstance(result, LLMResponse)
    assert result.content == "Hello from OpenAI"
