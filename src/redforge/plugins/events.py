from typing import Callable, List

class PluginEvents:
    def __init__(self):
        self.listeners: List[Callable[[str, str], None]] = []

    def subscribe(self, callback: Callable[[str, str], None]):
        self.listeners.append(callback)

    def fire(self, event_type: str, plugin_id: str):
        for listener in self.listeners:
            try:
                listener(event_type, plugin_id)
            except Exception:
                pass
