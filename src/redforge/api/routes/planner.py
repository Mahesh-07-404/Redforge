"""
Planner routes — Phase 16: Unified API Gateway
"""
from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends

from ..contracts import PlanRequest, PlanResponse
from ..dependencies import get_current_auth, get_request_id, get_timer
from ..response import success

router = APIRouter(prefix="/planner", tags=["Planner"])


@router.post("/plan", summary="Generate an execution plan")
async def create_plan(
    body: PlanRequest,
    auth=Depends(get_current_auth),
    request_id: str = Depends(get_request_id),
    timer=Depends(get_timer),
):
    """Generate a structured execution plan from an intent."""
    plan_id = str(uuid4())
    phases: list = []
    summary = ""

    try:
        from redforge.planner.engine import PlannerEngine
        engine = PlannerEngine()
        plan = engine.create_plan(session_id=body.session_id, intent=body.intent, context=body.context)
        if hasattr(plan, "phases"):
            phases = [p if isinstance(p, dict) else vars(p) for p in plan.phases]
        if hasattr(plan, "summary"):
            summary = plan.summary
        if hasattr(plan, "id"):
            plan_id = str(plan.id)
    except Exception as exc:
        summary = f"[Planner unavailable: {exc}]"

    payload = PlanResponse(
        session_id=body.session_id,
        plan_id=plan_id,
        summary=summary,
        phases=phases,
        created_at=datetime.utcnow(),
    )
    return success(payload.model_dump(), duration_ms=timer.elapsed_ms, request_id=request_id)
