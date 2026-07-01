from __future__ import annotations

import time
from typing import Dict, List, Optional
from .exceptions import LeaseExpiredError


class LeaseInfo:
    def __init__(self, task_id: str, worker_id: str, expires_at: float) -> None:
        self.task_id = task_id
        self.worker_id = worker_id
        self.expires_at = expires_at


class LeaseManager:
    """Manages active task execution leases assigned to workers."""

    def __init__(self) -> None:
        self._leases: Dict[str, LeaseInfo] = {}

    def acquire(self, task_id: str, worker_id: str, duration: float) -> None:
        expires_at = time.time() + duration
        self._leases[task_id] = LeaseInfo(task_id, worker_id, expires_at)

    def release(self, task_id: str) -> None:
        self._leases.pop(task_id, None)

    def renew(self, task_id: str, worker_id: str, duration: float) -> None:
        lease = self._leases.get(task_id)
        if not lease:
            raise LeaseExpiredError(f"No active lease found for task '{task_id}'.")
        if lease.worker_id != worker_id:
            raise LeaseExpiredError(
                f"Lease for task '{task_id}' is owned by worker '{lease.worker_id}', not '{worker_id}'."
            )
        lease.expires_at = time.time() + duration

    def get_owner(self, task_id: str) -> Optional[str]:
        lease = self._leases.get(task_id)
        if lease and lease.expires_at > time.time():
            return lease.worker_id
        return None

    def check_expired(self) -> List[str]:
        """Find task IDs of expired leases and remove them."""
        now = time.time()
        expired = []
        for task_id, lease in list(self._leases.items()):
            if lease.expires_at < now:
                expired.append(task_id)
                self._leases.pop(task_id, None)
        return expired
