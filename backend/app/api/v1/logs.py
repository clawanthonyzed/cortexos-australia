"""System logs endpoint backed by audit_logs."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import Permission, require_permission
from app.dependencies import get_db
from app.models.audit_log import AuditLog
from app.models.user import User

router = APIRouter()


@router.get("", response_model=dict[str, Any], tags=["logs"])
async def list_logs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.AGENT_READ)),
    limit: int = Query(default=200, ge=1, le=1000),
    level: str | None = Query(default=None),
    service: str | None = Query(default=None),
    search: str | None = Query(default=None),
) -> dict[str, Any]:
    """Return recent audit log entries as system log entries."""
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)

    if service and service != "all":
        stmt = stmt.where(AuditLog.resource_type == service)

    count_stmt = select(func.count()).select_from(
        select(AuditLog).subquery()
    )
    total = (await db.execute(count_stmt)).scalar_one()

    result = await db.execute(stmt)
    rows = result.scalars().all()

    logs = []
    for row in rows:
        if not row.success:
            log_level = "error"
        elif row.action in ("DELETE", "CANCEL", "STOP"):
            log_level = "warn"
        else:
            log_level = "info"

        if level and level != "all" and log_level != level:
            continue

        message = f"{row.action} {row.resource_type}"
        if row.resource_id:
            message += f" [{row.resource_id[:8]}]"
        if row.error_message:
            message += f": {row.error_message}"

        if search and search.lower() not in message.lower():
            continue

        logs.append({
            "id": str(row.id),
            "level": log_level,
            "service": row.resource_type or "system",
            "message": message,
            "metadata": {
                "path": row.path,
                "method": row.method,
                "status_code": row.status_code,
                "ip": row.ip_address,
            },
            "timestamp": row.created_at.isoformat(),
        })

    return {"logs": logs, "total": total}
