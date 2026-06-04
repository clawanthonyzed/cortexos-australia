"""Main API router — aggregates all v1 sub-routers."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    agents,
    auth,
    finance,
    health,
    integrations,
    knowledge_graph,
    memory,
    models,
    products,
    tasks,
    workflows,
)

api_router = APIRouter()

# Health / system (no auth prefix)
api_router.include_router(health.router, prefix="", tags=["health"])

# Auth
api_router.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])

# Core resources
api_router.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
api_router.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])
api_router.include_router(workflows.router, prefix="/api/v1/workflows", tags=["workflows"])

# Memory & knowledge
api_router.include_router(memory.router, prefix="/api/v1/memory", tags=["memory"])
api_router.include_router(knowledge_graph.router, prefix="/api/v1/knowledge-graph", tags=["knowledge_graph"])

# Products & commerce
api_router.include_router(products.router, prefix="/api/v1/products", tags=["products"])
api_router.include_router(integrations.router, prefix="/api/v1/integrations", tags=["integrations"])

# Finance & models
api_router.include_router(finance.router, prefix="/api/v1/finance", tags=["finance"])
api_router.include_router(models.router, prefix="/api/v1/models", tags=["models"])
