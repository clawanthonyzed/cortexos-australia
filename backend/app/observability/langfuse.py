"""Langfuse client wrapper with trace decorator."""
from __future__ import annotations

import functools
import time
import uuid
from collections.abc import Callable
from typing import Any, TypeVar

import structlog

from app.config import settings

logger = structlog.get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])

# Lazy singleton
_client: Any = None


def _get_client() -> Any:
    """Return the Langfuse client, creating it on first call."""
    global _client
    if _client is not None:
        return _client

    if not settings.langfuse_enabled or not settings.langfuse_secret_key:
        return None

    try:
        from langfuse import Langfuse  # type: ignore[import]

        _client = Langfuse(
            secret_key=settings.langfuse_secret_key,
            public_key=settings.langfuse_public_key,
            host=settings.langfuse_host,
        )
        logger.info("Langfuse client initialised", host=settings.langfuse_host)
    except ImportError:
        logger.warning("langfuse package not installed — observability disabled")
        _client = None
    except Exception as exc:
        logger.error("Failed to initialise Langfuse", error=str(exc))
        _client = None

    return _client


class LangfuseTracer:
    """Thin wrapper around Langfuse for tracing LLM calls."""

    def __init__(self, name: str, metadata: dict[str, Any] | None = None) -> None:
        self.name = name
        self.metadata = metadata or {}
        self._trace: Any = None
        self._client = _get_client()

    def __enter__(self) -> "LangfuseTracer":
        if self._client:
            try:
                self._trace = self._client.trace(
                    name=self.name,
                    metadata=self.metadata,
                    id=str(uuid.uuid4()),
                )
            except Exception as exc:
                logger.warning("Langfuse trace creation failed", error=str(exc))
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._trace and exc_type is not None:
            try:
                self._trace.update(status="error", status_message=str(exc_val))
            except Exception:
                pass
        self.flush()

    @property
    def trace_id(self) -> str | None:
        if self._trace:
            return self._trace.id
        return None

    def log_generation(
        self,
        name: str,
        model: str,
        prompt: str | list[Any],
        completion: str,
        usage: dict[str, int] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Log a single LLM generation to the current trace."""
        if not self._trace:
            return
        try:
            self._trace.generation(
                name=name,
                model=model,
                input=prompt,
                output=completion,
                usage=usage,
                metadata=metadata or {},
            )
        except Exception as exc:
            logger.warning("Langfuse generation logging failed", error=str(exc))

    def flush(self) -> None:
        if self._client:
            try:
                self._client.flush()
            except Exception:
                pass


def trace(name: str | None = None, capture_input: bool = True, capture_output: bool = True) -> Callable[[F], F]:
    """
    Decorator that wraps an async function in a Langfuse trace.
    Usage:
        @trace("my-agent-step")
        async def my_step(x: int) -> str: ...
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            trace_name = name or func.__qualname__
            client = _get_client()

            if not client:
                return await func(*args, **kwargs)

            t0 = time.perf_counter()
            try:
                tr = client.trace(name=trace_name, id=str(uuid.uuid4()))
                result = await func(*args, **kwargs)
                elapsed = time.perf_counter() - t0
                tr.update(
                    metadata={"duration_seconds": round(elapsed, 3)},
                    status="success",
                )
                client.flush()
                return result
            except Exception as exc:
                elapsed = time.perf_counter() - t0
                try:
                    tr.update(
                        status="error",
                        status_message=str(exc),
                        metadata={"duration_seconds": round(elapsed, 3)},
                    )
                    client.flush()
                except Exception:
                    pass
                raise

        return wrapper  # type: ignore[return-value]
    return decorator


def get_tracer(name: str, metadata: dict[str, Any] | None = None) -> LangfuseTracer:
    """Factory for context-manager-style tracing."""
    return LangfuseTracer(name=name, metadata=metadata)
