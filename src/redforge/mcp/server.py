from typing import List
from .contracts import MCPTool, MCPResource
from .registry import MCPRegistry

class MCPServer:
    def __init__(self):
        self.registry = MCPRegistry()

    def list_tools(self) -> List[MCPTool]:
        return list(self.registry.tools.values())

    def list_resources(self) -> List[MCPResource]:
        return list(self.registry.resources.values())
