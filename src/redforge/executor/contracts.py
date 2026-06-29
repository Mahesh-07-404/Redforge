from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from .state import ExecutionStatus
from ..planner.plan import Plan
from ..policy.policy_decision import PolicyDecision

class ApprovedPlan(BaseModel):
    plan: Plan
    decision: PolicyDecision

class TaskResult(BaseModel):
    task_id: str
    status: ExecutionStatus
    raw_output: str = ""
    structured_output: Dict[str, Any] = {}
    exit_code: int = 0
    duration: float = 0.0
    error: Optional[str] = None

class ExecutionResult(BaseModel):
    plan_goal: str
    status: ExecutionStatus
    task_results: List[TaskResult] = []
    duration: float = 0.0
