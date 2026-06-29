from .server import MCPServer
from .client import MCPClient

class MCPManager:
    def __init__(self):
        self.server = MCPServer()
        self.client = MCPClient(self.server)
