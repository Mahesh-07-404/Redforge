from typing import List, Optional
from pydantic import BaseModel

class Task(BaseModel):
    id: str
    title: str
    description: str
    tool_hint: Optional[str] = None
    estimated_duration: int = 0  # in seconds
    dependencies: List[str] = []
    risk: str = "safe"
    requires_confirmation: bool = False
    status: str = "pending"
