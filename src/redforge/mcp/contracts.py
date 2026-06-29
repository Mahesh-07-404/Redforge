from typing import Dict, Any, Optional
from pydantic import BaseModel

class MCPTool(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any] = {}

class MCPResource(BaseModel):
    uri: str
    name: str
    description: str
    mime_type: Optional[str] = None
