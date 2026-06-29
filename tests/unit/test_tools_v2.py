import pytest
from unittest.mock import MagicMock, patch
from redforge.tools.tool import Tool
from redforge.tools.capabilities import Capability
from redforge.tools.platform import detect_platform, PlatformInfo
from redforge.tools.discovery import ToolDiscovery
from redforge.tools.validator import ToolValidator
from redforge.tools.installer import ToolInstaller
from redforge.tools.registry import ToolRegistry
from redforge.tools.resolver import ToolResolver
from redforge.tools.exceptions import ToolNotFoundError
from redforge.planner.planner_context import PlannerContext
from redforge.contracts.intent import ParsedIntent, IntentType
from redforge.contracts.session import Session

def test_registry_lookup_and_cache():
    registry = ToolRegistry()
    
    # 1. Lookup nmap
    nmap = registry.lookup_tool_by_name("nmap")
    assert nmap.id == "nmap"
    assert nmap.binary == "nmap"
    assert Capability.PORT_SCANNING in nmap.capabilities
    
    # 2. Check that it is cached
    assert "nmap" in registry._cache
    
    # 3. Lookup from cache
    nmap_cached = registry.lookup_tool_by_name("nmap")
    assert nmap_cached is nmap
    
    # 4. Lookup nonexistent
    with pytest.raises(ToolNotFoundError):
        registry.lookup_tool_by_name("nonexistent")

def test_capability_mapping_and_ranking():
    registry = ToolRegistry()
    
    # Resolve subdomain enumeration capability
    tools = registry.lookup_tools_by_capability(Capability.SUBDOMAIN_ENUMERATION)
    assert len(tools) >= 3
    tool_ids = [t.id for t in tools]
    
    # Ranking test (subfinder should be ranked higher than amass/assetfinder)
    assert tool_ids[0] == "subfinder"
    assert "amass" in tool_ids
    assert "assetfinder" in tool_ids

def test_platform_detection():
    plat = detect_platform()
    assert plat.name in ("Arch Linux", "Kali Linux", "Ubuntu", "Debian", "Fedora", "macOS", "Windows", "Windows WSL")
    assert plat.package_manager in ("apt", "pacman", "dnf", "brew", "choco")
    assert len(plat.default_paths) > 0

def test_tool_discovery():
    # Test PATH finding for system binary (like 'ls' or 'sh' or 'cmd')
    import sys
    bin_name = "cmd.exe" if sys.platform == "win32" else "sh"
    path = ToolDiscovery.find_binary(bin_name)
    assert path is not None
    assert ToolDiscovery.get_version(path) == "1.0.0"

def test_tool_validator():
    validator = ToolValidator()
    
    # Valid tool
    valid_tool = Tool(
        id="test_sh", name="Shell", binary="sh" if import_sys_is_not_windows() else "cmd.exe",
        platforms=["Debian", "Kali Linux", "Ubuntu", "macOS", "Windows WSL", "Arch Linux", "Fedora", "Windows"],
        description="Test shell", capabilities=[Capability.PORT_SCANNING]
    )
    errors = validator.validate(valid_tool)
    assert not errors
    
    # Invalid tool (nonexistent binary)
    invalid_tool = Tool(
        id="invalid", name="Invalid Binary", binary="nonexistent_binary_xyz",
        description="Invalid description"
    )
    errors = validator.validate(invalid_tool)
    assert len(errors) > 0
    assert any("not found" in e for e in errors)

def test_tool_installer_plan():
    installer = ToolInstaller()
    tool = Tool(
        id="nuclei", name="Nuclei", binary="nuclei",
        platforms=["Kali Linux", "Ubuntu"], description="Scanner",
        package="nuclei", install_command="go install nuclei"
    )
    plan = installer.generate_install_plan(tool)
    assert plan["tool_id"] == "nuclei"
    assert "install_command" in plan
    assert len(plan["steps"]) >= 3

def test_planner_integration_resolver():
    registry = ToolRegistry()
    resolver = ToolResolver(registry)
    
    # Planner asks for Subdomain Enumeration
    tools = resolver.resolve_capability(Capability.SUBDOMAIN_ENUMERATION)
    assert len(tools) > 0
    assert tools[0].id == "subfinder"

def import_sys_is_not_windows():
    import sys
    return sys.platform != "win32"
