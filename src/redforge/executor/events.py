from typing import Any

from pydantic import BaseModel


class ExecutionEvent(BaseModel):
    event_type: str
    task_id: str | None = None
    data: dict[str, Any] = {}
