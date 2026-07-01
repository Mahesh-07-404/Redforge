"""
API Contracts — Phase 16: Unified API Gateway
Pydantic schemas for all request/response bodies.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SessionModeEnum(str, Enum):
    bugbounty = "bugbounty"
    ctf = "ctf"
    pentest = "pentest"
    learning = "learning"
    coding = "coding"
    android = "android"


class AutonomyEnum(str, Enum):
    manual = "manual"
    semi = "semi"
    full = "full"


class ReportFormatEnum(str, Enum):
    markdown = "markdown"
    json = "json"
    html = "html"
    pdf = "pdf"


class WorkflowStatusEnum(str, Enum):
    pending = "pending"
    running = "running"
    paused = "paused"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


# ---------------------------------------------------------------------------
# Standard API Envelope
# ---------------------------------------------------------------------------

class APIResponse(BaseModel):
    """Standard envelope returned by every non-streaming endpoint."""
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str = "success"
    version: str = "2.0.0"
    duration_ms: float = 0.0
    payload: Optional[Any] = None
    errors: List[str] = []

    @classmethod
    def ok(cls, payload: Any, duration_ms: float = 0.0) -> "APIResponse":
        return cls(status="success", payload=payload, duration_ms=duration_ms)

    @classmethod
    def error(cls, errors: List[str], status: str = "error") -> "APIResponse":
        return cls(status=status, errors=errors)


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    trace_id: str = Field(default_factory=lambda: str(uuid4()))


# ---------------------------------------------------------------------------
# Auth schemas
# ---------------------------------------------------------------------------

class TokenRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600


class APIKeyRequest(BaseModel):
    name: str
    scopes: List[str] = ["read", "write"]
    expires_days: Optional[int] = None


class APIKeyResponse(BaseModel):
    key_id: str
    api_key: str
    name: str
    scopes: List[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Session schemas
# ---------------------------------------------------------------------------

class SessionCreateRequest(BaseModel):
    mode: SessionModeEnum
    target: Optional[str] = None
    autonomy: AutonomyEnum = AutonomyEnum.manual
    name: str = ""
    metadata: Dict[str, Any] = {}


class SessionResponse(BaseModel):
    id: str
    mode: str
    target: Optional[str]
    autonomy: str
    status: str
    name: str = ""
    created_at: datetime
    updated_at: datetime
    memory_namespace: Optional[str] = None
    metadata: Dict[str, Any] = {}


class SessionUpdateRequest(BaseModel):
    target: Optional[str] = None
    autonomy: Optional[str] = None
    name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Chat / Conversation schemas
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    stream: bool = True
    metadata: Dict[str, Any] = {}


class ChatResponse(BaseModel):
    session_id: str
    message: str
    intent: Optional[Dict[str, Any]] = None
    plan: Optional[Dict[str, Any]] = None
    findings: List[Dict[str, Any]] = []
    events: List[Dict[str, Any]] = []


class ConversationMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = {}


class ConversationHistoryResponse(BaseModel):
    session_id: str
    messages: List[ConversationMessage] = []
    total: int = 0


# ---------------------------------------------------------------------------
# Workflow schemas
# ---------------------------------------------------------------------------

class WorkflowStartRequest(BaseModel):
    workflow_id: str
    target: Optional[str] = None
    parameters: Dict[str, Any] = {}
    session_id: Optional[str] = None


class WorkflowResponse(BaseModel):
    workflow_id: str
    run_id: str
    status: WorkflowStatusEnum
    session_id: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    stages_completed: int = 0
    stages_total: int = 0
    error: Optional[str] = None


class WorkflowListResponse(BaseModel):
    workflows: List[Dict[str, Any]] = []
    total: int = 0


# ---------------------------------------------------------------------------
# Planner schemas
# ---------------------------------------------------------------------------

class PlanRequest(BaseModel):
    session_id: str
    intent: Dict[str, Any]
    context: Dict[str, Any] = {}


class PlanResponse(BaseModel):
    session_id: str
    plan_id: str
    summary: str
    phases: List[Dict[str, Any]] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Reasoning schemas
# ---------------------------------------------------------------------------

class ReasoningRequest(BaseModel):
    session_id: str
    goal: str
    context: Dict[str, Any] = {}


class ReasoningResponse(BaseModel):
    session_id: str
    reasoning_id: str
    decision: str
    strategy: str
    confidence: float
    next_actions: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Execution schemas
# ---------------------------------------------------------------------------

class ExecutionRequest(BaseModel):
    session_id: str
    plan_id: Optional[str] = None
    tool: str
    command: List[str]
    timeout: int = 60


class ExecutionResponse(BaseModel):
    execution_id: str
    session_id: str
    tool: str
    status: str
    stdout: str = ""
    stderr: str = ""
    exit_code: Optional[int] = None
    duration_ms: float = 0.0
    findings: List[Dict[str, Any]] = []


# ---------------------------------------------------------------------------
# Report schemas
# ---------------------------------------------------------------------------

class ReportRequest(BaseModel):
    session_id: str
    format: ReportFormatEnum = ReportFormatEnum.markdown
    include_evidence: bool = True
    include_remediation: bool = True


class ReportResponse(BaseModel):
    report_id: str
    session_id: str
    format: str
    title: str
    content: str
    finding_count: int = 0
    severity_summary: Dict[str, int] = {}
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Memory schemas
# ---------------------------------------------------------------------------

class MemoryStoreRequest(BaseModel):
    session_id: str
    content: str
    tier: str = "short"
    metadata: Dict[str, Any] = {}


class MemoryQueryRequest(BaseModel):
    session_id: str
    query: str
    top_k: int = 5


class MemoryEntry(BaseModel):
    id: str
    content: str
    tier: str
    relevance: float = 1.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = {}


class MemoryQueryResponse(BaseModel):
    session_id: str
    query: str
    results: List[MemoryEntry] = []
    total: int = 0


# ---------------------------------------------------------------------------
# Plugin schemas
# ---------------------------------------------------------------------------

class PluginInstallRequest(BaseModel):
    plugin_id: str
    version: Optional[str] = None
    source: Optional[str] = None


class PluginResponse(BaseModel):
    plugin_id: str
    name: str
    version: str
    plugin_type: str
    enabled: bool
    installed_at: datetime = Field(default_factory=datetime.utcnow)
    description: str = ""
    author: str = ""


class PluginListResponse(BaseModel):
    plugins: List[PluginResponse] = []
    total: int = 0


# ---------------------------------------------------------------------------
# MCP schemas
# ---------------------------------------------------------------------------

class MCPToolResponse(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any] = {}
    version: str = "1.0.0"


class MCPResourceResponse(BaseModel):
    uri: str
    name: str
    description: str
    mime_type: str = "text/plain"


class MCPDiscoveryResponse(BaseModel):
    tools: List[MCPToolResponse] = []
    resources: List[MCPResourceResponse] = []
    server_version: str = "2.0.0"


# ---------------------------------------------------------------------------
# System / Health schemas
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    uptime_seconds: float = 0.0


class ReadinessResponse(BaseModel):
    ready: bool
    checks: Dict[str, bool] = {}
    message: str = ""


class LivenessResponse(BaseModel):
    alive: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class VersionResponse(BaseModel):
    version: str
    phase: str
    build: str = ""
    python_version: str = ""


class MetricsResponse(BaseModel):
    uptime_seconds: float
    total_requests: int
    active_sessions: int
    total_sessions: int
    total_findings: int
    total_executions: int
    error_rate: float
    avg_response_ms: float
    memory_usage_mb: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# WebSocket event schemas
# ---------------------------------------------------------------------------

class WSEvent(BaseModel):
    event_type: str
    session_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload: Dict[str, Any] = {}


class WSChatEvent(WSEvent):
    event_type: str = "chat"
    token: str = ""
    done: bool = False


class WSWorkflowEvent(WSEvent):
    event_type: str = "workflow"
    stage: str = ""
    progress: float = 0.0


class WSExecutionEvent(WSEvent):
    event_type: str = "execution"
    tool: str = ""
    status: str = ""
    output: str = ""


class WSReasoningEvent(WSEvent):
    event_type: str = "reasoning"
    step: str = ""
    decision: str = ""


class WSReportEvent(WSEvent):
    event_type: str = "report"
    section: str = ""
    content: str = ""


class WSSystemEvent(WSEvent):
    event_type: str = "system"
    level: str = "info"
    message: str = ""
