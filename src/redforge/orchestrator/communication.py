import logging
from typing import List, Dict, Any, Callable
from pydantic import BaseModel

logger = logging.getLogger(__name__)

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
            except Exception as exc:  # nosec B110 - isolated subscriber; must not crash message bus
                logger.warning("CommunicationBus subscriber raised an error (type=%s): %s", msg.message_type, exc)
