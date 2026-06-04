"""Pydantic schemas for Workflow."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


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


class WorkflowBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    graph_json: dict[str, Any] = Field(default_factory=dict)
    trigger_type: str = Field(default="manual")
    cron_expression: str | None = None
    config_json: dict[str, Any] = Field(default_factory=dict)


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


class WorkflowRead(WorkflowBase):
    id: uuid.UUID
    status: str
    run_count: int
    success_count: int
    failure_count: int
    steps: list[WorkflowStepRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WorkflowReadBrief(BaseModel):
    id: uuid.UUID
    name: str
    status: str
    trigger_type: str
    run_count: int
    created_at: datetime

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
