"""
CortexOS Australia — FastAPI application entry point.
Startup: initialise DB, agent registry, MCP registry, memory manager.
Shutdown: cleanup connections.
"""
from __future__ import annotations

import asyncio
import time
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI, Query, Request, WebSocket, WebSocketDisconnect, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings

# Structured logging setup
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(
        getattr(__import__("logging"), settings.log_level, 20)
    ),
)
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.
    Startup: init DB tables, agents, MCPs.
    Shutdown: close DB connections, knowledge graph.
    """
    logger.info(
        "CortexOS Australia starting",
        environment=settings.environment,
        version=settings.app_version,
    )

    # 1. Initialise database
    try:
        from app.database import init_db
        await init_db()
        logger.info("Database initialised")
    except Exception as exc:
        logger.error("Database init failed — continuing with degraded mode", error=str(exc))

    # 2. Seed default roles if first run
    try:
        await _seed_roles()
        logger.info("Default roles seeded")
    except Exception as exc:
        logger.warning("Role seeding failed", error=str(exc))

    # 3. Initialise agent registry (imports all default agents)
    try:
        from app.agents.registry import AgentRegistry
        AgentRegistry()  # triggers _import_defaults
        logger.info("Agent registry initialised", types=AgentRegistry.list_types())
    except Exception as exc:
        logger.error("Agent registry init failed", error=str(exc))

    # 4. Initialise MCP registry
    try:
        from app.mcp.registry import init_mcp_registry
        init_mcp_registry()
        logger.info("MCP registry initialised")
    except Exception as exc:
        logger.error("MCP registry init failed", error=str(exc))

    # 5. Warm up memory clients
    try:
        from app.memory.manager import get_graphiti, get_mem0
        get_mem0()   # triggers lazy init
        get_graphiti()
        logger.info("Memory clients warmed up")
    except Exception as exc:
        logger.warning("Memory client warmup failed", error=str(exc))

    # 6. Start revenue sync scheduler
    try:
        from app.integrations.revenue_sync import start_revenue_sync_scheduler
        start_revenue_sync_scheduler()
        logger.info("Revenue sync scheduler started")
    except Exception as exc:
        logger.warning("Revenue sync scheduler failed to start", error=str(exc))

    logger.info("CortexOS Australia ready")
    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info("CortexOS Australia shutting down")

    try:
        from app.integrations.revenue_sync import stop_revenue_sync_scheduler
        stop_revenue_sync_scheduler()
    except Exception:
        pass

    try:
        from app.memory.manager import get_graphiti
        await get_graphiti().close()
    except Exception:
        pass

    try:
        from app.database import close_db
        await close_db()
    except Exception:
        pass

    logger.info("Shutdown complete")


async def _seed_roles() -> None:
    """Create admin/operator/viewer roles if they don't exist."""
    import json
    from sqlalchemy import select
    from app.auth.rbac import ROLE_PERMISSIONS
    from app.database import AsyncSessionLocal
    from app.models.user import Role

    async with AsyncSessionLocal() as db:
        for role_name, permissions in ROLE_PERMISSIONS.items():
            result = await db.execute(select(Role).where(Role.name == role_name))
            if not result.scalar_one_or_none():
                role = Role(
                    name=role_name,
                    description=f"Default {role_name} role",
                    permissions=json.dumps(permissions),
                )
                db.add(role)
        await db.commit()


# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "CortexOS Australia — Production Agentic Operating System for AI Holding Companies. "
        "Multi-agent orchestration, LLM routing, knowledge graph memory, "
        "digital commerce integrations, and financial observability."
    ),
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request logging + audit middleware ───────────────────────────────────────

_SKIP_AUDIT_PATHS = {"/ready", "/health", "/metrics", "/ws"}


async def _write_audit_log(
    method: str,
    path: str,
    status_code: int,
    elapsed_ms: float,
    ip_address: str,
    user_agent: str,
    user_id: str | None,
) -> None:
    """Fire-and-forget: write an AuditLog row to the database."""
    try:
        from app.database import AsyncSessionLocal
        from app.models.audit_log import AuditLog

        action = f"{method} {path}"
        resource_type = path.split("/")[3] if path.count("/") >= 3 else "unknown"

        async with AsyncSessionLocal() as db:
            log = AuditLog(
                user_id=uuid.UUID(user_id) if user_id else None,
                action=action[:100],
                resource_type=resource_type[:100],
                method=method,
                path=path[:500],
                ip_address=ip_address[:45],
                user_agent=user_agent[:500],
                status_code=status_code,
                success=status_code < 400,
            )
            db.add(log)
            await db.commit()
    except Exception as exc:
        logger.warning("Audit log write failed", error=str(exc))


def _extract_user_id(request: Request) -> str | None:
    """Pull user_id from JWT in Authorization header without verifying (middleware-safe)."""
    try:
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return None
        import base64
        import json as _json
        token = auth[7:]
        parts = token.split(".")
        if len(parts) != 3:
            return None
        payload_b64 = parts[1] + "=="  # add padding
        payload = _json.loads(base64.urlsafe_b64decode(payload_b64))
        return str(payload.get("sub")) if payload.get("sub") else None
    except Exception:
        return None


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next: Any) -> Any:
    request_id = str(uuid.uuid4())[:8]
    t0 = time.perf_counter()

    logger.info(
        "Request",
        id=request_id,
        method=request.method,
        path=request.url.path,
        client=request.client.host if request.client else "unknown",
    )

    response = await call_next(request)
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    logger.info(
        "Response",
        id=request_id,
        status=response.status_code,
        ms=elapsed,
    )
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{elapsed}ms"

    # Async audit log (fire-and-forget — never blocks the response)
    if request.url.path not in _SKIP_AUDIT_PATHS and not request.url.path.startswith("/ws"):
        user_id = _extract_user_id(request)
        asyncio.create_task(
            _write_audit_log(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                elapsed_ms=elapsed,
                ip_address=request.client.host if request.client else "unknown",
                user_agent=request.headers.get("User-Agent", "")[:500],
                user_id=user_id,
            )
        )

    return response


# ── Exception handlers ────────────────────────────────────────────────────────

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Any) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": "Resource not found", "detail": {"path": request.url.path}},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "detail": {"errors": exc.errors()},
        },
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "Internal server error",
        path=request.url.path,
        error=str(exc),
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": {"message": "An unexpected error occurred"},
        },
    )


# ── Register routes ───────────────────────────────────────────────────────────

from app.api.router import api_router  # noqa: E402
app.include_router(api_router)


# ── WebSocket endpoint ────────────────────────────────────────────────────────

from app.api.v1.ws_manager import manager as ws_manager  # noqa: E402


@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(default=""),
) -> None:
    """
    Authenticated WebSocket endpoint.
    Clients connect with ?token=<jwt>.
    Messages: agent.status_changed, agent.metrics_updated, system.health, alert, ping/pong.
    """
    import json

    # Validate token
    user_id: str | None = None
    try:
        if token:
            from app.auth.jwt import decode_token
            payload = decode_token(token)
            user_id = str(payload.get("sub", ""))
    except Exception:
        await websocket.close(code=4001)
        return

    client_id = str(uuid.uuid4())
    await ws_manager.connect(client_id, websocket)

    # Send initial connection ack
    await ws_manager.send(client_id, {
        "type": "connected",
        "clientId": client_id,
        "userId": user_id,
    })

    try:
        while True:
            try:
                raw = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                msg = json.loads(raw)
                if msg.get("type") == "ping":
                    await ws_manager.send(client_id, {"type": "pong", "ts": time.time()})
            except asyncio.TimeoutError:
                # Send keepalive ping
                await ws_manager.send(client_id, {"type": "ping", "ts": time.time()})
            except WebSocketDisconnect:
                break
            except Exception as exc:
                logger.warning("WS receive error", client_id=client_id, error=str(exc))
                break
    finally:
        await ws_manager.disconnect(client_id)
