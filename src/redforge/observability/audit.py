from __future__ import annotations

import hashlib
import json
import time
import uuid
from typing import Any

from .contracts import AuditEntry, AuditStatus


class AuditLogger:
    """Implements an immutable, cryptographically chained audit log validator."""

    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []
        self._last_signature: str = "genesis-block-00000000000000000000000000000000"

    def record(
        self,
        event_type: str,
        actor: str,
        action: str,
        status: AuditStatus = AuditStatus.SUCCESS,
        details: dict[str, Any] | None = None,
    ) -> AuditEntry:
        """Create and append an immutable audit log entry."""
        event_id = str(uuid.uuid4())
        timestamp = time.time()
        det = details or {}

        # Build canonical payload for hashing
        payload_data = {
            "event_id": event_id,
            "event_type": event_type,
            "actor": actor,
            "action": action,
            "status": status.value,
            "timestamp": timestamp,
            "details": det,
            "prev_signature": self._last_signature,
        }

        payload_str = json.dumps(payload_data, sort_keys=True)
        signature = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

        entry = AuditEntry(
            event_id=event_id,
            event_type=event_type,
            actor=actor,
            action=action,
            status=status,
            timestamp=timestamp,
            details=det,
            signature=signature,
        )

        self._entries.append(entry)
        self._last_signature = signature
        return entry

    def verify_chain(self) -> bool:
        """Verify the integrity of the audit log chain. Returns True if untouched."""
        temp_signature = "genesis-block-00000000000000000000000000000000"

        for entry in self._entries:
            # Reconstruct payload hash
            payload_data = {
                "event_id": entry.event_id,
                "event_type": entry.event_type,
                "actor": entry.actor,
                "action": entry.action,
                "status": entry.status.value,
                "timestamp": entry.timestamp,
                "details": entry.details,
                "prev_signature": temp_signature,
            }
            payload_str = json.dumps(payload_data, sort_keys=True)
            expected_signature = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

            if entry.signature != expected_signature:
                return False
            temp_signature = entry.signature

        return True

    def get_entries(self) -> list[AuditEntry]:
        """Get all recorded audit entries."""
        return self._entries

    def clear(self) -> None:
        """Clear audit history and reset signature chain."""
        self._entries.clear()
        self._last_signature = "genesis-block-00000000000000000000000000000000"
