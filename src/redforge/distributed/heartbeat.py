from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable, Coroutine

from .registry import WorkerRegistry

logger = logging.getLogger(__name__)


class HeartbeatMonitor:
    """Monitors worker heartbeat timeouts and triggers recovery callbacks."""

    def __init__(
        self,
        registry: WorkerRegistry,
        recovery_callback: Callable[[str], Coroutine[None, None, None]],
        check_interval: float = 3.0,
    ) -> None:
        self.registry = registry
        self.recovery_callback = recovery_callback
        self.check_interval = check_interval
        self._task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        """Start the background monitoring loop."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        """Stop the background monitoring loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _run_loop(self) -> None:
        while self._running:
            try:
                offline_worker_ids = self.registry.cleanup_offline_workers()
                for worker_id in offline_worker_ids:
                    # Invoke async recovery callback
                    await self.recovery_callback(worker_id)
            except Exception as exc:  # nosec B110 - heartbeat loop must survive transient errors
                logger.warning("Heartbeat monitoring loop encountered an error: %s", exc)
            await asyncio.sleep(self.check_interval)
