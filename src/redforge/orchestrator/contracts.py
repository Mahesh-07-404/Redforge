from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from ..planner.task import Task
from ..planner.plan import Plan

class AgentAssignment(BaseModel):
    agent_id: str
    task_id: str
    assigned_at: str

class AgentTaskResult(BaseModel):
    task_id: str
    agent_id: str
    status: str
    output: str
    duration: float = 0.0

class OrchestrationResult(BaseModel):
    plan_goal: str
    status: str
    agent_results: List[AgentTaskResult] = []
    duration: float = 0.0
