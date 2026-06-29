from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from .task import Task

class Plan(BaseModel):
    goal: str
    ordered_tasks: List[Task] = []
    dependency_graph: Dict[str, List[str]] = {}  # task_id -> list of dependencies
    estimated_duration: int = 0
    confidence: float = 1.0
    warnings: List[str] = []
    required_tools: List[str] = []
    approval_required: bool = False
