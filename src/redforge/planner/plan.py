from pydantic import BaseModel

from .task import Task


class Plan(BaseModel):
    goal: str
    ordered_tasks: list[Task] = []
    dependency_graph: dict[str, list[str]] = {}  # task_id -> list of dependencies
    estimated_duration: int = 0
    confidence: float = 1.0
    warnings: list[str] = []
    required_tools: list[str] = []
    approval_required: bool = False
