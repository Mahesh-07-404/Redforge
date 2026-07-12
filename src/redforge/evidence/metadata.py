from pydantic import BaseModel


class ArtifactMetadata(BaseModel):
    session_id: str
    execution_id: str
    task_id: str
    tool: str
    target: str
    timestamp: str
    duration: float
    exit_code: int
    risk: str
    status: str
    hash: str
    platform: str
    tool_version: str = "1.0.0"
