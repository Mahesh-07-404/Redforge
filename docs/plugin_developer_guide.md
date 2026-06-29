# Plugin Developer Guide

This guide explains how to write custom plugins for RedForge using the Plugin SDK.

## Plugin Types

Plugins in RedForge can be one of the following types:
- **Tool Plugin**: Extends the workspace with new executable security tools.
- **Workflow Plugin**: Adds custom workflows for target pentesting/active scanning.
- **Agent Plugin**: Exposes new specialized agents inheriting from `BaseAgent`.
- **Report Plugin**: Renders customized findings to alternative output report targets.
- **Memory Provider**: Hooks custom databases for long-term semantic records.
- **RAG Provider**: Custom embedding or vector retrieval adapters.
- **Authentication Provider**: Controls platform authorization API headers.

## Declaring Metadata

A plugin must define its structure inside a `PluginMetadata` schema:

```python
from redforge.plugins.contracts import PluginMetadata

metadata = PluginMetadata(
    id="custom_scanner",
    name="Custom Port Scanner",
    version="1.0.0",
    description="Uses custom scripts for lightweight scanning",
    author="Admin",
    plugin_type="Tool",
    dependencies=["base_recon"],
    permissions=["read_file", "execute_tool"]
)
```

## Hook Listeners

Register callbacks to execute at specific stages of execution:

```python
from redforge.plugins import PluginManager

manager = PluginManager()
manager.hooks.register_hook("before_plan", lambda: print("Executing custom scanning rules..."))
```
