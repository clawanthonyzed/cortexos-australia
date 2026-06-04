"""FastAPI dependency functions."""
from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import AsyncSessionLocal
from app.models.user import User

_bearer = HTTPBearer(auto_error=True)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide an async database session for each request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Validate the Bearer token and return the authenticated User.
    Loads the user's roles eagerly.
    """
    from app.auth.jwt import decode_token

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"error": "Could not validate credentials"},
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise credentials_exception
        user_id_str: str = payload.get("sub", "")
        if not user_id_str:
            raise credentials_exception
        user_id = uuid.UUID(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception

    result = await db.execute(
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.user_roles).selectinload("role"))
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "Account is deactivated"},
        )

    return user


async def get_current_active_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require that the current user has the admin role."""
    role_names = [r.name for r in current_user.roles]
    if "admin" not in role_names:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "Admin role required"},
        )
    return current_user


def paginate(page: int = 1, page_size: int = 20) -> dict[str, int]:
    """Standard pagination dependency — returns offset and limit."""
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    return {"offset": (page - 1) * page_size, "limit": page_size, "page": page, "page_size": page_size}
