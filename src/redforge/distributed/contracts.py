from __future__ import annotations

import time
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WorkerStatus(str, Enum):
    ONLINE = "online"
    BUSY = "busy"
    OFFLINE = "offline"


class TaskStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    DEAD_LETTER = "dead_letter"


class WorkerMetadata(BaseModel):
    worker_id: str
    host: str
    capabilities: List[str] = Field(default_factory=list)
    status: WorkerStatus = WorkerStatus.ONLINE
    load: int = 0  # Number of running tasks
    weight: float = 1.0
    last_heartbeat: float = Field(default_factory=time.time)


class TaskMessage(BaseModel):
    task_id: str
    session_id: str
    tool: str
    command: List[str]
    priority: int = 0  # Higher value = higher priority
    dependencies: List[str] = Field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    retries: int = 0
    max_retries: int = 3
    timeout: float = 300.0  # seconds
    lease_owner: Optional[str] = None
    lease_expires_at: Optional[float] = None
    created_at: float = Field(default_factory=time.time)


class TaskResult(BaseModel):
    task_id: str
    status: TaskStatus
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    duration_ms: float = 0.0
    error: Optional[str] = None
    timestamp: float = Field(default_factory=time.time)


class HeartbeatMessage(BaseModel):
    worker_id: str
    timestamp: float = Field(default_factory=time.time)
    load: int = 0
    status: WorkerStatus = WorkerStatus.ONLINE
