from __future__ import annotations

from typing import Any

from .contracts import TaskMessage, TaskResult, TaskStatus
from .lease import LeaseManager
from .load_balancer import LoadBalancer
from .queue import BaseQueue
from .registry import WorkerRegistry


class TaskDispatcher:
    """Dispatches tasks to workers using load balancing policies and lease monitoring."""

    def __init__(
        self,
        queue: BaseQueue,
        registry: WorkerRegistry,
        load_balancer: LoadBalancer,
        lease_manager: LeaseManager,
        algorithm: str = "least_loaded",
    ) -> None:
        self.queue = queue
        self.registry = registry
        self.load_balancer = load_balancer
        self.lease_manager = lease_manager
        self.algorithm = algorithm

        # Dead-letter queue (DLQ) for failed/unroutable tasks
        self.dead_letter_queue: list[TaskMessage] = []
        # Active local instances maps: worker_id -> Worker Object (if simulated locally)
        self._worker_instances: dict[str, Any] = {}

    def register_worker_instance(self, worker_id: str, instance: Any) -> None:
        """Register worker instance directly for dispatching tasks locally."""
        self._worker_instances[worker_id] = instance

    async def dispatch(self) -> TaskResult | None:
        """Pop a task, match to a worker, execute, manage lease, and return result."""
        task = await self.queue.pop()
        if not task:
            return None

        # Check workers
        online_workers = self.registry.list_online_workers()
        worker = self.load_balancer.select(task, online_workers, self.algorithm)

        if not worker:
            # Re-queue or DLQ depending on retry count
            task.retries += 1
            if task.retries > task.max_retries:
                task.status = TaskStatus.DEAD_LETTER
                self.dead_letter_queue.append(task)
            else:
                task.status = TaskStatus.QUEUED
                await self.queue.push(task)
            return None

        # Acquire execution lease
        self.lease_manager.acquire(task.task_id, worker.worker_id, task.timeout)
        task.status = TaskStatus.RUNNING
        task.lease_owner = worker.worker_id

        # Execute (simulate dispatch to worker instance)
        worker_obj = self._worker_instances.get(worker.worker_id)
        if not worker_obj:
            # If no local worker instance is registered, simulate dispatch success
            self.lease_manager.release(task.task_id)
            return None

        try:
            # Let worker run task
            result = await worker_obj.execute_task(task)
            self.lease_manager.release(task.task_id)
            return result
        except Exception as exc:
            self.lease_manager.release(task.task_id)
            return TaskResult(
                task_id=task.task_id,
                status=TaskStatus.FAILED,
                error=f"Dispatcher execution failure: {exc}",
            )
