from typing import List
from pydantic import BaseModel

class PluginMetadata(BaseModel):
    id: str
    name: str
    version: str
    description: str
    author: str
    plugin_type: str
    dependencies: List[str] = []
    permissions: List[str] = []
