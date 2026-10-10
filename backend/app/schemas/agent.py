"""Pydantic schemas for Agent CRUD."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class AgentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    purpose: str = Field(..., min_length=1)
    description: str | None = None
    model_provider: str = Field(default="claude", pattern=r"^(claude|openai|gemini|openrouter)$")
    model_name: str = Field(default="claude-sonnet-4-6", max_length=100)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1, le=200000)
    config_json: dict[str, Any] = Field(default_factory=dict)
    system_prompt: str | None = None
    agent_type: str = Field(default="custom", max_length=50)
    tags: list[str] = Field(default_factory=list)


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    purpose: str | None = None
    description: str | None = None
    model_provider: str | None = Field(None, pattern=r"^(claude|openai|gemini|openrouter)$")
    model_name: str | None = None
    temperature: float | None = Field(None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(None, ge=1, le=200000)
    config_json: dict[str, Any] | None = None
    system_prompt: str | None = None
    tags: list[str] | None = None
    status: str | None = None


class AgentRead(AgentBase):
    id: uuid.UUID
    status: str
    total_tokens_used: int
    total_cost_usd: float
    success_count: int
    error_count: int
    last_run_at: datetime | None
    created_at: datetime
    updated_at: datetime
    venture_name: str | None = None
    role_tier: str = "worker"
    reporting_manager_id: uuid.UUID | None = None
    repo_path: str | None = None
    working_directory: str | None = None
    permitted_tools: list[str] = Field(default_factory=list)
    permitted_services: list[str] = Field(default_factory=list)
    monthly_budget_usd: float | None = None

    model_config = {"from_attributes": True}

    @field_validator("permitted_tools", "permitted_services", mode="before")
    @classmethod
    def parse_gov_lists(cls, v):
        if isinstance(v, str):
            try:
                import json as _j; r = _j.loads(v); return r if isinstance(r, list) else [r]
            except Exception: return []
        return v or []

    @field_validator("config_json", mode="before")
    @classmethod
    def parse_config(cls, v):
        if isinstance(v, str):
            try:
                import json as _j; return _j.loads(v)
            except Exception: return {}
        return v or {}

    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, v):
        if isinstance(v, str):
            try:
                import json as _j; result = _j.loads(v); return result if isinstance(result, list) else [result]
            except Exception: return [v] if v else []
        return v or []


class AgentReadBrief(BaseModel):
    id: uuid.UUID
    name: str
    purpose: str
    status: str
    model_provider: str
    model_name: str
    agent_type: str
    tags: list[str] = Field(default_factory=list)
    role_tier: str = "worker"
    venture_name: str | None = None
    reporting_manager_id: uuid.UUID | None = None
    repo_path: str | None = None
    monthly_budget_usd: float | None = None

    model_config = {"from_attributes": True}

    @field_validator("tags", mode="before")
    @classmethod
    def parse_brief_tags(cls, v):
        if isinstance(v, str):
            try:
                import json as _j; r = _j.loads(v); return r if isinstance(r, list) else [r]
            except Exception: return [v] if v and v != "[]" else []
        return v or []


class AgentRunRequest(BaseModel):
    task: str = Field(..., min_length=1)
    context: dict[str, Any] = Field(default_factory=dict)
    max_iterations: int = Field(default=10, ge=1, le=100)
    async_run: bool = True  # If True, dispatch to Celery


class AgentRunResult(BaseModel):
    agent_id: uuid.UUID
    task_id: uuid.UUID | None = None
    celery_task_id: str | None = None
    status: str
    result: Any | None = None
    error: str | None = None
    tokens_used: int = 0
    cost_usd: float = 0.0
    duration_seconds: float = 0.0


class AgentCloneRequest(BaseModel):
    new_name: str = Field(..., min_length=1, max_length=100)
    new_purpose: str | None = None
