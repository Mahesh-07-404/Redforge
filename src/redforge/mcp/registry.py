from typing import Dict
from .contracts import MCPTool, MCPResource

class MCPRegistry:
    def __init__(self):
        self.tools: Dict[str, MCPTool] = {}
        self.resources: Dict[str, MCPResource] = {}

    def register_tool(self, tool: MCPTool):
        self.tools[tool.name] = tool

    def register_resource(self, resource: MCPResource):
        self.resources[resource.uri] = resource
