from .contracts import MCPResource, MCPTool
from .registry import MCPRegistry


class MCPServer:
    def __init__(self):
        self.registry = MCPRegistry()

    def list_tools(self) -> list[MCPTool]:
        return list(self.registry.tools.values())

    def list_resources(self) -> list[MCPResource]:
        return list(self.registry.resources.values())
