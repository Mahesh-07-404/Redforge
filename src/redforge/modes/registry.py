from typing import Dict, Optional, List
from dataclasses import dataclass, field

@dataclass
class ModeConfig:
    name: str
    description: str
    essential_tools: List[str] = field(default_factory=list)
    skills_dir: str = ""

class ModeRegistry:
    def __init__(self):
        self.modes: Dict[str, ModeConfig] = {}

    def register(self, config: ModeConfig):
        self.modes[config.name] = config

    def get(self, name: str) -> Optional[ModeConfig]:
        return self.modes.get(name)

    def list_modes(self) -> List[ModeConfig]:
        return list(self.modes.values())
