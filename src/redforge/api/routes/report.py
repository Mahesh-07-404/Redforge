"""
Report routes — Phase 16: Unified API Gateway
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Path
from fastapi.responses import PlainTextResponse

from ..contracts import ReportRequest, ReportResponse
from ..dependencies import AuthInfo, RequestID, Timer
from ..response import success

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/generate", summary="Generate a security report")
async def generate_report(
    body: ReportRequest,
    auth: AuthInfo,
    request_id: RequestID,
    timer: Timer,
):
    """Generate a formatted security report from session evidence and findings."""
    report_id = str(uuid4())
    content = ""
    finding_count = 0
    severity_summary: dict = {}
    title = f"RedForge Security Report — Session {body.session_id}"

    try:
        from redforge.reports.engine import ReportEngine

        engine = ReportEngine()
        report = engine.generate(
            session_id=body.session_id,
            format=body.format.value,
        )
        if isinstance(report, dict):
            content = report.get("content", "")
            finding_count = report.get("finding_count", 0)
            severity_summary = report.get("severity_summary", {})
            title = report.get("title", title)
        elif isinstance(report, str):
            content = report
        elif hasattr(report, "content"):
            content = report.content
            finding_count = getattr(report, "finding_count", 0)
    except Exception as exc:
        content = f"[Report engine unavailable: {exc}]"

    payload = ReportResponse(
        report_id=report_id,
        session_id=body.session_id,
        format=body.format.value,
        title=title,
        content=content,
        finding_count=finding_count,
        severity_summary=severity_summary,
        generated_at=datetime.now(timezone.utc),
    )
    return success(payload.model_dump(), duration_ms=timer.elapsed_ms, request_id=request_id)


@router.get("/{session_id}/markdown", summary="Get Markdown report")
async def get_markdown_report(
    auth: AuthInfo,
    session_id: str = Path(...),
):
    """Return the raw Markdown report as plain text."""
    content = f"# RedForge Security Report\n\nSession: {session_id}\n\n*No findings recorded.*"
    try:
        from redforge.reports.engine import ReportEngine

        engine = ReportEngine()
        result = engine.generate(session_id=session_id, format="markdown")
        if isinstance(result, str):
            content = result
        elif isinstance(result, dict):
            content = result.get("content", content)
    except Exception as exc:  # nosec B110 - raw report load is best-effort
        logger.warning("Failed to generate raw report for session '%s': %s", session_id, exc)
    return PlainTextResponse(content=content, media_type="text/markdown")
