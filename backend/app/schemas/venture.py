"""Pydantic schemas for Venture CRUD + health scoring."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class VentureBase(BaseModel):
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    name: str = Field(..., min_length=1, max_length=255)
    manager_name: str = Field(..., min_length=1, max_length=100)
    category: str = Field(default="other", max_length=50)


class VentureCreate(VentureBase):
    pass


class VentureRead(VentureBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    repo_url: str | None = None
    parent_venture_id: uuid.UUID | None = None
    monthly_budget_usd: float | None = None
    target_revenue_monthly_usd: float | None = None
    legacy_docs_path: str | None = None
    status: str = "building"

    model_config = {"from_attributes": True}


class VentureHealth(BaseModel):
    slug: str
    name: str
    manager: str
    category: str
    healthScore: int
    status: str
    tasksLast7d: int
    successRate: float
    agentCount: int
    lastActivityAt: datetime | None = None
