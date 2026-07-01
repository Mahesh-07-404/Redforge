"""RedForge - CLI Pentesting AI Agent

Autonomous security testing framework with:
- 5 operational modes
- 128+ specialized skills
- LangGraph agent orchestration
- Workspace memory with RAG
- Safety engine and tool management
"""

__version__ = "0.1.0"
__author__ = "RedForge Team"

# Core exports
from redforge.core.safety import SafetyEngine, SafetyLevel, Scope
from redforge.modes.mode_implementations import (
    AndroidMode,
    BugBountyMode,
    CodingMode,
    CTFChallenge,
    CTFMode,
    Finding,
    LearningMode,
    Mode,
    ModeFactory,
)
from redforge.plugins import PlatformManager
from redforge.reports import CVEGenerator, ReportGenerator
from redforge.tools import Platform, ToolManager, ToolRegistry

__all__ = [
    # Version
    "__version__",
    # Safety
    "SafetyEngine",
    "SafetyLevel",
    "Scope",
    # Tools
    "ToolManager",
    "ToolRegistry",
    "Platform",
    # Modes
    "BugBountyMode",
    "CTFMode",
    "LearningMode",
    "CodingMode",
    "AndroidMode",
    "ModeFactory",
    "Mode",
    "Finding",
    "CTFChallenge",
    # Advanced
    "CVEGenerator",
    "ReportGenerator",
    # Platforms
    "PlatformManager",
]
