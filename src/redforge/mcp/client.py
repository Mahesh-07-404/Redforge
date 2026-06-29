from typing import List
from .server import MCPServer
from .contracts import MCPTool, MCPResource

class MCPClient:
    def __init__(self, server: MCPServer):
        self.server = server

    def get_available_tools(self) -> List[MCPTool]:
        return self.server.list_tools()

    def get_available_resources(self) -> List[MCPResource]:
        return self.server.list_resources()
