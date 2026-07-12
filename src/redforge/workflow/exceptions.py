class WorkflowError(Exception):
    """Base exception for workflows"""

    pass


class WorkflowValidationError(WorkflowError):
    """Raised when workflow validation fails"""

    pass


class WorkflowExecutionError(WorkflowError):
    """Raised when workflow execution fails"""

    pass
