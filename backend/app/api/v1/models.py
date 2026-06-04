"""LLM model listing and token usage endpoints."""
from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import Permission, require_permission
from app.dependencies import get_db
from app.llm.factory import LLMFactory
from app.models.cost_record import CostRecord
from app.models.user import User

logger = structlog.get_logger(__name__)
router = APIRouter()


_MODEL_CATALOG = {
    "claude": [
        {"id": "claude-sonnet-4-6", "name": "Claude Sonnet 4.6", "default": True, "context_window": 200000},
        {"id": "claude-opus-4-5", "name": "Claude Opus 4.5", "context_window": 200000},
        {"id": "claude-haiku-3-5", "name": "Claude Haiku 3.5", "context_window": 200000},
    ],
    "openai": [
        {"id": "gpt-4o", "name": "GPT-4o", "default": True, "context_window": 128000},
        {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "context_window": 128000},
        {"id": "o1", "name": "o1", "context_window": 128000},
    ],
    "gemini": [
        {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash", "default": True, "context_window": 1000000},
        {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro", "context_window": 1000000},
    ],
    "openrouter": [
        {"id": "anthropic/claude-sonnet-4-6", "name": "Claude Sonnet 4.6 (OR)", "default": True},
        {"id": "openai/gpt-4o", "name": "GPT-4o (OR)"},
        {"id": "google/gemini-2.5-flash", "name": "Gemini 2.5 Flash (OR)"},
        {"id": "meta-llama/llama-3.1-70b-instruct", "name": "Llama 3.1 70B (OR)"},
        {"id": "mistralai/mixtral-8x7b", "name": "Mixtral 8x7B (OR)"},
    ],
}


@router.get("", tags=["models"])
async def list_models(
    provider: str | None = Query(None),
    current_user: User = Depends(require_permission(Permission.AGENT_READ)),
) -> dict[str, Any]:
    """List all available LLM models, optionally filtered by provider."""
    if provider:
        models = _MODEL_CATALOG.get(provider, [])
        return {"provider": provider, "models": models}

    return {
        "providers": LLMFactory.list_providers(),
        "catalog": _MODEL_CATALOG,
    }


@router.get("/usage", tags=["models"])
async def token_usage_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.FINANCE_READ)),
    days: int = Query(default=7, ge=1, le=90),
) -> dict[str, Any]:
    """Aggregate token usage and cost by provider and model."""
    from datetime import datetime, timedelta, timezone

    start_dt = datetime.now(tz=timezone.utc) - timedelta(days=days)

    rows = await db.execute(
        select(
            CostRecord.provider,
            CostRecord.model,
            func.sum(CostRecord.total_tokens).label("total_tokens"),
            func.sum(CostRecord.prompt_tokens).label("prompt_tokens"),
            func.sum(CostRecord.completion_tokens).label("completion_tokens"),
            func.sum(CostRecord.cache_creation_tokens).label("cache_creation"),
            func.sum(CostRecord.cache_read_tokens).label("cache_read"),
            func.sum(CostRecord.cost_usd).label("cost_usd"),
            func.count(CostRecord.id).label("call_count"),
        )
        .where(CostRecord.created_at >= start_dt)
        .group_by(CostRecord.provider, CostRecord.model)
        .order_by(func.sum(CostRecord.cost_usd).desc())
    )

    usage = [
        {
            "provider": row.provider,
            "model": row.model,
            "total_tokens": int(row.total_tokens or 0),
            "prompt_tokens": int(row.prompt_tokens or 0),
            "completion_tokens": int(row.completion_tokens or 0),
            "cache_creation_tokens": int(row.cache_creation or 0),
            "cache_read_tokens": int(row.cache_read or 0),
            "cost_usd": round(float(row.cost_usd or 0), 6),
            "call_count": int(row.call_count or 0),
        }
        for row in rows
    ]

    total_cost = sum(u["cost_usd"] for u in usage)
    total_tokens = sum(u["total_tokens"] for u in usage)

    return {
        "period_days": days,
        "total_cost_usd": round(total_cost, 6),
        "total_tokens": total_tokens,
        "by_model": usage,
    }
