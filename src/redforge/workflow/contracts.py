from typing import Any

from pydantic import BaseModel


class WorkflowStage(BaseModel):
    id: str
    name: str
    agent: str
    planner_strategy: str
    required_tools: list[str] = []
    policy_level: str = "medium"
    timeout: float = 300.0
    retries: int = 1
    dependencies: list[str] = []


class WorkflowDefinition(BaseModel):
    id: str
    name: str
    description: str
    supported_intents: list[str]
    required_target: bool = True
    stages: list[WorkflowStage]
    dependencies: list[str] = []
    conditions: list[str] = []
    retry_policy: dict[str, Any] = {}
    timeout: float = 1800.0
    approval_requirements: str = "none"
