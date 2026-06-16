from pydantic import BaseModel

class BaseToolOutput(BaseModel):
    tool_name: str
    success: bool
    error: str | None = None
