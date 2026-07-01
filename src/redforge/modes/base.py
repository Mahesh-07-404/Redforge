"""Base mode interface"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ModeType(Enum):
    BUGBOUNTY = "bugbounty"
    CTF = "ctf"
    LEARNING = "learning"
    CODING = "coding"
    ANDROID = "android"


@dataclass
class ModeResult:
    success: bool
    message: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    findings: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class BaseMode(ABC):
    """Abstract base class for all modes"""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.name = self.__class__.__name__

    @abstractmethod
    async def execute(self, task: str, **kwargs) -> ModeResult:
        """Execute the mode with given task"""
        pass

    @abstractmethod
    def get_prompt(self) -> str:
        """Get mode-specific system prompt"""
        pass

    def validate_scope(self, target: str) -> bool:
        """Validate if target is in scope"""
        return True

    def get_available_tools(self) -> list[str]:
        """Get list of tools available for this mode"""
        return []

    def get_required_tools(self) -> list[str]:
        """Get list of required tools for this mode"""
        return []

    def get_default_context(self) -> dict[str, Any]:
        """Get default context for this mode"""
        return {
            "mode": self.name,
            "type": (
                ModeType[self.name.upper()].value
                if self.name.upper() in ModeType.__members__
                else "unknown"
            ),
        }
