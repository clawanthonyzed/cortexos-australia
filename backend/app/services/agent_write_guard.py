"""SPEC-COS-16 — lightweight write guards for agent-service memory/KG writes.

Deliberately not a review queue: two cheap Redis checks, both O(1), neither
blocks a legitimate write. Rate limit stops a runaway loop from flooding the
table; the dedupe check stops a stuck loop from writing the same content
over and over without needing the agent to handle a new error case.
"""
from __future__ import annotations

import hashlib

import redis.asyncio as aioredis
import structlog
from fastapi import HTTPException, status

from app.config import settings

logger = structlog.get_logger(__name__)

_redis: aioredis.Redis | None = None


def _get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url)
    return _redis


async def enforce_rate_limit(agent_id: str) -> None:
    """Sliding-window cap on writes/agent/hour. Raises 429 past the limit."""
    key = f"agent-write-rate:{agent_id}"
    try:
        r = _get_redis()
        count = await r.incr(key)
        if count == 1:
            await r.expire(key, 3600)
    except Exception:
        # Redis unreachable — fail open. A rate-limit outage shouldn't take
        # down agent writes; Hex's traefik/network review covers the actual
        # abuse-prevention boundary (internal-only exposure).
        logger.warning("agent_write_guard: redis unavailable, rate limit skipped")
        return

    if count > settings.agent_write_rate_limit_per_hour:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"error": "Agent write rate limit exceeded", "limit_per_hour": settings.agent_write_rate_limit_per_hour},
        )


async def is_recent_duplicate(agent_id: str, content: str) -> bool:
    """
    True if this exact (agent, content) pair was written within the dedupe
    window — caller should silently skip the write, not error.
    """
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()[:24]
    key = f"agent-write-dedupe:{agent_id}:{content_hash}"
    try:
        r = _get_redis()
        # SET ... NX returns True only if the key didn't already exist.
        was_set = await r.set(key, "1", nx=True, ex=settings.agent_write_dedupe_window_seconds)
        return not was_set
    except Exception:
        logger.warning("agent_write_guard: redis unavailable, dedupe check skipped")
        return False
