import pytest
from redforge.plugins.contracts import PluginMetadata
from redforge.plugins.exceptions import PluginLoadError
from redforge.plugins.sandbox import PluginSandbox
from redforge.plugins.permissions import PluginPermissionManager
from redforge.plugins.manager import PluginManager
from redforge.mcp.contracts import MCPTool, MCPResource
from redforge.mcp.server import MCPServer
from redforge.mcp.client import MCPClient
from redforge.mcp.transport import MCPTransport

def test_plugin_installation_and_dependency():
    manager = PluginManager()
    
    p1 = PluginMetadata(
        id="base_plugin",
        name="Base Plugin",
        version="1.0.0",
        description="Base helper",
        author="Admin",
        plugin_type="Tool"
    )
    
    p2 = PluginMetadata(
        id="dep_plugin",
        name="Dependent Plugin",
        version="1.0.0",
        description="Depends on base_plugin",
        author="Admin",
        plugin_type="Agent",
        dependencies=["base_plugin"]
    )
    
    # Installing p2 first should raise PluginLoadError since dependency is missing
    with pytest.raises(PluginLoadError):
        manager.install_plugin(p2)
        
    manager.install_plugin(p1)
    manager.install_plugin(p2)
    
    assert manager.registry.get_plugin("dep_plugin") is not None
    assert manager.registry.is_enabled("dep_plugin") is True
    
    # Test disable
    manager.disable_plugin("dep_plugin")
    assert manager.registry.is_enabled("dep_plugin") is False

def test_plugin_sandbox_and_permissions():
    sandbox = PluginSandbox(granted_permissions=["read_file"])
    
    def test_func(x):
        return x * 2
        
    res = sandbox.execute_safely(test_func, 5)
    assert res == 10
    
    # Verify permission checking
    assert PluginPermissionManager.verify_permissions(["read_file"], ["read_file", "write_file"]) is True
    assert PluginPermissionManager.verify_permissions(["execute_tool"], ["read_file"]) is False

def test_plugin_hooks():
    manager = PluginManager()
    triggered = []
    
    manager.hooks.register_hook("before_plan", lambda: triggered.append("before_plan"))
    manager.hooks.trigger_hook("before_plan")
    
    assert len(triggered) == 1
    assert triggered[0] == "before_plan"

@pytest.mark.asyncio
async def test_mcp_discovery_and_communication():
    server = MCPServer()
    server.registry.register_tool(MCPTool(name="test_tool", description="Test description"))
    server.registry.register_resource(MCPResource(uri="file://test", name="test_resource", description="Test description"))
    
    client = MCPClient(server)
    
    tools = client.get_available_tools()
    resources = client.get_available_resources()
    
    assert len(tools) == 1
    assert tools[0].name == "test_tool"
    assert len(resources) == 1
    
    # Test transport output structure
    transport = MCPTransport()
    res = await transport.send_message({"action": "list_tools"})
    assert "jsonrpc" in res
