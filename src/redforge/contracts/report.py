from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Evidence(BaseModel):
    tool_name: str
    command: list[str]
    raw_output_excerpt: str
    verified: bool


class Finding(BaseModel):
    id: str
    session_id: str
    title: str
    severity: Severity
    description: str
    evidence: list[Evidence]
    cvss_score: float | None
    cve_ids: list[str]
    remediation: str | None
    created_at: datetime
    target: str


class ReportRequest(BaseModel):
    session_id: str
    format: str


class Report(BaseModel):
    content: str
