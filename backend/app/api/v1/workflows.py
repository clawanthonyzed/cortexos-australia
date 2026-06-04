"""Workflow CRUD + execute endpoints."""
from __future__ import annotations

import json
import uuid
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.rbac import Permission, require_permission
from app.dependencies import get_db, paginate
from app.models.user import User
from app.models.workflow import Workflow, WorkflowStatus, WorkflowStep
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowExecuteRequest,
    WorkflowExecuteResult,
    WorkflowRead,
    WorkflowReadBrief,
    WorkflowUpdate,
)

logger = structlog.get_logger(__name__)
router = APIRouter()


def _error(msg: str, detail: Any = None) -> dict[str, Any]:
    return {"error": msg, "detail": detail or {}}


@router.get("", response_model=dict[str, Any], tags=["workflows"])
async def list_workflows(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.WORKFLOW_READ)),
    pagination: dict = Depends(paginate),
    status_filter: str | None = Query(None, alias="status"),
) -> dict[str, Any]:
    """List all workflows with pagination."""
    stmt = select(Workflow)
    if status_filter:
        stmt = stmt.where(Workflow.status == status_filter)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.offset(pagination["offset"]).limit(pagination["limit"]).order_by(Workflow.created_at.desc())
    result = await db.execute(stmt)
    workflows = result.scalars().all()

    return {
        "items": [WorkflowReadBrief.model_validate(w) for w in workflows],
        "total": total,
        "page": pagination["page"],
        "page_size": pagination["page_size"],
    }


@router.post("", response_model=WorkflowRead, status_code=status.HTTP_201_CREATED, tags=["workflows"])
async def create_workflow(
    payload: WorkflowCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.WORKFLOW_CREATE)),
) -> WorkflowRead:
    """Create a new workflow with optional steps."""
    workflow = Workflow(
        name=payload.name,
        description=payload.description,
        graph_json=json.dumps(payload.graph_json),
        trigger_type=payload.trigger_type,
        cron_expression=payload.cron_expression,
        config_json=json.dumps(payload.config_json),
    )
    db.add(workflow)
    await db.flush()

    for i, step_data in enumerate(payload.steps):
        step = WorkflowStep(
            workflow_id=workflow.id,
            name=step_data.name,
            description=step_data.description,
            step_type=step_data.step_type,
            config_json=json.dumps(step_data.config_json),
            order=step_data.order if step_data.order else i,
            next_steps_json=json.dumps(step_data.next_steps),
            node_id=step_data.node_id,
        )
        db.add(step)

    await db.flush()

    result = await db.execute(
        select(Workflow)
        .where(Workflow.id == workflow.id)
        .options(selectinload(Workflow.steps))
    )
    workflow = result.scalar_one()
    return WorkflowRead.model_validate(workflow)


@router.get("/templates", tags=["workflows"])
async def list_templates(
    current_user: User = Depends(require_permission(Permission.WORKFLOW_READ)),
) -> dict[str, Any]:
    """List available workflow templates."""
    return {
        "templates": [
            {
                "id": "product_launch",
                "name": "Product Launch Pipeline",
                "description": "Research → Create → SEO → Human Approval → Marketing",
                "nodes": 6,
            },
            {
                "id": "content_pipeline",
                "name": "Content Creation Pipeline",
                "description": "Brief → Research → Keywords → Write",
                "nodes": 4,
            },
        ]
    }


@router.get("/templates/{template_id}", tags=["workflows"])
async def get_template(
    template_id: str,
    current_user: User = Depends(require_permission(Permission.WORKFLOW_READ)),
) -> dict[str, Any]:
    """Get a workflow template graph_json."""
    from app.workflows.templates import get_content_pipeline_template, get_product_launch_template

    match template_id:
        case "product_launch":
            return {"template_id": template_id, "graph": get_product_launch_template()}
        case "content_pipeline":
            return {"template_id": template_id, "graph": get_content_pipeline_template()}
        case _:
            raise HTTPException(status_code=404, detail=_error("Template not found"))


@router.get("/{workflow_id}", response_model=WorkflowRead, tags=["workflows"])
async def get_workflow(
    workflow_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.WORKFLOW_READ)),
) -> WorkflowRead:
    """Get a workflow with its steps."""
    result = await db.execute(
        select(Workflow)
        .where(Workflow.id == workflow_id)
        .options(selectinload(Workflow.steps))
    )
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail=_error("Workflow not found"))
    return WorkflowRead.model_validate(workflow)


@router.patch("/{workflow_id}", response_model=WorkflowRead, tags=["workflows"])
async def update_workflow(
    workflow_id: uuid.UUID,
    payload: WorkflowUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.WORKFLOW_UPDATE)),
) -> WorkflowRead:
    """Update workflow definition."""
    result = await db.execute(
        select(Workflow)
        .where(Workflow.id == workflow_id)
        .options(selectinload(Workflow.steps))
    )
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail=_error("Workflow not found"))

    if workflow.status == WorkflowStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_error("Cannot update a running workflow"),
        )

    update_data = payload.model_dump(exclude_none=True)
    for field, value in update_data.items():
        if field in ("graph_json", "config_json"):
            setattr(workflow, field, json.dumps(value))
        else:
            setattr(workflow, field, value)

    await db.flush()
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id).options(selectinload(Workflow.steps))
    )
    workflow = result.scalar_one()
    return WorkflowRead.model_validate(workflow)


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None, tags=["workflows"])
async def delete_workflow(
    workflow_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.WORKFLOW_DELETE)),
) -> None:
    """Delete a workflow."""
    workflow = await db.get(Workflow, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail=_error("Workflow not found"))
    await db.delete(workflow)


@router.post("/{workflow_id}/execute", response_model=WorkflowExecuteResult, tags=["workflows"])
async def execute_workflow(
    workflow_id: uuid.UUID,
    payload: WorkflowExecuteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.WORKFLOW_RUN)),
) -> WorkflowExecuteResult:
    """Execute a workflow (sync or async via Celery)."""
    workflow = await db.get(Workflow, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail=_error("Workflow not found"))

    if workflow.status == WorkflowStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_error("Workflow is already running"),
        )

    import uuid as _uuid
    run_id = str(_uuid.uuid4())

    if payload.async_run:
        from app.tasks.agent_tasks import run_workflow_task
        celery_result = run_workflow_task.delay(str(workflow_id), payload.input_data)
        return WorkflowExecuteResult(
            workflow_id=workflow_id,
            run_id=run_id,
            status="queued",
            celery_task_id=celery_result.id,
            message="Workflow queued for execution",
        )

    from app.workflows.engine import WorkflowEngine
    engine = WorkflowEngine(db)
    final_state = await engine.execute(workflow_id, payload.input_data)

    success = not final_state.get("error") and not final_state.get("requires_approval")
    return WorkflowExecuteResult(
        workflow_id=workflow_id,
        run_id=final_state.get("run_id", run_id),
        status="completed" if success else ("paused" if final_state.get("requires_approval") else "failed"),
        message=final_state.get("error") or "Workflow completed",
    )
