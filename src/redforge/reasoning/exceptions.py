class ReasoningError(Exception):
    """Base exception for reasoning engine"""
    pass

class GoalError(ReasoningError):
    """Goal management errors"""
    pass

class StrategyError(ReasoningError):
    """Strategy selector errors"""
    pass
