from .contracts import PluginMetadata


class PluginRegistry:
    def __init__(self):
        self.plugins: dict[str, PluginMetadata] = {}
        self.enabled_states: dict[str, bool] = {}

    def register(self, metadata: PluginMetadata) -> None:
        self.plugins[metadata.id] = metadata
        self.enabled_states[metadata.id] = True

    def unregister(self, plugin_id: str) -> None:
        if plugin_id in self.plugins:
            del self.plugins[plugin_id]
            del self.enabled_states[plugin_id]

    def set_enabled(self, plugin_id: str, enabled: bool) -> None:
        if plugin_id in self.enabled_states:
            self.enabled_states[plugin_id] = enabled

    def is_enabled(self, plugin_id: str) -> bool:
        return self.enabled_states.get(plugin_id, False)

    def get_plugin(self, plugin_id: str) -> PluginMetadata | None:
        return self.plugins.get(plugin_id)

    def list_plugins(self) -> list[PluginMetadata]:
        return list(self.plugins.values())
