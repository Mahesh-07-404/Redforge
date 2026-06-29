class OrchestratorError(Exception):
    """Base exception for the orchestrator package"""
    pass

class AgentLoadError(OrchestratorError):
    """Raised when an agent fails to load"""
    pass

class TaskScheduleError(OrchestratorError):
    """Raised when task scheduling fails"""
    pass
