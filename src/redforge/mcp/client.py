from .contracts import MCPResource, MCPTool
from .server import MCPServer


class MCPClient:
    def __init__(self, server: MCPServer):
        self.server = server

    def get_available_tools(self) -> list[MCPTool]:
        return self.server.list_tools()

    def get_available_resources(self) -> list[MCPResource]:
        return self.server.list_resources()
