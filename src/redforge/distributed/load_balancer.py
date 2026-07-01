from __future__ import annotations

from .contracts import TaskMessage, WorkerMetadata


class LoadBalancer:
    """Selects target Workers for Task execution based on configurable algorithms."""

    def __init__(self) -> None:
        self._round_robin_index = 0

    def select(
        self,
        task: TaskMessage,
        workers: list[WorkerMetadata],
        algorithm: str = "least_loaded",
    ) -> WorkerMetadata | None:
        """
        Select a worker for the task.
        Filters workers by capability matching (worker must support task.tool).
        """
        # Filter by capabilities (Capability-based routing)
        capable_workers = [
            w
            for w in workers
            if not task.tool or task.tool in w.capabilities or "all" in w.capabilities
        ]

        if not capable_workers:
            return None

        algo = algorithm.lower()
        if algo == "round_robin":
            return self._round_robin(capable_workers)
        elif algo == "least_loaded":
            return self._least_loaded(capable_workers)
        elif algo == "weighted":
            return self._weighted(capable_workers)
        else:
            # Default to least loaded
            return self._least_loaded(capable_workers)

    def _round_robin(self, workers: list[WorkerMetadata]) -> WorkerMetadata:
        self._round_robin_index = (self._round_robin_index + 1) % len(workers)
        return workers[self._round_robin_index]

    def _least_loaded(self, workers: list[WorkerMetadata]) -> WorkerMetadata:
        # Load: number of active running tasks. Returns the minimum loaded.
        return min(workers, key=lambda w: w.load)

    def _weighted(self, workers: list[WorkerMetadata]) -> WorkerMetadata:
        # Choose minimum of (load / weight)
        return min(workers, key=lambda w: w.load / max(w.weight, 0.1))
