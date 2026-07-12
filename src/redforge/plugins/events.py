import logging
from collections.abc import Callable

logger = logging.getLogger(__name__)


class PluginEvents:
    def __init__(self):
        self.listeners: list[Callable[[str, str], None]] = []

    def subscribe(self, callback: Callable[[str, str], None]):
        self.listeners.append(callback)

    def fire(self, event_type: str, plugin_id: str):
        for listener in self.listeners:
            try:
                listener(event_type, plugin_id)
            except Exception as exc:  # nosec B110 - isolated listener; must not crash plugin events
                logger.warning(
                    "Plugin event listener raised an error (event=%s, plugin=%s): %s",
                    event_type,
                    plugin_id,
                    exc,
                )
