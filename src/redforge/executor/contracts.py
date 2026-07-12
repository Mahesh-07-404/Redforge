from typing import Any

from pydantic import BaseModel

from ..planner.plan import Plan
from ..policy.policy_decision import PolicyDecision
from .state import ExecutionStatus


class ApprovedPlan(BaseModel):
    plan: Plan
    decision: PolicyDecision


class TaskResult(BaseModel):
    task_id: str
    status: ExecutionStatus
    raw_output: str = ""
    structured_output: dict[str, Any] = {}
    exit_code: int = 0
    duration: float = 0.0
    error: str | None = None


class ExecutionResult(BaseModel):
    plan_goal: str
    status: ExecutionStatus
    task_results: list[TaskResult] = []
    duration: float = 0.0
