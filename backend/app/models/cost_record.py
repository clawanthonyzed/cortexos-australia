"""CostRecord model for tracking LLM token usage and costs."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.agent import Agent


class CostRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "cost_records"

    # What generated this cost
    agent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("agents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True
    )
    workflow_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("workflows.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # LLM details
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Token breakdown
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Cache tokens (Anthropic prompt caching)
    cache_creation_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cache_read_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Cost in USD
    cost_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Langfuse trace reference
    trace_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    # Optional label for grouping (e.g. "research_phase", "generation")
    label: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    agent: Mapped["Agent | None"] = relationship("Agent", back_populates="cost_records")

    def __repr__(self) -> str:
        return f"<CostRecord {self.provider}/{self.model} ${self.cost_usd:.4f}>"
