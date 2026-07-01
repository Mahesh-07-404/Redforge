import logging
from collections.abc import Callable

from .events import ExecutionEvent

logger = logging.getLogger(__name__)


class StreamManager:
    def __init__(self):
        self._subscribers: list[Callable[[ExecutionEvent], None]] = []

    def subscribe(self, callback: Callable[[ExecutionEvent], None]):
        self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[ExecutionEvent], None]):
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def emit(self, event: ExecutionEvent):
        for sub in self._subscribers:
            try:
                sub(event)
            except Exception as exc:  # nosec B110 - isolated subscriber; must not crash stream
                logger.warning("Stream subscriber raised an error (event=%s): %s", event, exc)
