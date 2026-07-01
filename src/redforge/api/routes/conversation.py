"""
Chat & Conversation routes — Phase 16: Unified API Gateway
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Path

from ..contracts import (
    ChatRequest,
    ChatResponse,
    ConversationHistoryResponse,
    ConversationMessage,
)
from ..dependencies import AuthInfo, RequestID, Timer
from ..response import no_content, success

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Chat & Conversation"])


def _run_chat(session_id: str, message: str) -> dict:
    try:
        from redforge.conversation.engine import ConversationEngine

        engine = ConversationEngine()
        result = engine.process(session_id=session_id, message=message)
        return result if isinstance(result, dict) else {"response": str(result)}
    except Exception as exc:
        return {"response": f"[Conversation engine unavailable: {exc}]", "error": str(exc)}


@router.post("/chat", summary="Send a chat message (non-streaming)")
async def chat(
    body: ChatRequest,
    auth: AuthInfo,
    request_id: RequestID,
    timer: Timer,
):
    """Send a message to RedForge. For streaming, use /ws/chat."""
    session_id = body.session_id or "default"
    result = _run_chat(session_id, body.message)
    payload = ChatResponse(
        session_id=session_id,
        message=result.get("response", ""),
        intent=result.get("intent"),
        plan=result.get("plan"),
        findings=result.get("findings", []),
        events=result.get("events", []),
    )
    return success(payload.model_dump(), duration_ms=timer.elapsed_ms, request_id=request_id)


@router.get("/conversations/{session_id}", summary="Get conversation history")
async def get_conversation(
    auth: AuthInfo,
    request_id: RequestID,
    timer: Timer,
    session_id: str = Path(..., description="Session ID"),
    limit: int = 50,
):
    """Retrieve message history for a session."""
    messages: list[dict] = []
    try:
        from redforge.core.session import SessionService

        svc = SessionService()
        session = svc.load(session_id)
        if session and hasattr(session, "metadata"):
            history = session.metadata.get("conversation_history", [])
            messages = history[-limit:]
    except Exception as exc:  # nosec B110 - session history load is best-effort
        logger.warning("Failed to load message history for session '%s': %s", session_id, exc)

    payload = ConversationHistoryResponse(
        session_id=session_id,
        messages=[ConversationMessage(**m) if isinstance(m, dict) else m for m in messages],
        total=len(messages),
    )
    return success(payload.model_dump(), duration_ms=timer.elapsed_ms, request_id=request_id)


@router.delete("/conversations/{session_id}", status_code=204, summary="Clear conversation history")
async def clear_conversation(
    auth: AuthInfo,
    session_id: str = Path(..., description="Session ID"),
):
    """Clear all messages for a session."""
    try:
        from redforge.core.session import SessionService

        svc = SessionService()
        session = svc.load(session_id)
        if session and hasattr(session, "metadata"):
            session.metadata.pop("conversation_history", None)
            svc.save(session)
    except Exception as exc:  # nosec B110 - clearing history is best-effort
        logger.warning("Failed to clear conversation history for session '%s': %s", session_id, exc)
    return no_content()
