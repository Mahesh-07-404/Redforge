from __future__ import annotations

import logging
import time
from typing import Any, Callable, Dict, List, Set

logger = logging.getLogger(__name__)


class ObservabilityEvent:
    def __init__(self, name: str, data: Dict[str, Any]) -> None:
        self.name = name
        self.data = data
        self.timestamp = time.time()


class EventBus:
    """Manages publishing and subscribing to system observability events."""

    def __init__(self) -> None:
        self._listeners: Dict[str, Set[Callable[[ObservabilityEvent], None]]] = {}

    def subscribe(self, event_name: str, handler: Callable[[ObservabilityEvent], None]) -> None:
        """Subscribe to a specific event name."""
        if event_name not in self._listeners:
            self._listeners[event_name] = set()
        self._listeners[event_name].add(handler)

    def unsubscribe(self, event_name: str, handler: Callable[[ObservabilityEvent], None]) -> None:
        """Unsubscribe from a specific event name."""
        if event_name in self._listeners:
            self._listeners[event_name].discard(handler)

    def publish(self, name: str, data: Dict[str, Any]) -> None:
        """Publish an event to all registered subscriber callbacks."""
        event = ObservabilityEvent(name, data)
        # Notify specific listeners
        listeners = self._listeners.get(name, set())
        for handler in listeners:
            try:
                handler(event)
            except Exception as exc:  # nosec B110 - isolated handler; must not crash event bus
                logger.warning("Observability event handler raised an error (event=%s): %s", name, exc)
                
        # Notify wildcard listeners
        wildcard_listeners = self._listeners.get("*", set())
        for handler in wildcard_listeners:
            try:
                handler(event)
            except Exception as exc:  # nosec B110 - isolated handler; must not crash event bus
                logger.warning("Observability wildcard handler raised an error (event=%s): %s", name, exc)
