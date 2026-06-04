"""Pydantic schemas for Memory."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class MemoryItemCreate(BaseModel):
    content: str = Field(..., min_length=1)
    summary: str | None = None
    memory_type: str = Field(default="short_term")
    category: str | None = None
    tags: list[str] = Field(default_factory=list)
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0)
    agent_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None


class MemoryItemUpdate(BaseModel):
    content: str | None = None
    summary: str | None = None
    memory_type: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    importance_score: float | None = Field(None, ge=0.0, le=1.0)


class MemoryItemRead(BaseModel):
    id: uuid.UUID
    content: str
    summary: str | None
    memory_type: str
    category: str | None
    tags: list[str]
    importance_score: float
    access_count: int
    agent_id: uuid.UUID | None
    user_id: uuid.UUID | None
    external_id: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MemorySearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    agent_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    memory_type: str | None = None
    category: str | None = None
    limit: int = Field(default=10, ge=1, le=100)
    min_importance: float = Field(default=0.0, ge=0.0, le=1.0)


class MemorySearchResult(BaseModel):
    item: MemoryItemRead
    score: float
    distance: float | None = None


class MemorySearchResponse(BaseModel):
    results: list[MemorySearchResult]
    query: str
    total: int
