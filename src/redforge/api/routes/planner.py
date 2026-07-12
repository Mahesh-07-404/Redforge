"""
Planner routes — Phase 16: Unified API Gateway
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter

from ..contracts import PlanRequest, PlanResponse
from ..dependencies import AuthInfo, RequestID, Timer
from ..response import success

router = APIRouter(prefix="/planner", tags=["Planner"])


@router.post("/plan", summary="Generate an execution plan")
async def create_plan(
    body: PlanRequest,
    auth: AuthInfo,
    request_id: RequestID,
    timer: Timer,
):
    """Generate a structured execution plan from an intent."""
    plan_id = str(uuid4())
    phases: list = []
    summary = ""

    try:
        from redforge.planner.engine import PlannerEngine

        engine = PlannerEngine()
        plan = engine.create_plan(
            session_id=body.session_id, intent=body.intent, context=body.context
        )
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
