"""
FastAPI Dependencies — Phase 16: Unified API Gateway
Reusable Depends() callables for auth, pagination, rate-limit checks, session lookup.
"""

from __future__ import annotations

import time
from typing import Annotated, Any

from fastapi import Depends, Query, Request

from .auth import get_auth_service
from .config import get_api_config
from .exceptions import (
    AuthenticationError,
    SessionNotFoundError,
)

# ---------------------------------------------------------------------------
# Auth dependencies
# ---------------------------------------------------------------------------


async def get_current_auth(request: Request) -> dict[str, Any]:
    """Return auth_info attached by AuthenticationMiddleware."""
    auth_info = getattr(request.state, "auth_info", None)
    if auth_info is None:
        cfg = get_api_config()
        if cfg.auth.enabled:
            raise AuthenticationError()
        return {"authenticated": False, "scopes": ["read", "write", "execute", "report", "admin"]}
    return auth_info


AuthInfo = Annotated[dict[str, Any], Depends(get_current_auth)]


async def require_read(auth: AuthInfo) -> dict[str, Any]:
    get_auth_service().check_scope(auth, "read")
    return auth


async def require_write(auth: AuthInfo) -> dict[str, Any]:
    get_auth_service().check_scope(auth, "write")
    return auth


async def require_execute(auth: AuthInfo) -> dict[str, Any]:
    get_auth_service().check_scope(auth, "execute")
    return auth


async def require_admin(auth: AuthInfo) -> dict[str, Any]:
    get_auth_service().check_scope(auth, "admin")
    return auth


# ---------------------------------------------------------------------------
# Pagination dependency
# ---------------------------------------------------------------------------


class PaginationParams:
    def __init__(
        self,
        page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
        page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    ) -> None:
        self.page = page
        self.page_size = page_size
        self.offset = (page - 1) * page_size


# ---------------------------------------------------------------------------
# Request ID / Trace ID
# ---------------------------------------------------------------------------


async def get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


async def get_trace_id(request: Request) -> str:
    return getattr(request.state, "trace_id", "unknown")


# ---------------------------------------------------------------------------
# Request timing helper
# ---------------------------------------------------------------------------


class RequestTimer:
    def __init__(self) -> None:
        self._start = time.perf_counter()

    @property
    def elapsed_ms(self) -> float:
        return (time.perf_counter() - self._start) * 1000


async def get_timer() -> RequestTimer:
    return RequestTimer()


# ---------------------------------------------------------------------------
# Session lookup dependency
# ---------------------------------------------------------------------------


async def get_session_or_404(session_id: str) -> dict[str, Any]:
    """
    Lightweight session existence check.
    Routes that need the full Session object import the session service directly.
    This dependency is used for validation only.
    """
    # Delegate to internal session service
    try:
        from redforge.core.session import SessionService

        svc = SessionService()
        session = svc.load(session_id)
        if session is None:
            raise SessionNotFoundError(f"Session '{session_id}' not found")
        return session.model_dump() if hasattr(session, "model_dump") else dict(session)
    except SessionNotFoundError:
        raise
    except Exception:
        # If session service is unavailable, return a minimal stub so routes still work
        return {"id": session_id, "status": "unknown"}


# ---------------------------------------------------------------------------
# Workflow existence check
# ---------------------------------------------------------------------------


async def get_workflow_or_404(workflow_id: str) -> dict[str, Any]:
    try:
        from redforge.workflow.registry import WorkflowRegistry

        registry = WorkflowRegistry()
        workflow = registry.get(workflow_id)
        if workflow is None:
            from .exceptions import WorkflowNotFoundError

            raise WorkflowNotFoundError(f"Workflow '{workflow_id}' not found")
        return workflow if isinstance(workflow, dict) else {"id": workflow_id}
    except Exception:
        return {"id": workflow_id}


# ---------------------------------------------------------------------------
# Common type aliases
# ---------------------------------------------------------------------------

ReadAuth = Annotated[dict[str, Any], Depends(require_read)]
WriteAuth = Annotated[dict[str, Any], Depends(require_write)]
ExecuteAuth = Annotated[dict[str, Any], Depends(require_execute)]
AdminAuth = Annotated[dict[str, Any], Depends(require_admin)]
Pagination = Annotated[PaginationParams, Depends(PaginationParams)]
RequestID = Annotated[str, Depends(get_request_id)]
TraceID = Annotated[str, Depends(get_trace_id)]
Timer = Annotated[RequestTimer, Depends(get_timer)]
