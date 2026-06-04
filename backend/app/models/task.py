"""Task model with status enum, dependencies, and retry logic."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.agent import Agent


class TaskStatus:
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class TaskPriority:
    LOW = 1
    MEDIUM = 5
    HIGH = 8
    CRITICAL = 10


class Task(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "tasks"

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    input_data: Mapped[str] = mapped_column(Text, nullable=False, default="{}", server_default="{}")

    # Assignment
    agent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("agents.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Status & lifecycle
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=TaskStatus.PENDING, index=True
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=TaskPriority.MEDIUM)

    # Scheduling
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Results
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_traceback: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Retry logic
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)

    # Celery task tracking
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Hierarchy — self-referential FK for sub-tasks
    parent_task_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Workflow membership
    workflow_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("workflows.id", ondelete="SET NULL"), nullable=True, index=True
    )
    workflow_step_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("workflow_steps.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    agent: Mapped["Agent | None"] = relationship("Agent", back_populates="tasks")
    subtasks: Mapped[list["Task"]] = relationship(
        "Task", back_populates="parent_task", foreign_keys=[parent_task_id]
    )
    parent_task: Mapped["Task | None"] = relationship(
        "Task", back_populates="subtasks", remote_side="Task.id", foreign_keys=[parent_task_id]
    )

    def __repr__(self) -> str:
        return f"<Task {self.title[:40]} ({self.status})>"
