"""JWT token creation, verification, and refresh."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.config import settings


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


def create_access_token(
    user_id: uuid.UUID,
    roles: list[str],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a short-lived JWT access token."""
    expire = _utcnow() + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "exp": int(expire.timestamp()),
        "iat": int(_utcnow().timestamp()),
        "type": "access",
        "roles": roles,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(
    user_id: uuid.UUID,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a long-lived JWT refresh token."""
    expire = _utcnow() + (
        expires_delta or timedelta(days=settings.refresh_token_expire_days)
    )
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "exp": int(expire.timestamp()),
        "iat": int(_utcnow().timestamp()),
        "type": "refresh",
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT token.

    Raises:
        JWTError: if the token is invalid, expired, or malformed.
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        return payload
    except JWTError:
        raise


def get_token_user_id(token: str) -> uuid.UUID:
    """Extract user ID from a validated token."""
    payload = decode_token(token)
    return uuid.UUID(payload["sub"])


def get_token_roles(token: str) -> list[str]:
    """Extract roles from a validated access token."""
    payload = decode_token(token)
    return payload.get("roles", [])
