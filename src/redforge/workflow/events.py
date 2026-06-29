from typing import Callable, List

class WorkflowEvents:
    def __init__(self):
        self._listeners: List[Callable[[str, str], None]] = []

    def subscribe(self, callback: Callable[[str, str], None]):
        self._listeners.append(callback)

    def fire(self, event_type: str, message: str):
        for listener in self._listeners:
            try:
                listener(event_type, message)
            except Exception:
                pass
