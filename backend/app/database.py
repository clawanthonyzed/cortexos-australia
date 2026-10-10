"""Async SQLAlchemy engine, session factory, and base model."""
from __future__ import annotations

import os
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
from sqlalchemy.pool import NullPool

from app.config import settings


def _make_engine() -> AsyncEngine:
    # Celery runs every task in a brand-new event loop (asyncio.new_event_loop). Pooled asyncpg
    # connections are bound to the loop that opened them, so each task left its connections
    # stranded: 93 of Postgres's 100 slots were held by the worker on 2026-10-10 ("too many
    # clients already"). Workers set CORTEXOS_DB_NULLPOOL=1: one connection per session,
    # closed when the session closes. The web server keeps its normal pool.
    if os.environ.get("CORTEXOS_DB_NULLPOOL") == "1":
        return create_async_engine(settings.database_url, poolclass=NullPool, echo=settings.db_echo)
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
