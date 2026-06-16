from datetime import datetime
from pydantic import BaseModel

class TargetState(BaseModel):
    target: str | None
    changed: bool = False

class ModeState(BaseModel):
    mode: str

class SessionState(BaseModel):
    id: str
    mode: str
    target: str | None
    autonomy: str
    created_at: datetime
    updated_at: datetime
    status: str
