"""Pydantic schemas for Workflow."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class WorkflowStepBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    step_type: str = Field(default="agent_node")
    config_json: dict[str, Any] = Field(default_factory=dict)
    order: int = Field(default=0, ge=0)
    next_steps: list[str] = Field(default_factory=list)  # node IDs
    node_id: str | None = None


class WorkflowStepCreate(WorkflowStepBase):
    pass


class WorkflowStepRead(WorkflowStepBase):
    id: uuid.UUID
    workflow_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("config_json", mode="before")
    @classmethod
    def parse_config(cls, v):
        if isinstance(v, str):
            try:
                import json as _j; return _j.loads(v)
            except Exception: return {}
        return v or {}

    @field_validator("next_steps", mode="before")
    @classmethod
    def parse_next(cls, v):
        if isinstance(v, str):
            try:
                import json as _j; r = _j.loads(v); return r if isinstance(r, list) else []
            except Exception: return []
        return v or []


class WorkflowBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    graph_json: dict[str, Any] = Field(default_factory=dict)
    trigger_type: str = Field(default="manual")
    cron_expression: str | None = None
    config_json: dict[str, Any] = Field(default_factory=dict)
    venture: str | None = None
    tags: list[str] = Field(default_factory=list)


class WorkflowCreate(WorkflowBase):
    steps: list[WorkflowStepCreate] = Field(default_factory=list)


class WorkflowUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    graph_json: dict[str, Any] | None = None
    trigger_type: str | None = None
    cron_expression: str | None = None
    config_json: dict[str, Any] | None = None
    status: str | None = None
    venture: str | None = None
    tags: list[str] | None = None


class WorkflowRead(WorkflowBase):
    id: uuid.UUID
    status: str
    run_count: int
    success_count: int
    failure_count: int
    last_run_at: datetime | None = None
    last_run_status: str | None = None
    steps: list[WorkflowStepRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("graph_json", "config_json", mode="before")
    @classmethod
    def parse_json_fields(cls, v):
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
                import json as _j; r = _j.loads(v); return r if isinstance(r, list) else []
            except Exception: return []
        return v or []


class WorkflowReadBrief(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    status: str
    trigger_type: str
    run_count: int
    venture: str | None = None
    tags: list[str] = Field(default_factory=list)
    last_run_at: datetime | None = None
    last_run_status: str | None = None
    created_at: datetime

    @field_validator("tags", mode="before")
    @classmethod
    def parse_brief_tags(cls, v):
        if isinstance(v, str):
            try:
                import json as _j; r = _j.loads(v); return r if isinstance(r, list) else []
            except Exception: return []
        return v or []

    model_config = {"from_attributes": True}


class WorkflowExecuteRequest(BaseModel):
    input_data: dict[str, Any] = Field(default_factory=dict)
    async_run: bool = True


class WorkflowExecuteResult(BaseModel):
    workflow_id: uuid.UUID
    run_id: str
    status: str
    celery_task_id: str | None = None
    message: str = ""
