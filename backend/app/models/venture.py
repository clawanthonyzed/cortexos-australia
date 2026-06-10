"""Venture model — empire venture registry for multi-tenant workspaces."""
from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, TimestampMixin, UUIDMixin


class Venture(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ventures"

    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    manager_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="other", server_default="other")

    def __repr__(self) -> str:
        return f"<Venture {self.slug} ({self.manager_name})>"
