from __future__ import annotations

import time
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


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
    request_id: str | None = None
    session_id: str | None = None
    workflow_id: str | None = None
    execution_id: str | None = None
    duration: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class MetricRecord(BaseModel):
    name: str
    value: float
    labels: dict[str, str] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)


class TraceSpan(BaseModel):
    trace_id: str
    span_id: str
    parent_span_id: str | None = None
    name: str
    start_time: float = Field(default_factory=time.time)
    end_time: float | None = None
    duration_ms: float | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class AuditEntry(BaseModel):
    event_id: str
    event_type: str
    actor: str
    action: str
    status: AuditStatus
    timestamp: float = Field(default_factory=time.time)
    details: dict[str, Any] = Field(default_factory=dict)
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
    message: str | None = None
    latency_ms: float | None = None


class HealthStatus(BaseModel):
    overall_state: HealthState
    components: list[ComponentHealth] = Field(default_factory=list)
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
    resolved_at: float | None = None
