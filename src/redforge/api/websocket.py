"""
WebSocket endpoints — Phase 16: Unified API Gateway

Streaming endpoints:
  /ws/chat         — live chat streaming
  /ws/workflow     — workflow progress events
  /ws/execution    — tool execution output streaming
  /ws/events       — all session events
  /ws/reasoning    — reasoning step streaming
  /ws/report       — report generation streaming
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket Streaming"])


# ---------------------------------------------------------------------------
# Connection Manager
# ---------------------------------------------------------------------------


class ConnectionManager:
    """Manages active WebSocket connections per session."""

    def __init__(self) -> None:
        # session_id -> list of WebSocket
        self._connections: dict[str, list] = {}

    async def connect(self, websocket: WebSocket, session_id: str) -> None:
        from starlette.websockets import WebSocketState

        if websocket.client_state == WebSocketState.CONNECTING:
            await websocket.accept()
        if session_id not in self._connections:
            self._connections[session_id] = []
        if websocket not in self._connections[session_id]:
            self._connections[session_id].append(websocket)

    def disconnect(self, websocket: WebSocket, session_id: str) -> None:
        conns = self._connections.get(session_id, [])
        if websocket in conns:
            conns.remove(websocket)
        if not conns:
            self._connections.pop(session_id, None)

    async def send(self, websocket: WebSocket, event: dict[str, Any]) -> None:
        try:
            await websocket.send_text(json.dumps(event, default=str))
        except Exception as exc:  # nosec B110 - sending WS frame can fail if connection is dropped
            logger.debug("Failed to send websocket text frame: %s", exc)

    async def broadcast(self, session_id: str, event: dict[str, Any]) -> None:
        for ws in self._connections.get(session_id, [])[:]:
            await self.send(ws, event)

    @property
    def active_count(self) -> int:
        return sum(len(v) for v in self._connections.values())


manager = ConnectionManager()


# ---------------------------------------------------------------------------
# Helper: serialize events
# ---------------------------------------------------------------------------


def _event(event_type: str, session_id: str | None = None, **kwargs) -> dict:
    return {
        "event_type": event_type,
        "session_id": session_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **kwargs,
    }


# ---------------------------------------------------------------------------
# /ws/chat
# ---------------------------------------------------------------------------


@router.websocket("/ws/chat")
async def ws_chat(websocket: WebSocket):
    """
    Live chat streaming.

    Client sends JSON: {"session_id": "...", "message": "..."}
    Server streams token events, then a done event.
    """
    session_id = "default"
    await manager.connect(websocket, session_id)
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await manager.send(websocket, _event("error", message="Invalid JSON"))
                continue

            session_id = data.get("session_id", "default")
            message = data.get("message", "")

            if not message:
                await manager.send(
                    websocket, _event("error", session_id=session_id, message="Empty message")
                )
                continue

            # Send acknowledgement
            await manager.send(
                websocket, _event("chat_start", session_id=session_id, message=message)
            )

            # Stream response tokens
            try:
                from redforge.conversation.engine import ConversationEngine

                engine = ConversationEngine()
                response = engine.process(session_id=session_id, message=message)
                if isinstance(response, dict):
                    text = response.get("response", "")
                else:
                    text = str(response)
            except Exception as exc:
                text = f"[Error: {exc}]"

            # Emit tokens (word-by-word for streaming effect)
            for word in (text + " ").split(" "):
                if word:
                    await manager.send(
                        websocket,
                        _event(
                            "token",
                            session_id=session_id,
                            token=word + " ",
                        ),
                    )
                    await asyncio.sleep(0)  # yield to event loop

            # Done signal
            await manager.send(websocket, _event("done", session_id=session_id))

    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
    except Exception as exc:
        try:
            await manager.send(websocket, _event("error", session_id=session_id, message=str(exc)))
        except (
            Exception
        ) as exc_inner:  # nosec B110 - isolated error handling best-effort frame send
            logger.debug("Failed to send error frame to websocket in ws_chat: %s", exc_inner)
        manager.disconnect(websocket, session_id)


# ---------------------------------------------------------------------------
# /ws/workflow
# ---------------------------------------------------------------------------


@router.websocket("/ws/workflow")
async def ws_workflow(websocket: WebSocket):
    """
    Workflow progress streaming.

    Client sends: {"workflow_id": "...", "target": "...", "session_id": "..."}
    Server streams stage events, then completion.
    """
    session_id = "default"
    await manager.connect(websocket, session_id)
    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            session_id = data.get("session_id", "default")
            workflow_id = data.get("workflow_id", "")
            target = data.get("target", "")

            await manager.send(
                websocket,
                _event(
                    "workflow_start",
                    session_id=session_id,
                    workflow_id=workflow_id,
                    target=target,
                ),
            )

            # Simulate stage progression
            stages = ["recon", "scan", "analysis", "report"]
            for i, stage in enumerate(stages):
                await manager.send(
                    websocket,
                    _event(
                        "workflow_stage",
                        session_id=session_id,
                        workflow_id=workflow_id,
                        stage=stage,
                        progress=round((i + 1) / len(stages), 2),
                        status="running",
                    ),
                )
                await asyncio.sleep(0)

            await manager.send(
                websocket,
                _event(
                    "workflow_done",
                    session_id=session_id,
                    workflow_id=workflow_id,
                    status="completed",
                ),
            )

    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
    except Exception as exc:
        try:
            await manager.send(websocket, _event("error", message=str(exc)))
        except (
            Exception
        ) as exc_inner:  # nosec B110 - isolated error handling best-effort frame send
            logger.debug("Failed to send error frame to websocket in ws_workflow: %s", exc_inner)
        manager.disconnect(websocket, session_id)


# ---------------------------------------------------------------------------
# /ws/execution
# ---------------------------------------------------------------------------


@router.websocket("/ws/execution")
async def ws_execution(websocket: WebSocket):
    """
    Tool execution output streaming.

    Client sends: {"session_id": "...", "tool": "...", "command": [...]}
    Server streams stdout lines, then exit event.
    """
    session_id = "default"
    await manager.connect(websocket, session_id)
    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            session_id = data.get("session_id", "default")
            tool = data.get("tool", "")
            command = data.get("command", [])

            await manager.send(
                websocket,
                _event(
                    "execution_start",
                    session_id=session_id,
                    tool=tool,
                    command=command,
                ),
            )

            # Run tool
            stdout = ""
            stderr = ""
            exit_code = None
            try:
                from redforge.contracts.intent import RiskLevel
                from redforge.contracts.tool import ToolCall
                from redforge.tools.runner import ToolRunner

                tool_call = ToolCall(
                    tool_name=tool,
                    command=command,
                    target=command[-1] if command else "",
                    timeout_seconds=60,
                    risk_level=RiskLevel.LOW,
                    session_id=session_id,
                    approved=True,
                )
                runner = ToolRunner()
                result = runner.run(tool_call)
                if hasattr(result, "stdout"):
                    stdout = result.stdout or ""
                    stderr = result.stderr or ""
                    exit_code = result.exit_code
                elif isinstance(result, dict):
                    stdout = result.get("stdout", "")
                    stderr = result.get("stderr", "")
                    exit_code = result.get("exit_code")
            except Exception as exc:
                stderr = str(exc)
                exit_code = 1

            # Stream stdout line by line
            for line in stdout.splitlines():
                await manager.send(
                    websocket,
                    _event(
                        "output",
                        session_id=session_id,
                        tool=tool,
                        line=line,
                        stream="stdout",
                    ),
                )
                await asyncio.sleep(0)

            for line in stderr.splitlines():
                await manager.send(
                    websocket,
                    _event(
                        "output",
                        session_id=session_id,
                        tool=tool,
                        line=line,
                        stream="stderr",
                    ),
                )
                await asyncio.sleep(0)

            await manager.send(
                websocket,
                _event(
                    "execution_done",
                    session_id=session_id,
                    tool=tool,
                    exit_code=exit_code,
                    status="completed" if exit_code == 0 else "failed",
                ),
            )

    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
    except Exception as exc:
        try:
            await manager.send(websocket, _event("error", message=str(exc)))
        except (
            Exception
        ) as exc_inner:  # nosec B110 - isolated error handling best-effort frame send
            logger.debug("Failed to send error frame to websocket in ws_execution: %s", exc_inner)
        manager.disconnect(websocket, session_id)


# ---------------------------------------------------------------------------
# /ws/events — generic session event bus
# ---------------------------------------------------------------------------


@router.websocket("/ws/events")
async def ws_events(websocket: WebSocket):
    """
    Subscribe to all events for a session.

    Client sends: {"session_id": "...", "action": "subscribe"}
    Server keeps connection open and broadcasts events.
    """
    session_id = "default"
    await manager.connect(websocket, session_id)
    try:
        # Send welcome
        await manager.send(
            websocket, _event("connected", session_id=session_id, message="Subscribed to events")
        )
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            if data.get("action") == "ping":
                await manager.send(websocket, _event("pong", session_id=session_id))
            elif data.get("action") == "subscribe":
                session_id = data.get("session_id", session_id)
                manager.disconnect(websocket, "default")
                await manager.connect(websocket, session_id)
                await manager.send(websocket, _event("subscribed", session_id=session_id))
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
    except Exception as exc:
        try:
            await manager.send(websocket, _event("error", message=str(exc)))
        except (
            Exception
        ) as exc_inner:  # nosec B110 - isolated error handling best-effort frame send
            logger.debug("Failed to send error frame to websocket in ws_events: %s", exc_inner)
        manager.disconnect(websocket, session_id)


# ---------------------------------------------------------------------------
# /ws/reasoning
# ---------------------------------------------------------------------------


@router.websocket("/ws/reasoning")
async def ws_reasoning(websocket: WebSocket):
    """
    Reasoning step streaming.

    Client sends: {"session_id": "...", "goal": "..."}
    Server streams reasoning steps.
    """
    session_id = "default"
    await manager.connect(websocket, session_id)
    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            session_id = data.get("session_id", "default")
            goal = data.get("goal", "")

            await manager.send(
                websocket, _event("reasoning_start", session_id=session_id, goal=goal)
            )

            decision = ""
            try:
                from redforge.reasoning.engine import ReasoningEngine

                engine = ReasoningEngine()
                result = engine.reason(goal=goal, context={}, session_id=session_id)
                if isinstance(result, dict):
                    decision = result.get("decision", "")
                elif hasattr(result, "decision"):
                    decision = result.decision
            except Exception as exc:
                decision = f"[Reasoning unavailable: {exc}]"

            await manager.send(
                websocket,
                _event(
                    "reasoning_done",
                    session_id=session_id,
                    decision=decision,
                ),
            )

    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
    except Exception as exc:
        try:
            await manager.send(websocket, _event("error", message=str(exc)))
        except (
            Exception
        ) as exc_inner:  # nosec B110 - isolated error handling best-effort frame send
            logger.debug("Failed to send error frame to websocket in ws_reasoning: %s", exc_inner)
        manager.disconnect(websocket, session_id)


# ---------------------------------------------------------------------------
# /ws/report
# ---------------------------------------------------------------------------


@router.websocket("/ws/report")
async def ws_report(websocket: WebSocket):
    """
    Report generation streaming.

    Client sends: {"session_id": "...", "format": "markdown"}
    Server streams report sections.
    """
    session_id = "default"
    await manager.connect(websocket, session_id)
    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            session_id = data.get("session_id", "default")
            fmt = data.get("format", "markdown")

            await manager.send(websocket, _event("report_start", session_id=session_id, format=fmt))

            content = ""
            try:
                from redforge.reports.engine import ReportEngine

                engine = ReportEngine()
                result = engine.generate(session_id=session_id, format=fmt)
                content = (
                    result
                    if isinstance(result, str)
                    else result.get("content", "") if isinstance(result, dict) else ""
                )
            except Exception as exc:
                content = f"[Report generation failed: {exc}]"

            # Stream section by section
            sections = content.split("\n\n") if content else ["No content"]
            for section in sections:
                if section.strip():
                    await manager.send(
                        websocket,
                        _event(
                            "report_section",
                            session_id=session_id,
                            section=section,
                        ),
                    )
                    await asyncio.sleep(0)

            await manager.send(websocket, _event("report_done", session_id=session_id, format=fmt))

    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
    except Exception as exc:
        try:
            await manager.send(websocket, _event("error", message=str(exc)))
        except (
            Exception
        ) as exc_inner:  # nosec B110 - isolated error handling best-effort frame send
            logger.debug("Failed to send error frame to websocket in ws_report: %s", exc_inner)
        manager.disconnect(websocket, session_id)
