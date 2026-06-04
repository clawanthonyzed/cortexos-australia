"""Workflow and WorkflowStep models."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.task import Task


class WorkflowStatus:
    DRAFT = "draft"
    ACTIVE = "active"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    ARCHIVED = "archived"


class WorkflowTrigger:
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    WEBHOOK = "webhook"
    EVENT = "event"


class Workflow(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "workflows"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # React Flow compatible graph definition (JSON)
    graph_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}", server_default="{}")

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=WorkflowStatus.DRAFT, index=True
    )
    trigger_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default=WorkflowTrigger.MANUAL
    )

    # Cron expression for scheduled triggers
    cron_expression: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Config / variables
    config_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}", server_default="{}")

    # Run statistics
    run_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    steps: Mapped[list["WorkflowStep"]] = relationship(
        "WorkflowStep", back_populates="workflow", cascade="all, delete-orphan",
        order_by="WorkflowStep.order"
    )
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="workflow")  # type: ignore[assignment]

    def __repr__(self) -> str:
        return f"<Workflow {self.name} ({self.status})>"


class WorkflowStep(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "workflow_steps"

    workflow_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Step type: agent_node | condition_node | human_approval | scheduled_node
    step_type: Mapped[str] = mapped_column(String(50), nullable=False, default="agent_node")

    # Step configuration as JSON
    config_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}", server_default="{}")

    # Execution order within workflow
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Next step IDs (JSON array for branching)
    next_steps_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]", server_default="[]")

    # The React Flow node id this step maps to
    node_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    workflow: Mapped["Workflow"] = relationship("Workflow", back_populates="steps")
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="workflow_step")  # type: ignore[assignment]

    def __repr__(self) -> str:
        return f"<WorkflowStep {self.name} (order={self.order})>"
