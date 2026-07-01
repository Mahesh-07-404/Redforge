from pydantic import BaseModel

from .base import BaseToolOutput


class SqlmapVulnerability(BaseModel):
    parameter: str
    type: str
    payload: str


class SqlmapResult(BaseToolOutput):
    tool_name: str = "sqlmap"
    vulnerable: bool
    vulnerabilities: list[SqlmapVulnerability]
