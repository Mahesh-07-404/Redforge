from .contracts import PluginMetadata
from .events import PluginEvents
from .hooks import PluginHooks
from .loader import PluginLoader
from .registry import PluginRegistry


class PluginManager:
    def __init__(self):
        self.registry = PluginRegistry()
        self.loader = PluginLoader(self.registry)
        self.hooks = PluginHooks()
        self.events = PluginEvents()

    def install_plugin(self, metadata: PluginMetadata):
        self.loader.load_plugin(metadata)
        self.events.fire("installed", metadata.id)

    def uninstall_plugin(self, plugin_id: str):
        self.registry.unregister(plugin_id)
        self.events.fire("uninstalled", plugin_id)

    def enable_plugin(self, plugin_id: str):
        self.registry.set_enabled(plugin_id, True)
        self.events.fire("enabled", plugin_id)

    def disable_plugin(self, plugin_id: str):
        self.registry.set_enabled(plugin_id, False)
        self.events.fire("disabled", plugin_id)
