"""Agent model."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.task import Task
    from app.models.cost_record import CostRecord


class AgentStatus:
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    DISABLED = "disabled"


class Agent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "agents"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # LLM configuration
    model_provider: Mapped[str] = mapped_column(String(50), nullable=False, default="claude")
    model_name: Mapped[str] = mapped_column(String(100), nullable=False, default="claude-sonnet-4-6")
    temperature: Mapped[float] = mapped_column(Float, nullable=False, default=0.7)
    max_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=4096)

    # Agent config (tools, memory settings, etc.) as JSON string
    config_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}", server_default="{}")

    # System prompt override
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=AgentStatus.IDLE, index=True
    )

    # Metrics
    total_tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_cost_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    success_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Classification
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False, default="custom")
    tags: Mapped[str] = mapped_column(Text, nullable=False, default="[]", server_default="[]")

    # Relationships
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="agent")
    cost_records: Mapped[list["CostRecord"]] = relationship("CostRecord", back_populates="agent")

    def __repr__(self) -> str:
        return f"<Agent {self.name} ({self.status})>"
