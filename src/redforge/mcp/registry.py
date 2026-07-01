from .contracts import MCPResource, MCPTool


class MCPRegistry:
    def __init__(self):
        self.tools: dict[str, MCPTool] = {}
        self.resources: dict[str, MCPResource] = {}

    def register_tool(self, tool: MCPTool):
        self.tools[tool.name] = tool

    def register_resource(self, resource: MCPResource):
        self.resources[resource.uri] = resource
