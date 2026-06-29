from typing import Callable, List
from .events import ExecutionEvent

class StreamManager:
    def __init__(self):
        self._subscribers: List[Callable[[ExecutionEvent], None]] = []

    def subscribe(self, callback: Callable[[ExecutionEvent], None]):
        self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[ExecutionEvent], None]):
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def emit(self, event: ExecutionEvent):
        for sub in self._subscribers:
            try:
                sub(event)
            except Exception:
                pass
