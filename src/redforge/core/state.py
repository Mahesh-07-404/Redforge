"""LangGraph-based agent state and schema"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AutonomyLevel(str, Enum):
    MANUAL = "manual"
    PARTIAL = "partial"
    FULL = "full"


class AgentMode(str, Enum):
    GOAL_BASED = "goal"
    KNOWLEDGE_BASED = "knowledge"


class WorkflowPhase(str, Enum):
    PLAN = "plan"
    EXECUTE = "execute"
    VERIFY = "verify"
    STORE = "store"
    REPORT = "report"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class ToolCall:
    tool: str
    args: dict[str, Any]
    result: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    error: str | None = None


@dataclass
class Task:
    id: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    result: str | None = None
    subtasks: list["Task"] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None


@dataclass
class Finding:
    id: str
    type: str
    severity: str
    title: str
    description: str
    target: str
    evidence: dict[str, Any] | None = None
    cvss: float | None = None
    cwe: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    tool: str | None = None
    command: str | None = None
    status: str = "VERIFIED"


@dataclass
class Message:
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)


class AgentState(BaseModel):
    messages: list[dict[str, Any]] = Field(default_factory=list)
    target: str | None = None
    workflow_phase: WorkflowPhase = WorkflowPhase.PLAN
    current_task: str | None = None
    tasks: list[dict[str, Any]] = Field(default_factory=list)
    findings: list[dict[str, Any]] = Field(default_factory=list)
    reports: list[dict[str, Any]] = Field(default_factory=list)
    tools_used: list[str] = Field(default_factory=list)
    iteration: int = 0
    total_tokens: int = 0
    context: dict[str, Any] = Field(default_factory=dict)
    skills_loaded: list[str] = Field(default_factory=list)
    autonomy_level: AutonomyLevel = AutonomyLevel.MANUAL
    mode: AgentMode = AgentMode.GOAL_BASED
    loop_count: int = 0
    last_state_hash: str | None = None
    pending_confirmation: dict[str, Any] | None = None
    error: str | None = None
    workspace_id: str | None = None
    workspace_name: str | None = None
    active_mode: str | None = None
    intent: str | None = None


def create_initial_state(
    user_input: str,
    target: str | None = None,
    workspace_id: str | None = None,
    workspace_name: str | None = None,
    autonomy_level: AutonomyLevel = AutonomyLevel.MANUAL,
    mode: AgentMode = AgentMode.GOAL_BASED,
    active_mode: str | None = None,
) -> AgentState:
    """Create initial agent state from user input"""
    if active_mode is None:
        active_mode = "bugbounty" if mode == AgentMode.GOAL_BASED else "learning"

    return AgentState(
        messages=[{"role": "user", "content": user_input, "timestamp": datetime.now().isoformat()}],
        target=target,
        workspace_id=workspace_id,
        workspace_name=workspace_name,
        autonomy_level=autonomy_level,
        mode=mode,
        active_mode=active_mode,
        workflow_phase=WorkflowPhase.PLAN,
        context={
            "target": target,
            "workspace_id": workspace_id,
            "workspace_name": workspace_name,
            "started_at": datetime.now().isoformat(),
        },
    )
