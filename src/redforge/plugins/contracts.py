from pydantic import BaseModel


class PluginMetadata(BaseModel):
    id: str
    name: str
    version: str
    description: str
    author: str
    plugin_type: str
    dependencies: list[str] = []
    permissions: list[str] = []
