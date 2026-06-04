"""MemoryItem model with pgvector embedding."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, TimestampMixin, UUIDMixin

try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False
    Vector = None  # type: ignore[assignment,misc]


class MemoryType:
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


class MemoryItem(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "memory_items"

    # Owner (agent or user)
    agent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"), nullable=True, index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Classification
    memory_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default=MemoryType.SHORT_TERM, index=True
    )
    category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    tags: Mapped[str] = mapped_column(Text, nullable=False, default="[]", server_default="[]")

    # Vector embedding (1536 dims for OpenAI, 1024 for Claude)
    # Stored as text when pgvector not available
    embedding_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    embedding_dims: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relevance scoring
    importance_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    access_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Source tracking
    source_task_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True
    )

    # External memory system reference (mem0 memory_id)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    def __repr__(self) -> str:
        return f"<MemoryItem {self.memory_type} | {self.content[:50]}>"
