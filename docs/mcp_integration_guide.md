# MCP Integration Guide

This guide explains how RedForge integrates with the Model Context Protocol (MCP) framework.

## MCP Protocol Overview

MCP enables secure sharing of tools and resources across AI agents. In RedForge, the server exposes local tool capabilities and file resources, while client endpoints discover and invoke them.

## Declaring MCP Tools

To declare a new tool on the server:

```python
from redforge.mcp.contracts import MCPTool
from redforge.mcp.server import MCPServer

server = MCPServer()
server.registry.register_tool(
    MCPTool(
        name="custom_grep",
        description="Search for queries in files",
        input_schema={"query": {"type": "string"}}
    )
)
```

## Discovery

Clients query tools or resources directly:

```python
from redforge.mcp.client import MCPClient

client = MCPClient(server)
tools = client.get_available_tools()
for tool in tools:
    print(f"Discovered: {tool.name}")
```
