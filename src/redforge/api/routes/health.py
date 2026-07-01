"""
Health routes — Phase 16: Unified API Gateway
/health  /ready  /live  /version  /metrics
"""
from __future__ import annotations

import platform
import time
from datetime import datetime

import psutil
from fastapi import APIRouter, Depends

from ..contracts import (
    HealthResponse,
    LivenessResponse,
    MetricsResponse,
    ReadinessResponse,
    VersionResponse,
)
from ..response import success

router = APIRouter(tags=["Health & Observability"])

# Application start time for uptime calculation
_START_TIME = time.monotonic()
_START_DT = datetime.utcnow()

# Simple in-memory counters (production: use Prometheus / OpenTelemetry)
_metrics: dict = {
    "total_requests": 0,
    "active_sessions": 0,
    "total_sessions": 0,
    "total_findings": 0,
    "total_executions": 0,
    "total_errors": 0,
    "total_duration_ms": 0.0,
}


def increment(key: str, value: float = 1.0) -> None:
    _metrics[key] = _metrics.get(key, 0) + value


@router.get("/health", response_model=None, summary="Health check")
async def health() -> dict:
    """Basic health check. Always returns 200 while the process is alive."""
    payload = HealthResponse(
        status="healthy",
        version="2.0.0",
        timestamp=datetime.utcnow(),
        uptime_seconds=time.monotonic() - _START_TIME,
    )
    return success(payload.model_dump()).body.decode()  # type: ignore[attr-defined]


@router.get("/health", include_in_schema=False)
@router.get("/api/v1/health", summary="Health check (versioned)")
async def health_v1():
    uptime = time.monotonic() - _START_TIME
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": round(uptime, 2),
    }


@router.get("/ready", summary="Readiness probe")
async def readiness():
    """Kubernetes readiness probe — checks sub-system availability."""
    checks = {}

    # Check session DB
    try:
        from redforge.core.session import SessionService
        svc = SessionService()
        svc.list_sessions()
        checks["session_db"] = True
    except Exception:
        checks["session_db"] = False

    # Check memory (basic)
    checks["memory"] = True

    ready = all(checks.values())
    payload = ReadinessResponse(
        ready=ready,
        checks=checks,
        message="All systems operational" if ready else "Some subsystems unavailable",
    )
    status_code = 200 if ready else 503
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=status_code, content=payload.model_dump())


@router.get("/live", summary="Liveness probe")
async def liveness():
    """Kubernetes liveness probe — always 200 while event loop is alive."""
    return LivenessResponse(alive=True, timestamp=datetime.utcnow()).model_dump()


@router.get("/version", summary="Version information")
async def version():
    """Returns API version, phase, and runtime information."""
    payload = VersionResponse(
        version="2.0.0",
        phase="Phase 16 — Unified API Gateway",
        build="v2.0.0-phase-16",
        python_version=platform.python_version(),
    )
    return payload.model_dump()


@router.get("/metrics", summary="Application metrics")
async def metrics():
    """Exposes internal counters for monitoring dashboards."""
    uptime = time.monotonic() - _START_TIME
    total_req = _metrics.get("total_requests", 0)
    total_err = _metrics.get("total_errors", 0)
    total_dur = _metrics.get("total_duration_ms", 0.0)

    try:
        process = psutil.Process()
        mem_mb = process.memory_info().rss / 1_048_576
    except Exception:
        mem_mb = 0.0

    payload = MetricsResponse(
        uptime_seconds=round(uptime, 2),
        total_requests=total_req,
        active_sessions=_metrics.get("active_sessions", 0),
        total_sessions=_metrics.get("total_sessions", 0),
        total_findings=_metrics.get("total_findings", 0),
        total_executions=_metrics.get("total_executions", 0),
        error_rate=round(total_err / max(total_req, 1), 4),
        avg_response_ms=round(total_dur / max(total_req, 1), 2),
        memory_usage_mb=round(mem_mb, 2),
        timestamp=datetime.utcnow(),
    )
    return payload.model_dump()
