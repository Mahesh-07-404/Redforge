from __future__ import annotations

import asyncio
import logging
import time
import inspect
from typing import Callable, List, Optional
from .contracts import TaskMessage, TaskResult, TaskStatus, WorkerStatus
from .registry import WorkerRegistry
from .exceptions import DistributedError

logger = logging.getLogger(__name__)


class DistributedWorker:
    """A worker node that auto-registers, sends heartbeats, and executes tasks."""

    def __init__(
        self,
        worker_id: str,
        host: str = "localhost",
        capabilities: Optional[List[str]] = None,
        registry: Optional[WorkerRegistry] = None,
        heartbeat_interval: float = 2.0,
        executor_fn: Optional[Callable[[TaskMessage], TaskResult]] = None,
    ) -> None:
        self.worker_id = worker_id
        self.host = host
        self.capabilities = capabilities or ["all"]
        self.registry = registry
        self.heartbeat_interval = heartbeat_interval
        
        # Internal executor function (falls back to executing a mock/real process)
        self.executor_fn = executor_fn or self._default_execute
        
        self.status = WorkerStatus.ONLINE
        self.load = 0
        self._running = False
        self._heartbeat_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Register worker and start heartbeat updates."""
        if self._running:
            return
        self._running = True
        
        # Self-register
        if self.registry:
            self.registry.register(
                worker_id=self.worker_id,
                host=self.host,
                capabilities=self.capabilities,
            )
            # Start heartbeat loop
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def stop(self) -> None:
        """Stop worker loops and unregister."""
        self._running = False
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None
            
        if self.registry:
            self.registry.unregister(self.worker_id)

    async def execute_task(self, task: TaskMessage) -> TaskResult:
        """Execute task message payload and return structured outcome."""
        self.load += 1
        start_time = time.time()
        
        try:
            # Check timeout handling
            if task.timeout:
                try:
                    result = await asyncio.wait_for(
                        self._run_executor_fn(task),
                        timeout=task.timeout
                    )
                except asyncio.TimeoutError:
                    result = TaskResult(
                        task_id=task.task_id,
                        status=TaskStatus.FAILED,
                        exit_code=124,
                        stderr="Task execution timed out.",
                        error="TimeoutError",
                        duration_ms=(time.time() - start_time) * 1000,
                    )
            else:
                result = await self._run_executor_fn(task)
        except Exception as exc:
            result = TaskResult(
                task_id=task.task_id,
                status=TaskStatus.FAILED,
                exit_code=1,
                stderr=str(exc),
                error=exc.__class__.__name__,
                duration_ms=(time.time() - start_time) * 1000,
            )
        finally:
            self.load = max(0, self.load - 1)
            
        return result

    async def _run_executor_fn(self, task: TaskMessage) -> TaskResult:
        # Run executor_fn (which can be a sync or async function)
        if inspect.iscoroutinefunction(self.executor_fn):
            return await self.executor_fn(task)
        else:
            # Run in executor thread pool if it's blocking sync
            return await asyncio.to_thread(self.executor_fn, task)

    def _default_execute(self, task: TaskMessage) -> TaskResult:
        """Fallback mock tool executor."""
        start_time = time.time()
        # Mock execution logic
        time.sleep(0.1)  # Simulate short work
        
        # Mocking specific tool behavior for tests
        if task.tool == "nmap":
            stdout = f"Host {task.command[-1]} up. Ports 80, 443 open."
            exit_code = 0
            status = TaskStatus.COMPLETED
            err_msg = None
        elif task.tool == "error_tool":
            stdout = ""
            exit_code = 1
            status = TaskStatus.FAILED
            err_msg = "Tool simulated failure."
        else:
            stdout = f"Command {task.command} finished successfully."
            exit_code = 0
            status = TaskStatus.COMPLETED
            err_msg = None
            
        duration = (time.time() - start_time) * 1000
        return TaskResult(
            task_id=task.task_id,
            status=status,
            exit_code=exit_code,
            stdout=stdout,
            duration_ms=duration,
            error=err_msg,
        )

    async def _heartbeat_loop(self) -> None:
        while self._running:
            try:
                if self.registry:
                    self.registry.heartbeat(self.worker_id, load=self.load)
            except Exception as exc:  # nosec B110 - heartbeat loop must survive transient registry errors
                logger.warning("Worker %s heartbeat encountered an error: %s", self.worker_id, exc)
            await asyncio.sleep(self.heartbeat_interval)
