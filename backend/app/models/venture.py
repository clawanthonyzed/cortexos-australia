"""Venture model — empire venture registry for multi-tenant workspaces."""
from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, TimestampMixin, UUIDMixin


class Venture(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ventures"

    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    manager_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="other", server_default="other")

    # Governance registry (added 0006/0007)
    repo_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    parent_venture_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("ventures.id", ondelete="SET NULL"), nullable=True
    )
    monthly_budget_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_revenue_monthly_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    legacy_docs_path: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="building", server_default="building")

    def __repr__(self) -> str:
        return f"<Venture {self.slug} ({self.manager_name})>"
