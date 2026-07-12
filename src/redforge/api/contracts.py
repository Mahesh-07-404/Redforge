"""
API Contracts — Phase 16: Unified API Gateway
Pydantic schemas for all request/response bodies.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
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
    payload: Any | None = None
    errors: list[str] = []

    @classmethod
    def ok(cls, payload: Any, duration_ms: float = 0.0) -> APIResponse:
        return cls(status="success", payload=payload, duration_ms=duration_ms)

    @classmethod
    def error(cls, errors: list[str], status: str = "error") -> APIResponse:
        return cls(status=status, errors=errors)


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: dict[str, Any] | None = None
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
    scopes: list[str] = ["read", "write"]
    expires_days: int | None = None


class APIKeyResponse(BaseModel):
    key_id: str
    api_key: str
    name: str
    scopes: list[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None


# ---------------------------------------------------------------------------
# Session schemas
# ---------------------------------------------------------------------------


class SessionCreateRequest(BaseModel):
    mode: SessionModeEnum
    target: str | None = None
    autonomy: AutonomyEnum = AutonomyEnum.manual
    name: str = ""
    metadata: dict[str, Any] = {}


class SessionResponse(BaseModel):
    id: str
    mode: str
    target: str | None
    autonomy: str
    status: str
    name: str = ""
    created_at: datetime
    updated_at: datetime
    memory_namespace: str | None = None
    metadata: dict[str, Any] = {}


class SessionUpdateRequest(BaseModel):
    target: str | None = None
    autonomy: str | None = None
    name: str | None = None
    metadata: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Chat / Conversation schemas
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    stream: bool = True
    metadata: dict[str, Any] = {}


class ChatResponse(BaseModel):
    session_id: str
    message: str
    intent: dict[str, Any] | None = None
    plan: dict[str, Any] | None = None
    findings: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []


class ConversationMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = {}


class ConversationHistoryResponse(BaseModel):
    session_id: str
    messages: list[ConversationMessage] = []
    total: int = 0


# ---------------------------------------------------------------------------
# Workflow schemas
# ---------------------------------------------------------------------------


class WorkflowStartRequest(BaseModel):
    workflow_id: str
    target: str | None = None
    parameters: dict[str, Any] = {}
    session_id: str | None = None


class WorkflowResponse(BaseModel):
    workflow_id: str
    run_id: str
    status: WorkflowStatusEnum
    session_id: str | None = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    stages_completed: int = 0
    stages_total: int = 0
    error: str | None = None


class WorkflowListResponse(BaseModel):
    workflows: list[dict[str, Any]] = []
    total: int = 0


# ---------------------------------------------------------------------------
# Planner schemas
# ---------------------------------------------------------------------------


class PlanRequest(BaseModel):
    session_id: str
    intent: dict[str, Any]
    context: dict[str, Any] = {}


class PlanResponse(BaseModel):
    session_id: str
    plan_id: str
    summary: str
    phases: list[dict[str, Any]] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Reasoning schemas
# ---------------------------------------------------------------------------


class ReasoningRequest(BaseModel):
    session_id: str
    goal: str
    context: dict[str, Any] = {}


class ReasoningResponse(BaseModel):
    session_id: str
    reasoning_id: str
    decision: str
    strategy: str
    confidence: float
    next_actions: list[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Execution schemas
# ---------------------------------------------------------------------------


class ExecutionRequest(BaseModel):
    session_id: str
    plan_id: str | None = None
    tool: str
    command: list[str]
    timeout: int = 60


class ExecutionResponse(BaseModel):
    execution_id: str
    session_id: str
    tool: str
    status: str
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    duration_ms: float = 0.0
    findings: list[dict[str, Any]] = []


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
    severity_summary: dict[str, int] = {}
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Memory schemas
# ---------------------------------------------------------------------------


class MemoryStoreRequest(BaseModel):
    session_id: str
    content: str
    tier: str = "short"
    metadata: dict[str, Any] = {}


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
    metadata: dict[str, Any] = {}


class MemoryQueryResponse(BaseModel):
    session_id: str
    query: str
    results: list[MemoryEntry] = []
    total: int = 0


# ---------------------------------------------------------------------------
# Plugin schemas
# ---------------------------------------------------------------------------


class PluginInstallRequest(BaseModel):
    plugin_id: str
    version: str | None = None
    source: str | None = None


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
    plugins: list[PluginResponse] = []
    total: int = 0


# ---------------------------------------------------------------------------
# MCP schemas
# ---------------------------------------------------------------------------


class MCPToolResponse(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any] = {}
    version: str = "1.0.0"


class MCPResourceResponse(BaseModel):
    uri: str
    name: str
    description: str
    mime_type: str = "text/plain"


class MCPDiscoveryResponse(BaseModel):
    tools: list[MCPToolResponse] = []
    resources: list[MCPResourceResponse] = []
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
    checks: dict[str, bool] = {}
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
    session_id: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload: dict[str, Any] = {}


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
