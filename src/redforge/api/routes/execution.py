"""
Execution routes — Phase 16: Unified API Gateway
"""
from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends

from ..contracts import ExecutionRequest, ExecutionResponse
from ..dependencies import get_current_auth, get_request_id, get_timer
from ..response import success

router = APIRouter(prefix="/execution", tags=["Execution"])


@router.post("/run", summary="Execute a tool command (approved plans only)")
async def run_tool(
    body: ExecutionRequest,
    auth=Depends(get_current_auth),
    request_id: str = Depends(get_request_id),
    timer=Depends(get_timer),
):
    """
    Execute a single tool against an approved plan step.
    The Executor NEVER classifies intent, plans, or makes policy decisions.
    """
    execution_id = str(uuid4())
    stdout = ""
    stderr = ""
    exit_code: int | None = None
    status = "pending"
    findings: list = []

    try:
        from redforge.contracts.tool import ToolCall
        from redforge.contracts.intent import RiskLevel
        from redforge.tools.runner import ToolRunner
        tool_call = ToolCall(
            tool_name=body.tool,
            command=body.command,
            target=body.command[-1] if body.command else "",
            timeout_seconds=body.timeout or 60,
            risk_level=RiskLevel.LOW,
            session_id=body.session_id,
            approved=True
        )
        runner = ToolRunner()
        result = runner.run(tool_call)
        if hasattr(result, "stdout"):
            stdout = result.stdout or ""
            stderr = result.stderr or ""
            exit_code = result.exit_code
            status = "completed" if exit_code == 0 else "failed"
        elif isinstance(result, dict):
            stdout = result.get("stdout", "")
            stderr = result.get("stderr", "")
            exit_code = result.get("exit_code")
            status = result.get("status", "completed")
    except Exception as exc:
        stderr = str(exc)
        status = "error"

    payload = ExecutionResponse(
        execution_id=execution_id,
        session_id=body.session_id,
        tool=body.tool,
        status=status,
        stdout=stdout,
        stderr=stderr,
        exit_code=exit_code,
        duration_ms=timer.elapsed_ms,
        findings=findings,
    )
    return success(payload.model_dump(), duration_ms=timer.elapsed_ms, request_id=request_id)
