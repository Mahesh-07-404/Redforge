"""
RedForge Web Dashboard
FastAPI backend with WebSocket support for real-time monitoring and agent interaction
"""
import os
import uuid
import json
import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from redforge.core.config import get_settings
from redforge.core.agent import RedForgeAgent
from redforge.core.state import AgentState, AutonomyLevel, AgentMode, create_initial_state
from redforge.utils.platform import check_tool_available, detect_platform, get_tool_version

logger = logging.getLogger(__name__)

# FastAPI App
app = FastAPI(
    title="RedForge API",
    description="RedForge CLI Agent API",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class Message(BaseModel):
    role: MessageRole
    content: str
    timestamp: Optional[str] = None


class Session(BaseModel):
    id: str
    mode: str = "bugbounty"
    messages: List[Message] = []
    created_at: str = ""
    metadata: Dict[str, Any] = {}


class Finding(BaseModel):
    id: str
    title: str
    severity: str
    category: str
    target: str
    status: str = "open"
    description: Optional[str] = ""
    timestamp: Optional[str] = None


# Session and State Stores
session_states: Dict[str, AgentState] = {}
session_agents: Dict[str, RedForgeAgent] = {}
findings_db: Dict[str, Finding] = {}
running_sessions: set[str] = set()

# Global skill loader for efficiency
from redforge.core.skill_loader import SkillLoader
skill_loader = SkillLoader()
skill_loader.load_skills()


class ConnectionManager:
    """Manage WebSocket connections and subscriptions"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.sessions: Dict[str, Session] = {}
        self.subscriptions: Dict[str, List[WebSocket]] = {}  # event_type -> connections
    
    async def connect(self, websocket: WebSocket):
        """Accept and store connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # Remove from subscriptions
        for subs in self.subscriptions.values():
            if websocket in subs:
                subs.remove(websocket)
        
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")
    
    async def send(self, message: Dict, websocket: WebSocket):
        """Send message to specific connection"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict, event_type: Optional[str] = None):
        """Broadcast message to all connections or subscribers"""
        targets = self.active_connections
        
        if event_type and event_type in self.subscriptions:
            targets = self.subscriptions[event_type]
        
        disconnected = []
        for connection in targets:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Broadcast failed: {e}")
                disconnected.append(connection)
        
        # Clean up
        for conn in disconnected:
            self.disconnect(conn)
    
    def subscribe(self, websocket: WebSocket, event_types: List[str]):
        """Subscribe to event types"""
        for event_type in event_types:
            if event_type not in self.subscriptions:
                self.subscriptions[event_type] = []
            if websocket not in self.subscriptions[event_type]:
                self.subscriptions[event_type].append(websocket)
    
    # Session management
    def create_session(self, mode: str = "bugbounty", target: Optional[str] = None, autonomy: str = "manual") -> Session:
        """Create new session"""
        session_id = str(uuid.uuid4())
        session = Session(
            id=session_id,
            mode=mode,
            created_at=datetime.now().isoformat(),
            metadata={
                "target": target or "",
                "autonomy": autonomy,
                "workspace": "default"
            }
        )
        self.sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        return self.sessions.get(session_id)
    
    def add_message(self, session_id: str, message: Message):
        """Add message to session"""
        session = self.sessions.get(session_id)
        if session:
            message.timestamp = datetime.now().isoformat()
            session.messages.append(message)


# Global connection manager
manager = ConnectionManager()


# ---------------------------------------------------------------------------
# WebSocket event handler builders
# ---------------------------------------------------------------------------

def make_token_handler(session_id: str):
    async def token_handler(payload: Dict[str, Any]):
        content = payload.get("content", "")
        await manager.broadcast({
            "type": "token",
            "session_id": session_id,
            "content": content
        }, "chat")
    return token_handler


def make_tool_start_handler(session_id: str):
    async def tool_start_handler(payload: Dict[str, Any]):
        tool = payload.get("tool", "")
        command = payload.get("command", "")
        call_id = payload.get("call_id", "")
        await manager.broadcast({
            "type": "tool_start",
            "session_id": session_id,
            "call_id": call_id,
            "tool": tool,
            "command": command
        }, "chat")
    return tool_start_handler


def make_tool_end_handler(session_id: str):
    async def tool_end_handler(payload: Dict[str, Any]):
        tool = payload.get("tool", "")
        command = payload.get("command", "")
        call_id = payload.get("call_id", "")
        result = payload.get("result", {})
        success = payload.get("success", False)
        error = payload.get("error", None)
        
        await manager.broadcast({
            "type": "tool_end",
            "session_id": session_id,
            "call_id": call_id,
            "tool": tool,
            "command": command,
            "result": result,
            "success": success,
            "error": error
        }, "chat")
    return tool_end_handler


def make_finding_handler(session_id: str):
    async def finding_handler(payload: Dict[str, Any]):
        finding = payload.get("finding", {})
        finding_id = finding.get("id")
        if finding_id:
            target = ""
            session = manager.get_session(session_id)
            if session:
                target = session.metadata.get("target", "")
            
            f_model = Finding(
                id=finding_id,
                title=finding.get("title", ""),
                severity=finding.get("severity", "info"),
                category=finding.get("type", "general"),
                target=target,
                status="open",
                description=finding.get("description", ""),
                timestamp=datetime.now().isoformat()
            )
            findings_db[finding_id] = f_model
            
            await manager.broadcast({
                "type": "finding_created",
                "finding": f_model.model_dump(),
                "timestamp": datetime.now().isoformat()
            }, "findings")
    return finding_handler


def make_error_handler(session_id: str):
    async def error_handler(payload: Dict[str, Any]):
        message = payload.get("message", "Unknown error")
        await manager.broadcast({
            "type": "error",
            "session_id": session_id,
            "message": message
        }, "chat")
    return error_handler


def get_or_create_agent(session_id: str) -> RedForgeAgent:
    """Get or create agent for session with full initialization and handlers"""
    if session_id in session_agents:
        return session_agents[session_id]
        
    settings = get_settings()
    agent = RedForgeAgent(
        config=settings,
        llm_provider=settings.llm.provider,
        model=settings.llm.model,
        api_key=settings.llm.api_key,
        base_url=settings.llm.base_url,
    )
    
    # Register handlers
    agent.on("token", make_token_handler(session_id))
    agent.on("tool_start", make_tool_start_handler(session_id))
    agent.on("tool_end", make_tool_end_handler(session_id))
    agent.on("finding", make_finding_handler(session_id))
    agent.on("error", make_error_handler(session_id))
    
    session_agents[session_id] = agent
    return agent


async def run_agent_session(session_id: str, user_input: str):
    """Run agent thread in background and broadcast updates"""
    session = manager.get_session(session_id)
    if not session:
        return
    
    # Prevent concurrent runs for the same session
    if session_id in running_sessions:
        logger.warning(f"Session {session_id} is already running an agent task. Skipping concurrent run.")
        await manager.broadcast({
            "type": "error",
            "session_id": session_id,
            "message": "Agent is already busy. Please wait for the current task to finish."
        }, "chat")
        return

    running_sessions.add(session_id)
    
    try:
        # Initialize agent for session
        agent = get_or_create_agent(session_id)
        prior_state = session_states.get(session_id)
        
        autonomy_level = AutonomyLevel(session.metadata.get("autonomy", "manual"))
        agent_mode = AgentMode.GOAL_BASED
        if session.mode in ("learning", "coding"):
            agent_mode = AgentMode.KNOWLEDGE_BASED
            
        workspace_name = session.metadata.get("workspace", "default")
        
        # Run the agent graph asynchronously
        state = await agent.run(
            user_input=user_input,
            workspace_id=session_id,
            workspace_name=workspace_name,
            autonomy_level=autonomy_level,
            mode=agent_mode,
            prior_state=prior_state
        )
        
        # Save state
        session_states[session_id] = state
        
        # Extract and format assistant messages that were added in this run
        prior_len = len(prior_state.messages) if prior_state else 1
        new_messages = state.messages[prior_len:]
        
        assistant_content = ""
        for msg in new_messages:
            if msg.get("role") == "assistant":
                assistant_content += msg.get("content", "") + "\n\n"
        
        if assistant_content.strip():
            manager.add_message(session_id, Message(
                role=MessageRole.ASSISTANT,
                content=assistant_content.strip()
            ))
            
            await manager.broadcast({
                "type": "agent_message",
                "session_id": session_id,
                "content": assistant_content.strip(),
                "timestamp": datetime.now().isoformat()
            }, "chat")
            
        # Check if confirmation is required
        if state.pending_confirmation:
            await manager.broadcast({
                "type": "confirmation_required",
                "session_id": session_id,
                "message": state.pending_confirmation.get("message", ""),
                "tool_calls": state.pending_confirmation.get("tool_calls", [])
            }, "chat")
        else:
            await manager.broadcast({
                "type": "run_end",
                "session_id": session_id
            }, "chat")
            
    except Exception as e:
        logger.error(f"Error running agent session {session_id}: {e}", exc_info=True)
        await manager.broadcast({
            "type": "error",
            "session_id": session_id,
            "message": str(e)
        }, "chat")
    finally:
        if session_id in running_sessions:
            running_sessions.remove(session_id)


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket connection for real-time communication"""
    await manager.connect(websocket)
    
    try:
        # Send welcome message
        await manager.send({
            "type": "connected",
            "session_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat()
        }, websocket)
        
        while True:
            data = await websocket.receive_json()
            await handle_websocket_message(websocket, data)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


async def handle_websocket_message(websocket: WebSocket, data: Dict):
    """Handle incoming WebSocket message"""
    msg_type = data.get("type")
    
    if msg_type == "subscribe":
        events = data.get("events", [])
        manager.subscribe(websocket, events)
        await manager.send({"type": "subscribed", "events": events}, websocket)
    
    elif msg_type == "session_create":
        # Create session with details
        mode = data.get("mode", "bugbounty")
        target = data.get("target", "")
        autonomy = data.get("autonomy", "manual")
        
        session = manager.create_session(mode=mode, target=target, autonomy=autonomy)
        
        await manager.send({
            "type": "session_created",
            "session": session.model_dump()
        }, websocket)
    
    elif msg_type == "message":
        session_id = data.get("session_id")
        content = data.get("content", "")
        
        if session_id:
            session = manager.get_session(session_id)
            if session:
                manager.add_message(session_id, Message(
                    role=MessageRole.USER,
                    content=content
                ))
            
                # Broadcast user message
                await manager.broadcast({
                    "type": "user_message",
                    "session_id": session_id,
                    "content": content,
                    "timestamp": datetime.now().isoformat()
                }, "chat")
                
                # Run the agent in the background
                asyncio.create_task(run_agent_session(session_id, content))
    
    elif msg_type == "approve":
        session_id = data.get("session_id")
        if session_id:
            # Send approval user message
            content = "[APPROVED] Execute the planned action."
            manager.add_message(session_id, Message(
                role=MessageRole.USER,
                content=content
            ))
            await manager.broadcast({
                "type": "user_message",
                "session_id": session_id,
                "content": content,
                "timestamp": datetime.now().isoformat()
            }, "chat")
            
            asyncio.create_task(run_agent_session(session_id, content))
            
    elif msg_type == "reject":
        session_id = data.get("session_id")
        if session_id:
            # Send rejection user message
            content = "Cancel tool execution. Do not run this command."
            manager.add_message(session_id, Message(
                role=MessageRole.USER,
                content=content
            ))
            await manager.broadcast({
                "type": "user_message",
                "session_id": session_id,
                "content": content,
                "timestamp": datetime.now().isoformat()
            }, "chat")
            
            asyncio.create_task(run_agent_session(session_id, content))
            
    elif msg_type == "command":
        command = data.get("command")
        session_id = data.get("session_id")
        
        # Prevent concurrent runs for the same session
        if session_id in running_sessions:
            logger.warning(f"Session {session_id} is busy. Skipping direct command.")
            await manager.broadcast({
                "type": "error",
                "session_id": session_id,
                "message": "Agent is busy. Please wait for the current task to finish before sending direct commands."
            }, "chat")
            return

        await manager.broadcast({
            "type": "command_executing",
            "session_id": session_id,
            "command": command,
            "timestamp": datetime.now().isoformat()
        }, "command")
        
        # Run command directly using ToolExecutor bash command
        if session_id:
            if not command:
                logger.warning("Received empty command payload, skipping execution")
                return
            
            running_sessions.add(session_id)
            agent = get_or_create_agent(session_id)
            try:
                result = await agent.tool_executor.bash(command)
                await manager.broadcast({
                    "type": "command_result",
                    "session_id": session_id,
                    "command": command,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "success": result.success,
                    "returncode": result.returncode,
                    "duration_s": result.duration_s
                }, "command")
            except Exception as e:
                await manager.broadcast({
                    "type": "command_result",
                    "session_id": session_id,
                    "command": command,
                    "stdout": "",
                    "stderr": str(e),
                    "success": False,
                    "returncode": -1,
                    "duration_s": 0.0
                }, "command")
            finally:
                if session_id in running_sessions:
                    running_sessions.remove(session_id)
    
    elif msg_type == "ping":
        await manager.send({"type": "pong"}, websocket)


# ---------------------------------------------------------------------------
# REST API Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "connections": len(manager.active_connections),
        "sessions": len(manager.sessions)
    }


@app.get("/stats")
async def get_stats():
    """Get dashboard statistics"""
    settings = get_settings()
    
    # Use global skill loader stats
    skill_stats = skill_loader.stats()
    
    return {
        "active_connections": len(manager.active_connections),
        "total_sessions": len(manager.sessions),
        "total_findings": len(findings_db),
        "findings_by_severity": {
            "critical": sum(1 for f in findings_db.values() if f.severity == "critical"),
            "high": sum(1 for f in findings_db.values() if f.severity == "high"),
            "medium": sum(1 for f in findings_db.values() if f.severity == "medium"),
            "low": sum(1 for f in findings_db.values() if f.severity == "low"),
            "info": sum(1 for f in findings_db.values() if f.severity == "info")
        },
        "system": {
            "llm_provider": settings.llm.provider,
            "llm_model": settings.llm.model,
            "autonomy_level": settings.autonomy.default_level,
            "total_skills": skill_stats.get("total", 0),
            "skills_by_category": skill_stats.get("by_category", {})
        }
    }


@app.get("/tools")
async def list_tools():
    """List tool availability status"""
    tools_to_check = ["python3", "git", "curl", "nmap", "ffuf", "sqlmap", "whatweb", "dig", "whois"]
    results = {}
    for tool in tools_to_check:
        available, path = check_tool_available(tool)
        version = get_tool_version(tool) if available else None
        results[tool] = {
            "available": available,
            "path": path or "Not found",
            "version": version or "Unknown"
        }
    return results


@app.post("/sessions")
async def create_session(mode: str = "bugbounty", target: Optional[str] = None, autonomy: str = "manual"):
    """Create new session"""
    session = manager.create_session(mode, target, autonomy)
    return session


@app.get("/sessions")
async def list_sessions():
    """List all sessions"""
    return {"sessions": list(manager.sessions.values())}


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session details"""
    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.get("/sessions/{session_id}/messages")
async def get_messages(session_id: str):
    """Get session messages"""
    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"messages": session.messages}


@app.get("/findings")
async def list_findings(
    target: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None
):
    """List findings"""
    results = list(findings_db.values())
    
    if target:
        results = [f for f in results if target in f.target]
    if severity:
        results = [f for f in results if f.severity == severity]
    if status:
        results = [f for f in results if f.status == status]
    
    return {"findings": results}


@app.post("/findings")
async def create_finding(finding: Finding):
    """Create finding"""
    findings_db[finding.id] = finding
    
    # Broadcast to subscribers
    await manager.broadcast({
        "type": "finding_created",
        "finding": finding.model_dump(),
        "timestamp": datetime.now().isoformat()
    }, "findings")
    
    return finding


@app.get("/findings/{finding_id}")
async def get_finding(finding_id: str):
    """Get finding by ID"""
    if finding_id not in findings_db:
        raise HTTPException(status_code=404, detail="Finding not found")
    return findings_db[finding_id]


@app.patch("/findings/{finding_id}")
async def update_finding(finding_id: str, update: Dict[str, Any]):
    """Update finding"""
    if finding_id not in findings_db:
        raise HTTPException(status_code=404, detail="Finding not found")
    
    finding = findings_db[finding_id]
    for key, value in update.items():
        if hasattr(finding, key):
            setattr(finding, key, value)
    
    # Broadcast update
    await manager.broadcast({
        "type": "finding_updated",
        "finding_id": finding_id,
        "update": update,
        "timestamp": datetime.now().isoformat()
    }, "findings")
    
    return finding


# Setup static directories and template serving
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(BASE_DIR, "static", "css"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "static", "js"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "templates"), exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

@app.get("/")
async def root():
    """Serve the Web Dashboard HTML page"""
    return FileResponse(os.path.join(BASE_DIR, "templates", "index.html"))


# Run with: uvicorn redforge.web.app:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
