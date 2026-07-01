"""
Workflow routes — Phase 16: Unified API Gateway
"""

from __future__ import annotations

import logging
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Path

from ..contracts import (
    WorkflowListResponse,
    WorkflowResponse,
    WorkflowStartRequest,
    WorkflowStatusEnum,
)
from ..dependencies import AuthInfo, ReadAuth, RequestID, Timer
from ..response import created, success

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflows", tags=["Workflows"])


def _get_workflow_engine():
    try:
        from redforge.workflow.engine import WorkflowEngine

        return WorkflowEngine()
    except (
        Exception
    ) as exc:  # nosec B110 - workflow engine loading failure is handled by returning None
        logger.debug("Failed to load WorkflowEngine: %s", exc)
        return None


@router.get("", summary="List available workflows")
async def list_workflows(auth: ReadAuth, request_id: RequestID, timer: Timer):
    """List all registered workflow definitions."""
    workflows: list = []
    try:
        from redforge.workflow.registry import WorkflowRegistry

        registry = WorkflowRegistry()
        workflows = registry.list() if hasattr(registry, "list") else []
    except Exception as exc:  # nosec B110 - listing workflows is best-effort
        logger.warning("Failed to list workflows: %s", exc)
    payload = WorkflowListResponse(workflows=workflows, total=len(workflows))
    return success(payload.model_dump(), duration_ms=timer.elapsed_ms, request_id=request_id)


@router.post("/run", status_code=201, summary="Start a workflow")
async def start_workflow(
    body: WorkflowStartRequest,
    auth: AuthInfo,
    request_id: RequestID,
    timer: Timer,
):
    """Start a named workflow for a given target."""
    run_id = str(uuid4())
    engine = _get_workflow_engine()
    status = WorkflowStatusEnum.pending
    error: str | None = None

    if engine:
        try:
            engine.execute(
                workflow_id=body.workflow_id,
                target=body.target,
                session_id=body.session_id,
                parameters=body.parameters,
            )
            status = WorkflowStatusEnum.running
        except Exception as exc:
            status = WorkflowStatusEnum.failed
            error = str(exc)

    payload = WorkflowResponse(
        workflow_id=body.workflow_id,
        run_id=run_id,
        status=status,
        session_id=body.session_id,
        started_at=datetime.utcnow(),
        error=error,
    )
    return created(payload.model_dump(), duration_ms=timer.elapsed_ms, request_id=request_id)


@router.get("/{workflow_id}", summary="Get workflow details")
async def get_workflow(
    auth: AuthInfo,
    request_id: RequestID,
    timer: Timer,
    workflow_id: str = Path(...),
):
    """Get the definition of a specific workflow."""
    info: dict = {"id": workflow_id}
    try:
        from redforge.workflow.registry import WorkflowRegistry

        registry = WorkflowRegistry()
        w = registry.get(workflow_id) if hasattr(registry, "get") else None
        if w:
            info = w if isinstance(w, dict) else {"id": workflow_id, "workflow": str(w)}
    except Exception as exc:  # nosec B110 - workflow retrieval is best-effort
        logger.warning("Failed to retrieve details for workflow '%s': %s", workflow_id, exc)
    return success(info, duration_ms=timer.elapsed_ms, request_id=request_id)
