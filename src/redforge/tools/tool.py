from pydantic import BaseModel


class Tool(BaseModel):
    id: str
    name: str
    binary: str
    version: str | None = None
    platforms: list[str] = []
    supported_modes: list[str] = []
    categories: list[str] = []
    description: str
    capabilities: list[str] = []
    required_permissions: list[str] = []
    install_method: str = "apt"
    documentation: str | None = None
    health: str = "healthy"
    availability: bool = False

    # Backward compatibility attributes
    command: str | None = None
    package: str | None = None
    install_command: str | None = None
    category: str | None = None
    essential: bool = False
    min_version: str | None = None
    alternatives: list[str] = []
