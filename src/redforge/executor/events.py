from typing import Dict, Any, Optional
from pydantic import BaseModel

class ExecutionEvent(BaseModel):
    event_type: str
    task_id: Optional[str] = None
    data: Dict[str, Any] = {}
