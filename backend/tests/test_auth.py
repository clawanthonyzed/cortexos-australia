"""Auth + RBAC tests."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.auth.jwt import create_access_token, create_refresh_token, decode_token
from app.auth.password import hash_password, verify_password
import uuid


# ── Password hashing ──────────────────────────────────────────────────────────

def test_hash_password_produces_different_hashes() -> None:
    h1 = hash_password("secret")
    h2 = hash_password("secret")
    assert h1 != h2  # bcrypt uses random salt


def test_verify_password_correct() -> None:
    hashed = hash_password("correcthorse")
    assert verify_password("correcthorse", hashed) is True


def test_verify_password_wrong() -> None:
    hashed = hash_password("correcthorse")
    assert verify_password("wrong", hashed) is False


# ── JWT ───────────────────────────────────────────────────────────────────────

def test_access_token_roundtrip() -> None:
    user_id = uuid.uuid4()
    token = create_access_token(user_id=user_id, roles=["admin"])
    payload = decode_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["type"] == "access"
    assert "admin" in payload["roles"]


def test_refresh_token_roundtrip() -> None:
    user_id = uuid.uuid4()
    token = create_refresh_token(user_id=user_id)
    payload = decode_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["type"] == "refresh"


def test_invalid_token_raises() -> None:
    from jose import JWTError
    with pytest.raises(JWTError):
        decode_token("not.a.token")


# ── Auth endpoints ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, admin_user) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@cortexos.test", "password": "testpassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, admin_user) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@cortexos.test", "password": "wrongpassword"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_user(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "ghost@cortexos.test", "password": "anything"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_no_token(client: AsyncClient) -> None:
    response = await client.get("/api/v1/agents/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_with_token(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.get("/api/v1/agents/", headers=auth_headers)
    assert response.status_code == 200
