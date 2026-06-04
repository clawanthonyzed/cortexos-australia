"""AuditLog model for RBAC audit trail."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class AuditLog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "audit_logs"

    # Who performed the action
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # What was done
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Request details
    method: Mapped[str | None] = mapped_column(String(10), nullable=True)
    path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Outcome
    status_code: Mapped[int | None] = mapped_column(nullable=True)
    success: Mapped[bool] = mapped_column(nullable=False, default=True)

    # Diff / context
    before_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    after_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}", server_default="{}")

    # Error details
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User | None"] = relationship("User", back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} on {self.resource_type}/{self.resource_id}>"
