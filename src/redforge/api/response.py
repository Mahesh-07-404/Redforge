"""
Standard Response builder — Phase 16: Unified API Gateway
Every route returns the same APIResponse envelope.
"""

from __future__ import annotations

from typing import Any

from fastapi.responses import JSONResponse

from .contracts import APIResponse


def success(
    payload: Any,
    duration_ms: float = 0.0,
    status_code: int = 200,
    request_id: str = "",
    version: str = "2.0.0",
) -> JSONResponse:
    """Return a 2xx APIResponse envelope."""
    resp = APIResponse.ok(payload=payload, duration_ms=duration_ms)
    if request_id:
        resp.request_id = request_id
    resp.version = version
    return JSONResponse(status_code=status_code, content=_jsonable(resp))


def created(
    payload: Any,
    duration_ms: float = 0.0,
    request_id: str = "",
) -> JSONResponse:
    return success(payload, duration_ms=duration_ms, status_code=201, request_id=request_id)


def no_content() -> JSONResponse:
    return JSONResponse(status_code=204, content=None)


def error_response(
    errors: list[str],
    status_code: int = 400,
    request_id: str = "",
) -> JSONResponse:
    resp = APIResponse.error(errors=errors)
    if request_id:
        resp.request_id = request_id
    return JSONResponse(status_code=status_code, content=_jsonable(resp))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _jsonable(obj: Any) -> Any:
    """Convert Pydantic model to JSON-serializable dict."""
    if hasattr(obj, "model_dump"):
        raw = obj.model_dump()
        return _serialize(raw)
    return obj


def _serialize(obj: Any) -> Any:
    import uuid
    from datetime import datetime

    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize(i) for i in obj]
    return obj
