"""RedForge - Autonomous Intent-Based Cybersecurity Agent

Autonomous security testing framework with:
- Unified Autonomous agent
- 128+ specialized skills
- LangGraph agent orchestration
- Workspace memory with RAG
- Safety engine and tool management
"""

__version__ = "0.1.0"
__author__ = "RedForge Team"

from redforge.contracts import Finding
from redforge.core.agent import RedForgeAgent

# Core exports
from redforge.core.safety import SafetyEngine, SafetyLevel, Scope
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
    # Agent
    "RedForgeAgent",
    "Finding",
    # Advanced
    "CVEGenerator",
    "ReportGenerator",
    # Platforms
    "PlatformManager",
]
