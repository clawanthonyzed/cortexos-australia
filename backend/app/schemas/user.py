"""Pydantic schemas for User and Role."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Role schemas ─────────────────────────────────────────────────────────────

class RoleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: str | None = None
    permissions: list[str] = Field(default_factory=list)


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=50)
    description: str | None = None
    permissions: list[str] | None = None


class RoleRead(RoleBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── User schemas ──────────────────────────────────────────────────────────────

class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$")
    full_name: str | None = Field(None, max_length=255)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    username: str | None = Field(None, min_length=3, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$")
    full_name: str | None = Field(None, max_length=255)
    is_active: bool | None = None


class UserRead(UserBase):
    id: uuid.UUID
    is_active: bool
    is_verified: bool
    last_login_at: datetime | None
    venture_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime
    roles: list[RoleRead] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class UserReadBrief(BaseModel):
    id: uuid.UUID
    email: str
    username: str
    full_name: str | None

    model_config = {"from_attributes": True}


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


# ── Auth schemas ──────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPayload(BaseModel):
    sub: str  # user id
    exp: int
    iat: int
    type: str  # "access" or "refresh"
    roles: list[str] = Field(default_factory=list)
