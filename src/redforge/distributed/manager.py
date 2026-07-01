from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
from .contracts import TaskMessage, TaskResult, TaskStatus, WorkerMetadata
from .queue import BaseQueue, InMemoryQueue
from .registry import WorkerRegistry
from .scheduler import DistributedScheduler
from .dispatcher import TaskDispatcher
from .load_balancer import LoadBalancer
from .lease import LeaseManager
from .retry import RetryPolicy
from .coordinator import DistributedCoordinator
from .worker import DistributedWorker
from .autoscaler import DistributedAutoscaler


class DistributedManager:
    """Entry point for RedForge Distributed Execution Platform."""

    def __init__(
        self,
        queue: Optional[BaseQueue] = None,
        heartbeat_timeout: float = 10.0,
        algorithm: str = "least_loaded",
    ) -> None:
        self.queue = queue or InMemoryQueue()
        self.registry = WorkerRegistry(heartbeat_timeout=heartbeat_timeout)
        self.scheduler = DistributedScheduler(queue=self.queue)
        self.load_balancer = LoadBalancer()
        self.lease_manager = LeaseManager()
        self.retry_policy = RetryPolicy()
        
        self.dispatcher = TaskDispatcher(
            queue=self.queue,
            registry=self.registry,
            load_balancer=self.load_balancer,
            lease_manager=self.lease_manager,
            algorithm=algorithm,
        )
        
        self.coordinator = DistributedCoordinator(
            queue=self.queue,
            registry=self.registry,
            scheduler=self.scheduler,
            dispatcher=self.dispatcher,
            lease_manager=self.lease_manager,
            retry_policy=self.retry_policy,
        )
        
        # Initialize autoscaler (disabled by default until start_autoscaling called)
        self.autoscaler: Optional[DistributedAutoscaler] = None
        self._local_workers: Dict[str, DistributedWorker] = {}

    async def start(self) -> None:
        """Start the distributed execution engine coordination loops."""
        await self.coordinator.start()

    async def stop(self) -> None:
        """Stop all coordination loops and shut down local workers."""
        if self.autoscaler:
            await self.autoscaler.stop()
        await self.coordinator.stop()
        
        # Stop any manually registered local workers
        for worker in list(self._local_workers.values()):
            await worker.stop()
        self._local_workers.clear()

    async def create_local_worker(
        self,
        worker_id: str,
        capabilities: Optional[List[str]] = None,
        heartbeat_interval: float = 1.0,
    ) -> DistributedWorker:
        """Create and start a local worker node monitored by this manager."""
        worker = DistributedWorker(
            worker_id=worker_id,
            capabilities=capabilities,
            registry=self.registry,
            heartbeat_interval=heartbeat_interval,
        )
        await worker.start()
        self._local_workers[worker_id] = worker
        self.dispatcher.register_worker_instance(worker_id, worker)
        return worker

    async def start_autoscaling(
        self,
        min_workers: int = 1,
        max_workers: int = 5,
        scale_up_threshold: int = 2,
    ) -> None:
        """Enable dynamic autoscaling pool."""
        def worker_factory(wid: str) -> DistributedWorker:
            w = DistributedWorker(
                worker_id=wid,
                capabilities=["all"],
                registry=self.registry,
                heartbeat_interval=1.0,
            )
            self.dispatcher.register_worker_instance(wid, w)
            return w

        self.autoscaler = DistributedAutoscaler(
            registry=self.registry,
            queue=self.queue,
            worker_factory=worker_factory,
            min_workers=min_workers,
            max_workers=max_workers,
            scale_up_threshold=scale_up_threshold,
            check_interval=1.0,
        )
        await self.autoscaler.start()

    async def submit(
        self,
        task_id: str,
        session_id: str,
        tool: str,
        command: List[str],
        priority: int = 0,
        dependencies: Optional[List[str]] = None,
        timeout: float = 30.0,
    ) -> TaskMessage:
        """Submit a task to the execution scheduler."""
        task = TaskMessage(
            task_id=task_id,
            session_id=session_id,
            tool=tool,
            command=command,
            priority=priority,
            dependencies=dependencies or [],
            timeout=timeout,
        )
        await self.coordinator.submit_task(task)
        return task

    def get_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get the current execution status of a task."""
        task = self.coordinator.tasks.get(task_id)
        return task.status if task else None

    def get_result(self, task_id: str) -> Optional[TaskResult]:
        """Get the output results of a completed task."""
        return self.coordinator.results.get(task_id)

    async def get_monitoring_stats(self) -> Dict[str, Any]:
        """Return running execution statistics for monitoring endpoints."""
        return await self.coordinator.get_stats()
