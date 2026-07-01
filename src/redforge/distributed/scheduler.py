from __future__ import annotations

import asyncio

from .contracts import TaskMessage, TaskStatus
from .queue import BaseQueue


class DistributedScheduler:
    """Handles dependency-aware scheduling, priority queues, and task graph resolution."""

    def __init__(self, queue: BaseQueue) -> None:
        self.queue = queue
        # In-memory tracking of task dependency graphs
        self._pending_tasks: dict[str, TaskMessage] = {}
        self._completed_tasks: set[str] = set()
        self._failed_tasks: set[str] = set()
        # Maps dependency_id -> set of task_ids waiting on it
        self._waiting_on: dict[str, set[str]] = {}
        self._lock = asyncio.Lock()

    async def schedule(self, task: TaskMessage) -> None:
        """Schedule a task. Resolves dependencies. Pushes to queue if unblocked."""
        async with self._lock:
            # Check dependencies
            unresolved = [dep for dep in task.dependencies if dep not in self._completed_tasks]

            if unresolved:
                task.status = TaskStatus.PENDING
                self._pending_tasks[task.task_id] = task
                for dep in unresolved:
                    if dep not in self._waiting_on:
                        self._waiting_on[dep] = set()
                    self._waiting_on[dep].add(task.task_id)
            else:
                # No unresolved dependencies, push straight to queue
                await self.queue.push(task)

    async def complete_task(self, task_id: str) -> list[TaskMessage]:
        """Record task completion. Unblocks dependent children and returns newly ready tasks."""
        async with self._lock:
            self._completed_tasks.add(task_id)
            newly_ready: list[TaskMessage] = []

            # Find tasks waiting on this one
            waiting_ids = self._waiting_on.pop(task_id, set())
            for tid in waiting_ids:
                task = self._pending_tasks.get(tid)
                if not task:
                    continue
                # Check if all dependencies for this task are now resolved
                still_unresolved = [
                    dep for dep in task.dependencies if dep not in self._completed_tasks
                ]
                if not still_unresolved:
                    self._pending_tasks.pop(tid)
                    task.status = TaskStatus.QUEUED
                    await self.queue.push(task)
                    newly_ready.append(task)

            return newly_ready

    async def fail_task(self, task_id: str) -> list[str]:
        """Record task failure. Recursively cancels all dependent child tasks and returns cancelled IDs."""
        async with self._lock:
            self._failed_tasks.add(task_id)
            cancelled_ids: list[str] = []

            # Recursive cancellation helper
            queue_to_cancel = list(self._waiting_on.pop(task_id, set()))
            while queue_to_cancel:
                tid = queue_to_cancel.pop(0)
                task = self._pending_tasks.pop(tid, None)
                if task:
                    task.status = TaskStatus.CANCELLED
                    cancelled_ids.append(tid)

                    # Recursively add anyone waiting on tid
                    more_waiting = self._waiting_on.pop(tid, set())
                    queue_to_cancel.extend(more_waiting)

            return cancelled_ids

    async def cancel_task(self, task_id: str) -> list[str]:
        """Cancel a task from the active queue and recursively cancel its children."""
        async with self._lock:
            cancelled_ids = [task_id]
            # Try removing from queue
            await self.queue.remove(task_id)

            # Remove from pending if there
            self._pending_tasks.pop(task_id, None)

            # Cancel children
            queue_to_cancel = list(self._waiting_on.pop(task_id, set()))
            while queue_to_cancel:
                tid = queue_to_cancel.pop(0)
                task = self._pending_tasks.pop(tid, None)
                if task:
                    task.status = TaskStatus.CANCELLED
                    cancelled_ids.append(tid)
                    more_waiting = self._waiting_on.pop(tid, set())
                    queue_to_cancel.extend(more_waiting)

            return cancelled_ids

    async def get_state(self) -> dict[str, Any]:
        """Get summary of current scheduler states."""
        async with self._lock:
            return {
                "pending_count": len(self._pending_tasks),
                "completed_count": len(self._completed_tasks),
                "failed_count": len(self._failed_tasks),
                "waiting_dependency_nodes": len(self._waiting_on),
            }
