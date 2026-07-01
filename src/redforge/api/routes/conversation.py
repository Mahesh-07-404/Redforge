"""
Chat & Conversation routes — Phase 16: Unified API Gateway
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Path

from ..contracts import ChatRequest, ChatResponse, ConversationMessage, ConversationHistoryResponse
from ..dependencies import get_current_auth, get_request_id, get_timer
from ..response import success, no_content

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
    auth=Depends(get_current_auth),
    request_id: str = Depends(get_request_id),
    timer=Depends(get_timer),
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
    session_id: str = Path(..., description="Session ID"),
    auth=Depends(get_current_auth),
    request_id: str = Depends(get_request_id),
    timer=Depends(get_timer),
    limit: int = 50,
):
    """Retrieve message history for a session."""
    messages: List[dict] = []
    try:
        from redforge.core.session import SessionService
        svc = SessionService()
        session = svc.load(session_id)
        if session and hasattr(session, "metadata"):
            history = session.metadata.get("conversation_history", [])
            messages = history[-limit:]
    except Exception:
        pass

    payload = ConversationHistoryResponse(
        session_id=session_id,
        messages=[ConversationMessage(**m) if isinstance(m, dict) else m for m in messages],
        total=len(messages),
    )
    return success(payload.model_dump(), duration_ms=timer.elapsed_ms, request_id=request_id)


@router.delete("/conversations/{session_id}", status_code=204, summary="Clear conversation history")
async def clear_conversation(
    session_id: str = Path(..., description="Session ID"),
    auth=Depends(get_current_auth),
):
    """Clear all messages for a session."""
    try:
        from redforge.core.session import SessionService
        svc = SessionService()
        session = svc.load(session_id)
        if session and hasattr(session, "metadata"):
            session.metadata.pop("conversation_history", None)
            svc.save(session)
    except Exception:
        pass
    return no_content()
