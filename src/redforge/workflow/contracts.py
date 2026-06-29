from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class WorkflowStage(BaseModel):
    id: str
    name: str
    agent: str
    planner_strategy: str
    required_tools: List[str] = []
    policy_level: str = "medium"
    timeout: float = 300.0
    retries: int = 1
    dependencies: List[str] = []

class WorkflowDefinition(BaseModel):
    id: str
    name: str
    description: str
    supported_intents: List[str]
    required_target: bool = True
    stages: List[WorkflowStage]
    dependencies: List[str] = []
    conditions: List[str] = []
    retry_policy: Dict[str, Any] = {}
    timeout: float = 1800.0
    approval_requirements: str = "none"
