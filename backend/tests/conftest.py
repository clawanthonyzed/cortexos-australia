"""Pytest fixtures for CortexOS test suite."""
from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.jwt import create_access_token
from app.auth.password import hash_password
from app.config import Settings
from app.database import Base
from app.models.user import Role, User

# ── Test settings ─────────────────────────────────────────────────────────────

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    return Settings(
        database_url=TEST_DATABASE_URL,
        redis_url="redis://localhost:6379/15",
        secret_key="test-secret-key-32-chars-minimum!!",
        environment="testing",
        langfuse_enabled=False,
        mem0_use_local=False,
        graphiti_uri="bolt://localhost:7687",
    )


@pytest.fixture(scope="session")
def event_loop_policy():
    return asyncio.DefaultEventLoopPolicy()


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        # SQLite doesn't support pgvector — skip that extension
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def app(test_settings, db_engine) -> FastAPI:
    """FastAPI app configured for testing."""
    from app.main import app as _app
    from app import database as db_module

    # Patch the engine used by the app
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    db_module.AsyncSessionLocal = session_factory
    return _app


@pytest_asyncio.fixture(scope="function")
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


# ── User / auth fixtures ──────────────────────────────────────────────────────

@pytest_asyncio.fixture(scope="function")
async def admin_role(db_session: AsyncSession) -> Role:
    import json
    from app.auth.rbac import ROLE_PERMISSIONS
    role = Role(
        name="admin",
        description="Admin role",
        permissions=json.dumps(ROLE_PERMISSIONS.get("admin", [])),
    )
    db_session.add(role)
    await db_session.commit()
    await db_session.refresh(role)
    return role


@pytest_asyncio.fixture(scope="function")
async def admin_user(db_session: AsyncSession, admin_role: Role) -> User:
    user = User(
        email="admin@cortexos.test",
        hashed_password=hash_password("testpassword123"),
        full_name="Test Admin",
        is_active=True,
        is_superuser=True,
    )
    user.roles.append(admin_role)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def admin_token(admin_user: User) -> str:
    return create_access_token(
        user_id=admin_user.id,
        roles=["admin"],
    )


@pytest.fixture
def auth_headers(admin_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {admin_token}"}
