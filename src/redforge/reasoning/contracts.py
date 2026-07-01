from pydantic import BaseModel


class Goal(BaseModel):
    id: str
    text: str
    status: str
    created_at: str


class ReasoningDecision(BaseModel):
    action: str
    reason: str
    next_task_id: str | None = None
    strategy: str | None = None
