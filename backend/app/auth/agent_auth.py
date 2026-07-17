"""SPEC-COS-16 — agent-service write authentication.

Separate from app.auth.jwt (human dashboard login). Agents authenticate with
a single shared internal token (never routed through the public Traefik
route — internal Docker network only) plus an asserted agent name. The name
is resolved server-side against the `agents` table; nothing from the caller
about agent_id/venture_id/is_specialist is trusted beyond that lookup, which
is what stops one agent from writing as another.

NOTE: agents.venture_id (the SPEC-COS-04 FK) is populated for only 9/337
rows — it is not the real source of venture ownership. In practice venture
ownership lives in agents.tags, a bare string ("specialist" or a venture
slug like "bloom-bub"), not the JSON list the column comment implies.
Resolve venture from tags first, fall back to the FK if tags don't match a
known venture slug.
"""
from __future__ import annotations

import hmac
import json
from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import Permission, RequirePermission
from app.config import settings
from app.dependencies import get_current_user, get_db
from app.models.agent import Agent
from app.models.user import User
from app.models.venture import Venture


@dataclass
class AgentIdentity:
    agent_id: str
    name: str
    venture_id: str | None
    venture_slug: str | None
    is_specialist: bool


def _parse_tags(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [str(t) for t in parsed]
    except (json.JSONDecodeError, TypeError):
        pass
    # Not JSON — treat as a single bare tag (the common case in this table).
    stripped = raw.strip()
    return [stripped] if stripped and stripped != "[]" else []


async def get_agent_identity(
    authorization: str | None = Header(default=None),
    x_agent_name: str | None = Header(default=None, alias="X-Agent-Name"),
    db: AsyncSession = Depends(get_db),
) -> AgentIdentity | None:
    """
    Resolve caller as an agent-service identity, or return None if this
    request isn't using agent-service auth (falls through to human JWT auth
    at the call site).
    """
    if not authorization or not x_agent_name:
        return None
    if not settings.agent_write_token:
        return None

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    if not hmac.compare_digest(token, settings.agent_write_token):
        # Looked like an agent-token request but the token is wrong —
        # fail loudly rather than silently falling through to JWT auth,
        # which would just produce a confusing 401 from the wrong layer.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid agent write token"},
        )

    result = await db.execute(select(Agent).where(Agent.name == x_agent_name))
    agent = result.scalar_one_or_none()
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": f"Unknown agent: {x_agent_name}"},
        )

    tags = _parse_tags(agent.tags)
    is_specialist = "specialist" in tags

    venture_id: str | None = str(agent.venture_id) if agent.venture_id else None
    venture_slug: str | None = None
    if not is_specialist:
        candidate_slug = next((t for t in tags if t and t != "specialist"), None)
        if candidate_slug:
            v_result = await db.execute(select(Venture).where(Venture.slug == candidate_slug))
            venture = v_result.scalar_one_or_none()
            if venture:
                venture_id = str(venture.id)
                venture_slug = venture.slug

    return AgentIdentity(
        agent_id=str(agent.id),
        name=agent.name,
        venture_id=venture_id,
        venture_slug=venture_slug,
        is_specialist=is_specialist,
    )


@dataclass
class WriterContext:
    """Whichever of these two callers is writing — never both."""
    agent: AgentIdentity | None = None
    user: User | None = None


async def _get_bearer_token(authorization: str | None = Header(default=None)) -> str | None:
    scheme, _, token = (authorization or "").partition(" ")
    return token if scheme.lower() == "bearer" and token else None


class RequireWriter:
    """
    FastAPI dependency accepting either agent-service auth (X-Agent-Name +
    shared token) or human dashboard auth (User JWT + RBAC permission).
    Agent auth is checked first since it fully owns the Authorization
    header's meaning when X-Agent-Name is present; only falls through to
    JWT decoding when there's no agent-name header at all.

    Every parameter here is wrapped in Depends() deliberately — a bare
    `request: Request`-style parameter on a bound method (this class's
    __call__) can't be type-resolved by FastAPI under `from __future__
    import annotations` (bound methods don't expose __globals__, so the
    forward-ref lookup for the annotation fails at import time). Sub-
    dependencies on plain module-level functions don't have that problem,
    which is why the token itself is fetched via _get_bearer_token instead.
    """

    def __init__(self, permission: Permission) -> None:
        self.permission = permission

    async def __call__(
        self,
        db: AsyncSession = Depends(get_db),
        agent: AgentIdentity | None = Depends(get_agent_identity),
        bearer_token: str | None = Depends(_get_bearer_token),
    ) -> WriterContext:
        if agent is not None:
            return WriterContext(agent=agent)

        if not bearer_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Not authenticated"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=bearer_token)
        user = await get_current_user(credentials=creds, db=db)
        check_permission = RequirePermission(self.permission)
        user = await check_permission(current_user=user)
        return WriterContext(user=user)


def require_writer(permission: Permission) -> RequireWriter:
    return RequireWriter(permission)
