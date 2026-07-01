from __future__ import annotations

import time
import uuid
from typing import Callable, Dict, List, Optional
from .contracts import AlertRecord, AlertSeverity
from .logger import StructuredLogger


class AlertsEngine:
    """Dispatches alerts and tracks warning states across subsystems."""

    def __init__(self, logger: Optional[StructuredLogger] = None) -> None:
        self.logger = logger or StructuredLogger("alerts")
        self._alerts: Dict[str, AlertRecord] = {}
        self._handlers: List[Callable[[AlertRecord], None]] = []

    def register_handler(self, handler: Callable[[AlertRecord], None]) -> None:
        """Register custom alert callback handler."""
        self._handlers.append(handler)

    def trigger(
        self,
        severity: AlertSeverity,
        title: str,
        message: str,
        source: str,
    ) -> AlertRecord:
        """Trigger an operational alert."""
        alert_id = str(uuid.uuid4())
        alert = AlertRecord(
            alert_id=alert_id,
            severity=severity,
            title=title,
            message=message,
            source=source,
            timestamp=time.time(),
        )
        
        self._alerts[alert_id] = alert
        
        # Log structured warning/error
        log_msg = f"[{severity.value.upper()}] {title} - {message} (Source: {source})"
        if severity == AlertSeverity.CRITICAL:
            self.logger.critical(log_msg, alert_id=alert_id, source=source)
        elif severity == AlertSeverity.WARNING:
            self.logger.warning(log_msg, alert_id=alert_id, source=source)
        else:
            self.logger.info(log_msg, alert_id=alert_id, source=source)
            
        # Dispatch to custom handler callbacks
        for handler in self._handlers:
            try:
                handler(alert)
            except Exception:
                pass
                
        return alert

    def resolve(self, alert_id: str) -> None:
        """Resolve an active alert."""
        alert = self._alerts.get(alert_id)
        if alert:
            alert.resolved = True
            alert.resolved_at = time.time()
            self.logger.info(f"Alert resolved: {alert.title}", alert_id=alert_id)

    def list_active(self) -> List[AlertRecord]:
        """List active unresolved alerts."""
        return [a for a in self._alerts.values() if not a.resolved]

    def list_all(self) -> List[AlertRecord]:
        """List all triggered alerts (both active and resolved)."""
        return list(self._alerts.values())

    def clear(self) -> None:
        """Clear alerts history."""
        self._alerts.clear()
