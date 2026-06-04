"""
CortexOS Australia — FastAPI application entry point.
Startup: initialise DB, agent registry, MCP registry, memory manager.
Shutdown: cleanup connections.
"""
from __future__ import annotations

import time
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI, Request, status
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

    logger.info("CortexOS Australia ready")
    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info("CortexOS Australia shutting down")

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

# ── Request logging middleware ────────────────────────────────────────────────

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
