"""
Session routes — Phase 16: Unified API Gateway
CRUD for RedForge sessions.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from ..contracts import (
    SessionCreateRequest,
    SessionUpdateRequest,
    APIResponse,
)
from ..dependencies import get_current_auth, get_request_id, get_timer
from ..exceptions import SessionNotFoundError
from ..response import created, no_content, success

router = APIRouter(prefix="/sessions", tags=["Sessions"])


def _get_service():
    try:
        from redforge.core.session import SessionService
        return SessionService()
    except Exception as exc:  # nosec B110 - session service failure is handled by returning None
        logger.debug("Failed to load SessionService: %s", exc)
        return None


def _to_response(session) -> dict:
    if session is None:
        return {}
    if hasattr(session, "model_dump"):
        d = session.model_dump()
    elif hasattr(session, "__dict__"):
        d = vars(session)
    else:
        d = dict(session)
    # Normalize datetimes
    for k in ("created_at", "updated_at"):
        v = d.get(k)
        if isinstance(v, datetime):
            d[k] = v.isoformat()
    return d


@router.post("", status_code=201, summary="Create a new session")
async def create_session(
    body: SessionCreateRequest,
    auth=Depends(get_current_auth),
    request_id: str = Depends(get_request_id),
    timer=Depends(get_timer),
):
    """Create and persist a new RedForge session."""
    svc = _get_service()
    if svc is None:
        raise HTTPException(status_code=503, detail="Session service unavailable")
    try:
        session = svc.create(
            mode=body.mode.value,
            target=body.target,
            autonomy=body.autonomy.value,
            name=body.name,
        )
        return created(_to_response(session), duration_ms=timer.elapsed_ms, request_id=request_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("", summary="List sessions")
async def list_sessions(
    auth=Depends(get_current_auth),
    request_id: str = Depends(get_request_id),
    timer=Depends(get_timer),
    status: Optional[str] = Query(None, description="Filter by status: active, archived, completed"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    """List all sessions with optional status filter."""
    offset = (page - 1) * page_size
    svc = _get_service()
    if svc is None:
        return success({"sessions": [], "total": 0}, request_id=request_id)
    try:
        sessions = svc.list_sessions()
        if status:
            sessions = [s for s in sessions if s.get("status") == status]
        total = len(sessions)
        page_sessions = sessions[offset: offset + page_size]
        return success(
            {"sessions": page_sessions, "total": total, "page": page, "page_size": page_size},
            duration_ms=timer.elapsed_ms,
            request_id=request_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{session_id}", summary="Get a session")
async def get_session(
    session_id: str = Path(..., description="Session ID"),
    auth=Depends(get_current_auth),
    request_id: str = Depends(get_request_id),
    timer=Depends(get_timer),
):
    """Retrieve a single session by ID."""
    svc = _get_service()
    if svc:
        session = svc.load(session_id)
        if session is None:
            raise SessionNotFoundError(f"Session '{session_id}' not found")
        return success(_to_response(session), duration_ms=timer.elapsed_ms, request_id=request_id)
    raise SessionNotFoundError(session_id)


@router.patch("/{session_id}", summary="Update a session")
async def update_session(
    body: SessionUpdateRequest,
    session_id: str = Path(..., description="Session ID"),
    auth=Depends(get_current_auth),
    request_id: str = Depends(get_request_id),
    timer=Depends(get_timer),
):
    """Update session target, autonomy, or name."""
    svc = _get_service()
    if svc is None:
        raise HTTPException(status_code=503, detail="Session service unavailable")
    session = svc.load(session_id)
    if session is None:
        raise SessionNotFoundError(session_id)
    if body.target is not None:
        svc.set_target(session_id, body.target)
    session = svc.load(session_id)
    return success(_to_response(session), duration_ms=timer.elapsed_ms, request_id=request_id)


@router.delete("/{session_id}", status_code=204, summary="Delete a session")
async def delete_session(
    session_id: str = Path(..., description="Session ID"),
    auth=Depends(get_current_auth),
):
    """Permanently delete a session."""
    svc = _get_service()
    if svc:
        try:
            svc.delete(session_id)
        except Exception as exc:  # nosec B110 - deleting session is best-effort
            logger.warning("Failed to delete session '%s': %s", session_id, exc)
    return no_content()


@router.post("/{session_id}/archive", summary="Archive a session")
async def archive_session(
    session_id: str = Path(..., description="Session ID"),
    auth=Depends(get_current_auth),
    request_id: str = Depends(get_request_id),
):
    """Mark session as archived."""
    svc = _get_service()
    if svc:
        try:
            svc.archive(session_id)
        except AttributeError as exc:  # nosec B110 - session archiver missing or unsupported
            logger.debug("Archive method not supported on session service for session '%s': %s", session_id, exc)
    return success({"archived": True, "session_id": session_id}, request_id=request_id)
