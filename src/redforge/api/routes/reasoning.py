"""
Reasoning routes — Phase 16: Unified API Gateway
"""
from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends

from ..contracts import ReasoningRequest, ReasoningResponse
from ..dependencies import get_current_auth, get_request_id, get_timer
from ..response import success

router = APIRouter(prefix="/reasoning", tags=["Reasoning"])


@router.post("/decide", summary="Invoke the autonomous reasoning engine")
async def decide(
    body: ReasoningRequest,
    auth=Depends(get_current_auth),
    request_id: str = Depends(get_request_id),
    timer=Depends(get_timer),
):
    """Run one reasoning step for a given goal and context."""
    reasoning_id = str(uuid4())
    decision = ""
    strategy = ""
    confidence = 0.0
    next_actions: list = []

    try:
        from redforge.reasoning.engine import ReasoningEngine
        engine = ReasoningEngine()
        result = engine.reason(
            goal=body.goal,
            context=body.context,
            session_id=body.session_id,
        )
        if isinstance(result, dict):
            decision = result.get("decision", "")
            strategy = result.get("strategy", "")
            confidence = float(result.get("confidence", 0.0))
            next_actions = result.get("next_actions", [])
        elif hasattr(result, "decision"):
            decision = result.decision
            strategy = getattr(result, "strategy", "")
            confidence = float(getattr(result, "confidence", 0.0))
            next_actions = getattr(result, "next_actions", [])
    except Exception as exc:
        decision = f"[Reasoning engine unavailable: {exc}]"

    payload = ReasoningResponse(
        session_id=body.session_id,
        reasoning_id=reasoning_id,
        decision=decision,
        strategy=strategy,
        confidence=confidence,
        next_actions=next_actions,
        created_at=datetime.utcnow(),
    )
    return success(payload.model_dump(), duration_ms=timer.elapsed_ms, request_id=request_id)
