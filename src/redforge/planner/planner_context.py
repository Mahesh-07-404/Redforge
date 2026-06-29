from typing import Optional, Dict, Any
from pydantic import BaseModel
from ..contracts.session import Session
from ..contracts.intent import ParsedIntent

class PlannerContext(BaseModel):
    active_session: Optional[Session] = None
    target: Optional[str] = None
    current_goal: Optional[str] = None
    intent: Optional[ParsedIntent] = None
    user_preferences: Dict[str, Any] = {}
    active_mode: Optional[str] = None
