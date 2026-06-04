"""Pydantic schemas for Task."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    input_data: dict[str, Any] = Field(default_factory=dict)
    agent_id: uuid.UUID | None = None
    priority: int = Field(default=5, ge=1, le=10)
    scheduled_at: datetime | None = None
    max_retries: int = Field(default=3, ge=0, le=10)
    parent_task_id: uuid.UUID | None = None
    workflow_id: uuid.UUID | None = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    input_data: dict[str, Any] | None = None
    agent_id: uuid.UUID | None = None
    priority: int | None = Field(None, ge=1, le=10)
    scheduled_at: datetime | None = None
    max_retries: int | None = Field(None, ge=0, le=10)
    status: str | None = None


class TaskRead(TaskBase):
    id: uuid.UUID
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    result_json: dict[str, Any] | None = None
    error_message: str | None = None
    retry_count: int
    celery_task_id: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskReadBrief(BaseModel):
    id: uuid.UUID
    title: str
    status: str
    priority: int
    agent_id: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TaskExecuteRequest(BaseModel):
    """Trigger immediate execution of an existing task."""
    async_run: bool = True
    override_agent_id: uuid.UUID | None = None


class TaskRetryRequest(BaseModel):
    reset_input: dict[str, Any] | None = None
