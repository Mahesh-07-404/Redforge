from .client import MCPClient
from .server import MCPServer


class MCPManager:
    def __init__(self):
        self.server = MCPServer()
        self.client = MCPClient(self.server)
