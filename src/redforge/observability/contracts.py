from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import time


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AuditStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    DENIED = "denied"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class HealthState(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class LogEntry(BaseModel):
    timestamp: float = Field(default_factory=time.time)
    log_level: LogLevel = LogLevel.INFO
    component: str
    message: str
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    workflow_id: Optional[str] = None
    execution_id: Optional[str] = None
    duration: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MetricRecord(BaseModel):
    name: str
    value: float
    labels: Dict[str, str] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)


class TraceSpan(BaseModel):
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    name: str
    start_time: float = Field(default_factory=time.time)
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)


class AuditEntry(BaseModel):
    event_id: str
    event_type: str
    actor: str
    action: str
    status: AuditStatus
    timestamp: float = Field(default_factory=time.time)
    details: Dict[str, Any] = Field(default_factory=dict)
    signature: str = ""  # SHA-256 hash verifying immutability


class SystemResourceUsage(BaseModel):
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    memory_used_mb: float
    memory_total_mb: float


class ComponentHealth(BaseModel):
    name: str
    state: HealthState
    message: Optional[str] = None
    latency_ms: Optional[float] = None


class HealthStatus(BaseModel):
    overall_state: HealthState
    components: List[ComponentHealth] = Field(default_factory=list)
    resources: SystemResourceUsage
    timestamp: float = Field(default_factory=time.time)


class AlertRecord(BaseModel):
    alert_id: str
    severity: AlertSeverity
    title: str
    message: str
    source: str
    timestamp: float = Field(default_factory=time.time)
    resolved: bool = False
    resolved_at: Optional[float] = None
