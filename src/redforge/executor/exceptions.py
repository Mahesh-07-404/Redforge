class ExecutorError(Exception):
    """Base exception for executor errors"""
    pass

class ToolExecutionError(ExecutorError):
    """Raised when a tool fails to execute"""
    pass

class TaskTimeoutError(ExecutorError):
    """Raised when a task times out"""
    pass

class TaskCancelledError(ExecutorError):
    """Raised when a task is cancelled"""
    pass
