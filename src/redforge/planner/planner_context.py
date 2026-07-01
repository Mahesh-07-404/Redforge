from typing import Any

from pydantic import BaseModel

from ..contracts.intent import ParsedIntent
from ..contracts.session import Session


class PlannerContext(BaseModel):
    active_session: Session | None = None
    target: str | None = None
    current_goal: str | None = None
    intent: ParsedIntent | None = None
    user_preferences: dict[str, Any] = {}
    active_mode: str | None = None
