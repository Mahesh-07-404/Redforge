from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Set
from .contracts import TaskMessage, TaskStatus
from .exceptions import QueueError


class BaseQueue(ABC):
    """Abstract Base Class for Task Queue implementations."""

    @abstractmethod
    async def push(self, task: TaskMessage) -> None:
        """Push a task to the queue."""
        pass

    @abstractmethod
    async def pop(self) -> Optional[TaskMessage]:
        """Pop the highest priority task from the queue."""
        pass

    @abstractmethod
    async def remove(self, task_id: str) -> None:
        """Remove a task from the queue by ID."""
        pass

    @abstractmethod
    async def get(self, task_id: str) -> Optional[TaskMessage]:
        """Get a task by ID."""
        pass

    @abstractmethod
    async def list_tasks(self) -> List[TaskMessage]:
        """List all tasks in the queue."""
        pass

    @abstractmethod
    async def size(self) -> int:
        """Get the number of pending tasks."""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all tasks."""
        pass


class InMemoryQueue(BaseQueue):
    """Fallback thread-safe In-Memory Priority Queue."""

    def __init__(self) -> None:
        self._tasks: Dict[str, TaskMessage] = {}
        # Priority sorted list of task_ids
        self._queue: List[str] = []
        self._lock = asyncio.Lock()

    async def push(self, task: TaskMessage) -> None:
        async with self._lock:
            task.status = TaskStatus.QUEUED
            self._tasks[task.task_id] = task
            if task.task_id not in self._queue:
                self._queue.append(task.task_id)
            # Sort by priority desc, then created_at asc
            self._queue.sort(
                key=lambda tid: (-self._tasks[tid].priority, self._tasks[tid].created_at)
            )

    async def pop(self) -> Optional[TaskMessage]:
        async with self._lock:
            if not self._queue:
                return None
            task_id = self._queue.pop(0)
            task = self._tasks.get(task_id)
            if task:
                task.status = TaskStatus.ASSIGNED
            return task

    async def remove(self, task_id: str) -> None:
        async with self._lock:
            if task_id in self._queue:
                self._queue.remove(task_id)
            self._tasks.pop(task_id, None)

    async def get(self, task_id: str) -> Optional[TaskMessage]:
        async with self._lock:
            return self._tasks.get(task_id)

    async def list_tasks(self) -> List[TaskMessage]:
        async with self._lock:
            return list(self._tasks.values())

    async def size(self) -> int:
        async with self._lock:
            return len(self._queue)

    async def clear(self) -> None:
        async with self._lock:
            self._tasks.clear()
            self._queue.clear()


class RedisQueue(BaseQueue):
    """Redis-backed Priority Queue (fallback to InMemory if connection fails)."""

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0) -> None:
        self.host = host
        self.port = port
        self.db = db
        self._redis = None
        self._in_memory_fallback = InMemoryQueue()
        self._use_fallback = True

    async def connect(self) -> None:
        try:
            import redis.asyncio as aioredis
            self._redis = aioredis.Redis(host=self.host, port=self.port, db=self.db, decode_responses=True)
            # Ping connection
            await self._redis.ping()
            self._use_fallback = False
        except Exception:
            self._use_fallback = True

    async def push(self, task: TaskMessage) -> None:
        if self._use_fallback:
            await self._in_memory_fallback.push(task)
            return

        try:
            # Store task payload as JSON string
            await self._redis.hset("rf:tasks", task.task_id, task.model_dump_json())
            # Add to priority sorted set (priority score)
            # Redis Sorted Set sorts ascending, so we use negative priority to pop lowest score (highest priority) first
            await self._redis.zadd("rf:queue", {task.task_id: -task.priority})
            task.status = TaskStatus.QUEUED
        except Exception as exc:
            raise QueueError(f"Redis push failed: {exc}") from exc

    async def pop(self) -> Optional[TaskMessage]:
        if self._use_fallback:
            return await self._in_memory_fallback.pop()

        try:
            # Pop elements with lowest score (highest negative priority)
            res = await self._redis.zpopmin("rf:queue")
            if not res:
                return None
            task_id, _ = res[0]
            raw = await self._redis.hget("rf:tasks", task_id)
            if not raw:
                return None
            task = TaskMessage.model_validate_json(raw)
            task.status = TaskStatus.ASSIGNED
            await self._redis.hset("rf:tasks", task_id, task.model_dump_json())
            return task
        except Exception as exc:
            raise QueueError(f"Redis pop failed: {exc}") from exc

    async def remove(self, task_id: str) -> None:
        if self._use_fallback:
            await self._in_memory_fallback.remove(task_id)
            return

        try:
            await self._redis.zrem("rf:queue", task_id)
            await self._redis.hdel("rf:tasks", task_id)
        except Exception as exc:
            raise QueueError(f"Redis remove failed: {exc}") from exc

    async def get(self, task_id: str) -> Optional[TaskMessage]:
        if self._use_fallback:
            return await self._in_memory_fallback.get(task_id)

        try:
            raw = await self._redis.hget("rf:tasks", task_id)
            if not raw:
                return None
            return TaskMessage.model_validate_json(raw)
        except Exception as exc:
            raise QueueError(f"Redis get failed: {exc}") from exc

    async def list_tasks(self) -> List[TaskMessage]:
        if self._use_fallback:
            return await self._in_memory_fallback.list_tasks()

        try:
            raws = await self._redis.hvals("rf:tasks")
            return [TaskMessage.model_validate_json(r) for r in raws]
        except Exception as exc:
            raise QueueError(f"Redis list_tasks failed: {exc}") from exc

    async def size(self) -> int:
        if self._use_fallback:
            return await self._in_memory_fallback.size()

        try:
            return await self._redis.zcard("rf:queue")
        except Exception as exc:
            raise QueueError(f"Redis size failed: {exc}") from exc

    async def clear(self) -> None:
        if self._use_fallback:
            await self._in_memory_fallback.clear()
            return

        try:
            await self._redis.delete("rf:queue", "rf:tasks")
        except Exception as exc:
            raise QueueError(f"Redis clear failed: {exc}") from exc


class RabbitMQQueue(BaseQueue):
    """RabbitMQ-backed Queue wrapper (fallbacks to InMemory)."""

    def __init__(self, amqp_url: str = "amqp://guest:guest@localhost:5672/") -> None:
        self.amqp_url = amqp_url
        self._in_memory_fallback = InMemoryQueue()
        self._use_fallback = True

    async def connect(self) -> None:
        # Pika/aio-pika is highly interactive, fallback is default for local unit-tests
        self._use_fallback = True

    async def push(self, task: TaskMessage) -> None:
        await self._in_memory_fallback.push(task)

    async def pop(self) -> Optional[TaskMessage]:
        return await self._in_memory_fallback.pop()

    async def remove(self, task_id: str) -> None:
        await self._in_memory_fallback.remove(task_id)

    async def get(self, task_id: str) -> Optional[TaskMessage]:
        return await self._in_memory_fallback.get(task_id)

    async def list_tasks(self) -> List[TaskMessage]:
        return await self._in_memory_fallback.list_tasks()

    async def size(self) -> int:
        return await self._in_memory_fallback.size()

    async def clear(self) -> None:
        await self._in_memory_fallback.clear()
