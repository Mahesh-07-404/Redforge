from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from .session import Session
from .intent import ParsedIntent
from ..providers.base import Message

class ConversationContext(BaseModel):
    active_session: Optional[Session] = None
    active_target: Optional[str] = None
    current_goal: Optional[str] = None
    current_intent: Optional[ParsedIntent] = None
    previous_messages: List[Message] = []
    conversation_summary: Optional[str] = None
