"""Role-Based Access Control — permissions and enforcement."""
from __future__ import annotations

from enum import StrEnum
from functools import wraps
from typing import Callable

from fastapi import Depends, HTTPException, status

from app.dependencies import get_current_user
from app.models.user import User


class Permission(StrEnum):
    # Agent permissions
    AGENT_READ = "agent:read"
    AGENT_CREATE = "agent:create"
    AGENT_UPDATE = "agent:update"
    AGENT_DELETE = "agent:delete"
    AGENT_RUN = "agent:run"

    # Task permissions
    TASK_READ = "task:read"
    TASK_CREATE = "task:create"
    TASK_UPDATE = "task:update"
    TASK_DELETE = "task:delete"
    TASK_CANCEL = "task:cancel"

    # Workflow permissions
    WORKFLOW_READ = "workflow:read"
    WORKFLOW_CREATE = "workflow:create"
    WORKFLOW_UPDATE = "workflow:update"
    WORKFLOW_DELETE = "workflow:delete"
    WORKFLOW_RUN = "workflow:run"

    # Memory permissions
    MEMORY_READ = "memory:read"
    MEMORY_WRITE = "memory:write"
    MEMORY_DELETE = "memory:delete"

    # Product permissions
    PRODUCT_READ = "product:read"
    PRODUCT_CREATE = "product:create"
    PRODUCT_UPDATE = "product:update"
    PRODUCT_DELETE = "product:delete"

    # Finance permissions
    FINANCE_READ = "finance:read"
    FINANCE_EXPORT = "finance:export"

    # Venture permissions
    VENTURE_READ = "venture:read"
    VENTURE_WRITE = "venture:write"

    # User management
    USER_READ = "user:read"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    # Integration permissions
    INTEGRATION_READ = "integration:read"
    INTEGRATION_MANAGE = "integration:manage"

    # Admin
    ADMIN_ALL = "admin:*"


# Default permission sets per role
ROLE_PERMISSIONS: dict[str, list[str]] = {
    "admin": [Permission.ADMIN_ALL],
    "operator": [
        Permission.AGENT_READ, Permission.AGENT_CREATE, Permission.AGENT_UPDATE,
        Permission.AGENT_RUN,
        Permission.TASK_READ, Permission.TASK_CREATE, Permission.TASK_UPDATE,
        Permission.TASK_CANCEL,
        Permission.WORKFLOW_READ, Permission.WORKFLOW_CREATE, Permission.WORKFLOW_UPDATE,
        Permission.WORKFLOW_RUN,
        Permission.MEMORY_READ, Permission.MEMORY_WRITE,
        Permission.PRODUCT_READ, Permission.PRODUCT_CREATE, Permission.PRODUCT_UPDATE,
        Permission.FINANCE_READ,
        Permission.INTEGRATION_READ, Permission.INTEGRATION_MANAGE,
        Permission.VENTURE_READ, Permission.VENTURE_WRITE,
    ],
    "viewer": [
        Permission.AGENT_READ,
        Permission.TASK_READ,
        Permission.WORKFLOW_READ,
        Permission.MEMORY_READ,
        Permission.PRODUCT_READ,
        Permission.FINANCE_READ,
        Permission.INTEGRATION_READ,
        Permission.VENTURE_READ,
    ],
}


def _user_has_permission(user: User, permission: str) -> bool:
    """Check if a user has a given permission through any of their roles."""
    for role in user.roles:
        import json
        try:
            perms: list[str] = json.loads(role.permissions)
        except (json.JSONDecodeError, TypeError):
            perms = []

        # Admin wildcard
        if Permission.ADMIN_ALL in perms or "admin:*" in perms:
            return True
        if permission in perms:
            return True
    return False


class RequirePermission:
    """FastAPI dependency that enforces a specific permission."""

    def __init__(self, permission: str) -> None:
        self.permission = permission

    async def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if not _user_has_permission(current_user, self.permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "Forbidden", "detail": {"required_permission": self.permission}},
            )
        return current_user


def require_permission(permission: str) -> RequirePermission:
    """Shorthand factory for RequirePermission dependency."""
    return RequirePermission(permission)


class RequireAnyPermission:
    """FastAPI dependency that requires at least one of the listed permissions."""

    def __init__(self, *permissions: str) -> None:
        self.permissions = permissions

    async def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        for perm in self.permissions:
            if _user_has_permission(current_user, perm):
                return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Forbidden",
                "detail": {"required_any_of": list(self.permissions)},
            },
        )
