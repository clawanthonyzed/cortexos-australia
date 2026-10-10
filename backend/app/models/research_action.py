"""ResearchAction model — tracks insight -> approval -> outcome for the research loop."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, TimestampMixin, UUIDMixin


class ActionStatus:
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ResearchAction(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "research_actions"

    venture_slug: Mapped[str] = mapped_column(String(64), index=True)
    mm_post_id: Mapped[str] = mapped_column(String(64), index=True)
    mm_channel_id: Mapped[str] = mapped_column(String(64))

    insight: Mapped[str] = mapped_column(Text)
    action: Mapped[str] = mapped_column(Text)
    action_type: Mapped[str] = mapped_column(String(64))
    confidence: Mapped[float] = mapped_column(Float, default=0.5)

    status: Mapped[str] = mapped_column(String(16), default=ActionStatus.PENDING, index=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    reminder_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reminder_sent: Mapped[bool] = mapped_column(default=False)

    outcome_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    outcome_captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    draft_posted: Mapped[bool] = mapped_column(default=False)
