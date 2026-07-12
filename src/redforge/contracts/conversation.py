from pydantic import BaseModel

from ..providers.base import Message
from .intent import ParsedIntent
from .session import Session


class ConversationContext(BaseModel):
    active_session: Session | None = None
    active_target: str | None = None
    current_goal: str | None = None
    current_intent: ParsedIntent | None = None
    previous_messages: list[Message] = []
    conversation_summary: str | None = None
