"""
Memory routes — Phase 16: Unified API Gateway
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends

logger = logging.getLogger(__name__)

from ..contracts import (
    MemoryQueryRequest,
    MemoryQueryResponse,
    MemoryStoreRequest,
)
from ..dependencies import get_current_auth, get_request_id, get_timer
from ..response import no_content, success

router = APIRouter(prefix="/memory", tags=["Memory"])


@router.post("/store", summary="Store a memory entry")
async def store_memory(
    body: MemoryStoreRequest,
    auth=Depends(get_current_auth),
    request_id: str = Depends(get_request_id),
    timer=Depends(get_timer),
):
    """Store a text entry in session memory."""
    stored = False
    try:
        from redforge.contracts.memory import MemoryEntry as ContractEntry
        from redforge.memory.manager import MemoryManager

        mgr = MemoryManager()
        entry = ContractEntry(
            content=body.content, session_id=body.session_id, metadata=body.metadata
        )
        mgr.store(session_id=body.session_id, entry=entry)
        stored = True
    except Exception:
        stored = False

    return success(
        {"stored": stored, "session_id": body.session_id},
        duration_ms=timer.elapsed_ms,
        request_id=request_id,
    )


@router.post("/query", summary="Query session memory")
async def query_memory(
    body: MemoryQueryRequest,
    auth=Depends(get_current_auth),
    request_id: str = Depends(get_request_id),
    timer=Depends(get_timer),
):
    """Retrieve top-k relevant memory entries for a query."""
    results: list = []
    try:
        from redforge.memory.manager import MemoryManager

        mgr = MemoryManager()
        entries = mgr.retrieve(session_id=body.session_id, query=body.query, top_k=body.top_k)
        for e in entries:
            if hasattr(e, "model_dump"):
                d = e.model_dump()
            elif hasattr(e, "__dict__"):
                d = vars(e)
            else:
                d = dict(e)
            results.append(d)
    except Exception as exc:  # nosec B110 - memory query is best-effort
        logger.warning("Failed to query session memory for session '%s': %s", body.session_id, exc)

    payload = MemoryQueryResponse(
        session_id=body.session_id,
        query=body.query,
        results=results,
        total=len(results),
    )
    return success(payload.model_dump(), duration_ms=timer.elapsed_ms, request_id=request_id)


@router.delete("/session/{session_id}", status_code=204, summary="Flush session memory")
async def flush_memory(session_id: str, auth=Depends(get_current_auth)):
    """Remove all short-term memory entries for a session."""
    try:
        from redforge.memory.manager import MemoryManager

        mgr = MemoryManager()
        mgr.flush_session(session_id)
    except Exception as exc:  # nosec B110 - memory flush is best-effort
        logger.warning("Failed to flush session memory for session '%s': %s", session_id, exc)
    return no_content()
