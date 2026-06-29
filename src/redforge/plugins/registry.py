from typing import Dict, List
from .contracts import PluginMetadata

class PluginRegistry:
    def __init__(self):
        self.plugins: Dict[str, PluginMetadata] = {}
        self.enabled_states: Dict[str, bool] = {}

    def register(self, metadata: PluginMetadata):
        self.plugins[metadata.id] = metadata
        self.enabled_states[metadata.id] = True

    def unregister(self, plugin_id: str):
        if plugin_id in self.plugins:
            del self.plugins[plugin_id]
            del self.enabled_states[plugin_id]

    def set_enabled(self, plugin_id: str, enabled: bool):
        if plugin_id in self.enabled_states:
            self.enabled_states[plugin_id] = enabled

    def is_enabled(self, plugin_id: str) -> bool:
        return self.enabled_states.get(plugin_id, False)

    def get_plugin(self, plugin_id: str) -> PluginMetadata:
        return self.plugins.get(plugin_id)

    def list_plugins(self) -> List[PluginMetadata]:
        return list(self.plugins.values())
