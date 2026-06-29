from typing import List, Dict, Any, Callable
from pydantic import BaseModel

class AgentMessage(BaseModel):
    message_type: str  # TaskAssigned, TaskStarted, TaskCompleted, TaskFailed, etc.
    sender: str
    recipient: str
    data: Dict[str, Any] = {}

class CommunicationBus:
    def __init__(self):
        self._subscribers: List[Callable[[AgentMessage], None]] = []

    def subscribe(self, callback: Callable[[AgentMessage], None]):
        self._subscribers.append(callback)

    def publish(self, msg: AgentMessage):
        for sub in self._subscribers:
            try:
                sub(msg)
            except Exception:
                pass
