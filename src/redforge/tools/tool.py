from typing import List, Optional
from pydantic import BaseModel

class Tool(BaseModel):
    id: str
    name: str
    binary: str
    version: Optional[str] = None
    platforms: List[str] = []
    supported_modes: List[str] = []
    categories: List[str] = []
    description: str
    capabilities: List[str] = []
    required_permissions: List[str] = []
    install_method: str = "apt"
    documentation: Optional[str] = None
    health: str = "healthy"
    availability: bool = False
    
    # Backward compatibility attributes
    command: Optional[str] = None
    package: Optional[str] = None
    install_command: Optional[str] = None
    category: Optional[str] = None
    essential: bool = False
    min_version: Optional[str] = None
    alternatives: List[str] = []
