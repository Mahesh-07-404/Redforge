from __future__ import annotations

import asyncio
import time
from typing import Dict, List, Optional
from .contracts import TaskMessage, TaskResult, TaskStatus
from .queue import BaseQueue
from .registry import WorkerRegistry
from .scheduler import DistributedScheduler
from .dispatcher import TaskDispatcher
from .lease import LeaseManager
from .retry import RetryPolicy
from .heartbeat import HeartbeatMonitor


class DistributedCoordinator:
    """Core Coordinator coordinating tasks, schedules, fault-tolerance, and monitoring."""

    def __init__(
        self,
        queue: BaseQueue,
        registry: WorkerRegistry,
        scheduler: DistributedScheduler,
        dispatcher: TaskDispatcher,
        lease_manager: LeaseManager,
        retry_policy: RetryPolicy,
    ) -> None:
        self.queue = queue
        self.registry = registry
        self.scheduler = scheduler
        self.dispatcher = dispatcher
        self.lease_manager = lease_manager
        self.retry_policy = retry_policy

        # Background loops tasks
        self._running = False
        self._heartbeat_monitor = HeartbeatMonitor(
            registry=self.registry,
            recovery_callback=self.handle_worker_failure,
        )
        self._lease_loop_task: Optional[asyncio.Task] = None
        self._dispatch_loop_task: Optional[asyncio.Task] = None
        
        # Results collection for finished tasks
        self.results: Dict[str, TaskResult] = {}
        # List of all submitted tasks in registry
        self.tasks: Dict[str, TaskMessage] = {}
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        """Start distributed coordinator monitoring and scheduling loops."""
        if self._running:
            return
        self._running = True
        
        await self._heartbeat_monitor.start()
        self._lease_loop_task = asyncio.create_task(self._lease_check_loop())
        self._dispatch_loop_task = asyncio.create_task(self._dispatch_loop())

    async def stop(self) -> None:
        """Stop distributed coordinator monitoring loops."""
        self._running = False
        await self._heartbeat_monitor.stop()
        
        if self._lease_loop_task:
            self._lease_loop_task.cancel()
            try:
                await self._lease_loop_task
            except asyncio.CancelledError:
                pass
            self._lease_loop_task = None
            
        if self._dispatch_loop_task:
            self._dispatch_loop_task.cancel()
            try:
                await self._dispatch_loop_task
            except asyncio.CancelledError:
                pass
            self._dispatch_loop_task = None

    async def submit_task(self, task: TaskMessage) -> None:
        """Submit a task to the coordinator."""
        async with self._lock:
            self.tasks[task.task_id] = task
        await self.scheduler.schedule(task)

    async def handle_worker_failure(self, worker_id: str) -> None:
        """Invoked when a worker goes offline. Reschedules outstanding leases."""
        # Find tasks leased by this worker
        tasks_to_recover = []
        async with self._lock:
            for task_id, task in self.tasks.items():
                owner = self.lease_manager.get_owner(task_id)
                if owner == worker_id and task.status == TaskStatus.RUNNING:
                    tasks_to_recover.append(task_id)

        for task_id in tasks_to_recover:
            self.lease_manager.release(task_id)
            await self._reschedule_task(task_id, f"Worker '{worker_id}' failed heartbeat.")

    async def _reschedule_task(self, task_id: str, reason: str) -> None:
        """Reschedule a task based on its retry policy."""
        task = self.tasks.get(task_id)
        if not task:
            return

        if self.retry_policy.should_retry(task):
            task.retries += 1
            task.status = TaskStatus.QUEUED
            delay = self.retry_policy.get_delay(task)
            
            # Wait for backoff delay before pushing back
            async def re_push():
                await asyncio.sleep(delay)
                await self.queue.push(task)
            
            asyncio.create_task(re_push())
        else:
            task.status = TaskStatus.DEAD_LETTER
            self.dispatcher.dead_letter_queue.append(task)
            # Cascade failures to dependees
            cancelled_ids = await self.scheduler.fail_task(task_id)
            for cid in cancelled_ids:
                ctask = self.tasks.get(cid)
                if ctask:
                    ctask.status = TaskStatus.CANCELLED

    async def _lease_check_loop(self) -> None:
        """Periodically check for expired leases and reschedule tasks."""
        while self._running:
            try:
                expired_task_ids = self.lease_manager.check_expired()
                for task_id in expired_task_ids:
                    await self._reschedule_task(task_id, "Lease expired.")
            except Exception:
                pass
            await asyncio.sleep(1.0)

    async def _dispatch_loop(self) -> None:
        """Continuously pops ready tasks and schedules them on workers."""
        while self._running:
            try:
                # Retrieve result if task dispatched and executed successfully
                result = await self.dispatcher.dispatch()
                if result:
                    self.results[result.task_id] = result
                    task = self.tasks.get(result.task_id)
                    if task:
                        if result.status == TaskStatus.COMPLETED:
                            task.status = TaskStatus.COMPLETED
                            # Unblock children
                            await self.scheduler.complete_task(result.task_id)
                        else:
                            # Task execution failed on worker, try rescheduling/retrying
                            await self._reschedule_task(result.task_id, result.error or "Task failed.")
            except Exception:
                pass
            await asyncio.sleep(0.5)

    async def get_stats(self) -> dict:
        """Return running execution statistics for monitoring endpoints."""
        async with self._lock:
            statuses = {
                "pending": 0,
                "queued": 0,
                "assigned": 0,
                "running": 0,
                "completed": 0,
                "failed": 0,
                "cancelled": 0,
                "dead_letter": 0,
            }
            for t in self.tasks.values():
                val = t.status.value
                if val in statuses:
                    statuses[val] += 1
            return {
                "total_tasks": len(self.tasks),
                "task_statuses": statuses,
                "online_workers": len(self.registry.list_online_workers()),
                "dlq_size": len(self.dispatcher.dead_letter_queue),
            }
