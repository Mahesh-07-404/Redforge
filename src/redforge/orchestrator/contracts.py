from pydantic import BaseModel


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
    agent_results: list[AgentTaskResult] = []
    duration: float = 0.0
