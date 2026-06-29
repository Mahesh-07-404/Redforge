from typing import List
from .registry import ToolRegistry
from .tool import Tool

class ToolResolver:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def resolve_capability(self, capability: str) -> List[Tool]:
        return self.registry.lookup_tools_by_capability(capability)
