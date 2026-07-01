from pydantic import BaseModel


class Task(BaseModel):
    id: str
    title: str
    description: str
    tool_hint: str | None = None
    estimated_duration: int = 0  # in seconds
    dependencies: list[str] = []
    risk: str = "safe"
    requires_confirmation: bool = False
    status: str = "pending"
