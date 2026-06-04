"""Async SQLAlchemy engine, session factory, and base model."""
from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Any
import uuid

from sqlalchemy import DateTime, event, func, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.config import settings


def _make_engine() -> AsyncEngine:
    return create_async_engine(
        settings.database_url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout,
        echo=settings.db_echo,
        pool_pre_ping=True,  # Reconnect on stale connections
    )


engine: AsyncEngine = _make_engine()

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    # Subclasses declare __tablename__ themselves
    pass


class TimestampMixin:
    """Adds created_at and updated_at to any model."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UUIDMixin:
    """Adds a UUID primary key."""

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides a database session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Create all tables and ensure pgvector extension exists."""
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        # Import all models so they register with Base.metadata
        import app.models  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Dispose the engine connection pool."""
    await engine.dispose()
