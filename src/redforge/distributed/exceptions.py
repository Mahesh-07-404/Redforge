from __future__ import annotations

class DistributedError(Exception):
    """Base exception for all distributed execution errors."""
    pass

class WorkerNotFoundError(DistributedError):
    """Raised when a worker is not found or has unregistered."""
    pass

class QueueError(DistributedError):
    """Raised when a queue operation fails."""
    pass

class TaskDispatchError(DistributedError):
    """Raised when a task cannot be dispatched to any worker."""
    pass

class WorkerOfflineError(DistributedError):
    """Raised when a worker fails to respond or is offline."""
    pass

class LeaseExpiredError(DistributedError):
    """Raised when a task lease has expired."""
    pass

class SchedulerError(DistributedError):
    """Raised when scheduling decisions fail."""
    pass
