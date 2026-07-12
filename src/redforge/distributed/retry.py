from __future__ import annotations

import math

from .contracts import TaskMessage


class RetryPolicy:
    """Manages Task retry count limit and exponential backoff calculations."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential: bool = True,
    ) -> None:
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential = exponential

    def should_retry(self, task: TaskMessage) -> bool:
        """Check if the task has retries left."""
        limit = task.max_retries if task.max_retries is not None else self.max_retries
        return task.retries < limit

    def get_delay(self, task: TaskMessage) -> float:
        """Compute the backoff delay for the next retry attempt."""
        if not self.exponential:
            return self.base_delay
        delay = self.base_delay * math.pow(2, task.retries)
        return min(delay, self.max_delay)
