"""Lazy core exports for RedForge."""

import warnings

warnings.filterwarnings(
    "ignore",
    message=r"Core Pydantic V1 functionality isn't compatible with Python 3\.14 or greater\.",
    category=UserWarning,
    module=r"langchain_core\._api\.deprecation",
)


def __getattr__(name: str):
    if name in {"Settings", "get_settings"}:
        from redforge.core.config import Settings, get_settings

        return {"Settings": Settings, "get_settings": get_settings}[name]

    if name == "RedForgeAgent":
        from .factory import create_redforge_agent
        return create_redforge_agent

    if name in {"AgentState", "AutonomyLevel", "AgentMode"}:
        from redforge.core.state import AgentMode, AgentState, AutonomyLevel

        return {
            "AgentState": AgentState,
            "AutonomyLevel": AutonomyLevel,
            "AgentMode": AgentMode,
        }[name]

    if name == "AutonomyController":
        from redforge.core.autonomy_controller import AutonomyController

        return AutonomyController

    if name == "LoopDetector":
        from redforge.core.loop_detector import LoopDetector

        return LoopDetector

    if name == "SkillLoader":
        from redforge.core.skill_loader import SkillLoader

        return SkillLoader

    raise AttributeError(name)

__all__ = [
    "Settings",
    "get_settings",
    "RedForgeAgent",
    "AgentState",
    "AutonomyLevel",
    "AgentMode",
    "AutonomyController",
    "LoopDetector",
    "SkillLoader",
]
