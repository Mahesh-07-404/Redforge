"""LangGraph-based agent state and schema"""

from typing import Annotated, List, Dict, Any, Optional, Literal
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import operator


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
    args: Dict[str, Any]
    result: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None


@dataclass
class Task:
    id: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[str] = None
    subtasks: List["Task"] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


@dataclass
class Finding:
    id: str
    type: str
    severity: str
    title: str
    description: str
    target: str
    evidence: Optional[Dict[str, Any]] = None
    cvss: Optional[float] = None
    cwe: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    tool: Optional[str] = None
    command: Optional[str] = None
    status: str = "VERIFIED"


@dataclass
class Message:
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)


class AgentState(BaseModel):
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    target: Optional[str] = None
    workflow_phase: WorkflowPhase = WorkflowPhase.PLAN
    current_task: Optional[str] = None
    tasks: List[Dict[str, Any]] = Field(default_factory=list)
    findings: List[Dict[str, Any]] = Field(default_factory=list)
    reports: List[Dict[str, Any]] = Field(default_factory=list)
    tools_used: List[str] = Field(default_factory=list)
    iteration: int = 0
    total_tokens: int = 0
    context: Dict[str, Any] = Field(default_factory=dict)
    skills_loaded: List[str] = Field(default_factory=list)
    autonomy_level: AutonomyLevel = AutonomyLevel.MANUAL
    mode: AgentMode = AgentMode.GOAL_BASED
    loop_count: int = 0
    last_state_hash: Optional[str] = None
    pending_confirmation: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    workspace_id: Optional[str] = None
    workspace_name: Optional[str] = None
    active_mode: Optional[str] = None
    intent: Optional[str] = None


def create_initial_state(
    user_input: str,
    target: Optional[str] = None,
    workspace_id: Optional[str] = None,
    workspace_name: Optional[str] = None,
    autonomy_level: AutonomyLevel = AutonomyLevel.MANUAL,
    mode: AgentMode = AgentMode.GOAL_BASED,
    active_mode: Optional[str] = None,
) -> AgentState:
    """Create initial agent state from user input"""
    if active_mode is None:
        active_mode = "bugbounty" if mode == AgentMode.GOAL_BASED else "learning"

    return AgentState(
        messages=[{
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        }],
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
            "started_at": datetime.now().isoformat()
        }
    )
