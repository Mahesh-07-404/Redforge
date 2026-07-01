from __future__ import annotations

import time
from typing import Dict, List, Optional
from .contracts import WorkerMetadata, WorkerStatus
from .exceptions import WorkerNotFoundError


class WorkerRegistry:
    """Thread-safe Registry of active Distributed Workers."""

    def __init__(self, heartbeat_timeout: float = 15.0) -> None:
        self.heartbeat_timeout = heartbeat_timeout
        self._workers: Dict[str, WorkerMetadata] = {}

    def register(
        self,
        worker_id: str,
        host: str,
        capabilities: List[str],
        weight: float = 1.0,
    ) -> WorkerMetadata:
        """Register or update a worker node."""
        worker = WorkerMetadata(
            worker_id=worker_id,
            host=host,
            capabilities=capabilities,
            weight=weight,
            status=WorkerStatus.ONLINE,
            last_heartbeat=time.time(),
        )
        self._workers[worker_id] = worker
        return worker

    def unregister(self, worker_id: str) -> None:
        """Remove a worker from the registry."""
        self._workers.pop(worker_id, None)

    def heartbeat(self, worker_id: str, load: int = 0) -> None:
        """Record a heartbeat signal from a worker."""
        worker = self._workers.get(worker_id)
        if not worker:
            raise WorkerNotFoundError(f"Worker '{worker_id}' is not registered.")
        worker.last_heartbeat = time.time()
        worker.load = load
        worker.status = WorkerStatus.ONLINE

    def get(self, worker_id: str) -> Optional[WorkerMetadata]:
        """Get worker details."""
        return self._workers.get(worker_id)

    def list_workers(self) -> List[WorkerMetadata]:
        """List all registered workers."""
        return list(self._workers.values())

    def list_online_workers(self) -> List[WorkerMetadata]:
        """List registered workers that are online and active."""
        self.cleanup_offline_workers()
        return [
            w for w in self._workers.values()
            if w.status == WorkerStatus.ONLINE
        ]

    def cleanup_offline_workers(self) -> List[str]:
        """Mark workers offline if they missed heartbeats. Return marked IDs."""
        now = time.time()
        marked = []
        for worker in list(self._workers.values()):
            if now - worker.last_heartbeat > self.heartbeat_timeout:
                if worker.status != WorkerStatus.OFFLINE:
                    worker.status = WorkerStatus.OFFLINE
                    marked.append(worker.worker_id)
        return marked
