"""Auth endpoints — login, refresh, logout, register."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.jwt import create_access_token, create_refresh_token, decode_token
from app.auth.password import hash_password, verify_password
from app.auth.rbac import ROLE_PERMISSIONS
from app.dependencies import get_current_user, get_db
from app.models.audit_log import AuditLog
from app.models.user import Role, User, UserRole
from app.schemas.user import (
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UserCreate,
    UserRead,
)

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    tags=["auth"],
)
async def register(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    """Register a new user. Assigns 'viewer' role by default."""
    # Check uniqueness
    existing = await db.execute(
        select(User).where(
            (User.email == payload.email) | (User.username == payload.username)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "Email or username already registered"},
        )

    # Ensure viewer role exists
    role_result = await db.execute(select(Role).where(Role.name == "viewer"))
    viewer_role = role_result.scalar_one_or_none()
    if not viewer_role:
        viewer_role = Role(
            name="viewer",
            permissions=json.dumps(ROLE_PERMISSIONS.get("viewer", [])),
        )
        db.add(viewer_role)
        await db.flush()

    user = User(
        email=payload.email,
        username=payload.username,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    await db.flush()

    user_role = UserRole(user_id=user.id, role_id=viewer_role.id)
    db.add(user_role)
    await db.flush()

    await db.refresh(user)
    result = await db.execute(
        select(User)
        .where(User.id == user.id)
        .options(selectinload(User.user_roles).selectinload(UserRole.role))
    )
    user = result.scalar_one()

    logger.info("User registered", user_id=str(user.id), email=user.email)
    return UserRead.model_validate(user)


@router.post("/login", response_model=TokenResponse, tags=["auth"])
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticate and return access + refresh tokens."""
    result = await db.execute(
        select(User)
        .where(User.email == payload.email)
        .options(selectinload(User.user_roles).selectinload(UserRole.role))
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid credentials"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "Account is deactivated"},
        )

    roles = [r.name for r in user.roles]
    access_token = create_access_token(user.id, roles)
    refresh_token = create_refresh_token(user.id)

    # Store hash of refresh token for revocation
    user.refresh_token_hash = hash_password(refresh_token)
    user.last_login_at = datetime.now(tz=timezone.utc)
    await db.flush()

    # Audit log
    audit = AuditLog(
        user_id=user.id,
        action="login",
        resource_type="user",
        resource_id=str(user.id),
        method="POST",
        path="/api/v1/auth/login",
        ip_address=request.client.host if request.client else None,
        success=True,
    )
    db.add(audit)

    from app.config import settings
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/refresh", response_model=TokenResponse, tags=["auth"])
async def refresh_token(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Exchange a refresh token for a new access token."""
    from jose import JWTError

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"error": "Invalid or expired refresh token"},
    )

    try:
        token_data = decode_token(payload.refresh_token)
        if token_data.get("type") != "refresh":
            raise credentials_exception
        user_id = uuid.UUID(token_data["sub"])
    except (JWTError, ValueError):
        raise credentials_exception

    result = await db.execute(
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.user_roles).selectinload(UserRole.role))
    )
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise credentials_exception

    if not user.refresh_token_hash or not verify_password(
        payload.refresh_token, user.refresh_token_hash
    ):
        raise credentials_exception

    roles = [r.name for r in user.roles]
    access_token = create_access_token(user.id, roles)
    new_refresh_token = create_refresh_token(user.id)
    user.refresh_token_hash = hash_password(new_refresh_token)
    await db.flush()

    from app.config import settings
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, response_model=None, tags=["auth"])
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Revoke the refresh token."""
    current_user.refresh_token_hash = None
    await db.flush()
    logger.info("User logged out", user_id=str(current_user.id))


@router.get("/me", response_model=UserRead, tags=["auth"])
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    """Get the current authenticated user's profile."""
    result = await db.execute(
        select(User)
        .where(User.id == current_user.id)
        .options(selectinload(User.user_roles).selectinload(UserRole.role))
    )
    user = result.scalar_one()
    return UserRead.model_validate(user)
