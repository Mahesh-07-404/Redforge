from .contracts import PluginMetadata
from .registry import PluginRegistry
from .exceptions import PluginLoadError

class PluginLoader:
    def __init__(self, registry: PluginRegistry):
        self.registry = registry

    def load_plugin(self, metadata: PluginMetadata):
        for dep in metadata.dependencies:
            if not self.registry.get_plugin(dep):
                raise PluginLoadError(f"Missing dependency: {dep}")
        self.registry.register(metadata)
