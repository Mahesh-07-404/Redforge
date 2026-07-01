from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable

from .queue import BaseQueue
from .registry import WorkerRegistry
from .worker import DistributedWorker

logger = logging.getLogger(__name__)


class DistributedAutoscaler:
    """Manages worker pool sizing based on queue demand and active node load metrics."""

    def __init__(
        self,
        registry: WorkerRegistry,
        queue: BaseQueue,
        worker_factory: Callable[[str], DistributedWorker],
        min_workers: int = 1,
        max_workers: int = 10,
        scale_up_threshold: int = 3,  # Queue size trigger
        check_interval: float = 3.0,
    ) -> None:
        self.registry = registry
        self.queue = queue
        self.worker_factory = worker_factory
        self.min_workers = min_workers
        self.max_workers = max_workers
        self.scale_up_threshold = scale_up_threshold
        self.check_interval = check_interval

        self.active_autoscaled_workers: list[DistributedWorker] = []
        self._running = False
        self._loop_task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the background autoscaling monitoring loop."""
        if self._running:
            return
        self._running = True

        # Initialize to min_workers
        while len(self.active_autoscaled_workers) < self.min_workers:
            await self._scale_up()

        self._loop_task = asyncio.create_task(self._monitor_loop())

    async def stop(self) -> None:
        """Stop background loop and cleanup all scaled worker nodes."""
        self._running = False
        if self._loop_task:
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass
            self._loop_task = None

        # Stop all workers
        for worker in self.active_autoscaled_workers:
            await worker.stop()
        self.active_autoscaled_workers.clear()

    async def _monitor_loop(self) -> None:
        while self._running:
            try:
                q_size = await self.queue.size()
                workers = self.registry.list_online_workers()
                w_count = len(workers)

                # Check Scale-Up
                if q_size >= self.scale_up_threshold and w_count < self.max_workers:
                    await self._scale_up()
                # Check Scale-Down
                elif q_size == 0 and w_count > self.min_workers:
                    # Find worker with least load and scale it down
                    await self._scale_down()
            except Exception as exc:  # nosec B110 - monitoring loop must survive transient errors
                logger.warning("Autoscaler monitoring loop encountered an error: %s", exc)
            await asyncio.sleep(self.check_interval)

    async def _scale_up(self) -> None:
        worker_id = f"autoscaled-worker-{len(self.active_autoscaled_workers) + 1}"
        worker = self.worker_factory(worker_id)
        await worker.start()
        self.active_autoscaled_workers.append(worker)

    async def _scale_down(self) -> None:
        if not self.active_autoscaled_workers:
            return
        # Stop and remove the last added worker
        worker = self.active_autoscaled_workers.pop()
        await worker.stop()
