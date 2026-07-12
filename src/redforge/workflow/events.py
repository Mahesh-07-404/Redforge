import logging
from collections.abc import Callable

logger = logging.getLogger(__name__)


class WorkflowEvents:
    def __init__(self):
        self._listeners: list[Callable[[str, str], None]] = []

    def subscribe(self, callback: Callable[[str, str], None]):
        self._listeners.append(callback)

    def fire(self, event_type: str, message: str):
        for listener in self._listeners:
            try:
                listener(event_type, message)
            except (
                Exception
            ) as exc:  # nosec B110 - isolated listener; must not crash workflow events
                logger.warning(
                    "Workflow event listener raised an error (event=%s): %s", event_type, exc
                )
