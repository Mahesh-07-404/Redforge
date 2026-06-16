from datetime import datetime
from enum import Enum
from pydantic import BaseModel
from .intent import RiskLevel

class ToolCall(BaseModel):
    tool_name: str
    command: list[str]
    target: str
    timeout_seconds: int
    risk_level: RiskLevel
    session_id: str
    approved: bool

class ToolResult(BaseModel):
    tool_name: str
    command: list[str]
    exit_code: int
    stdout: str
    stderr: str
    parsed_output: dict
    execution_time_ms: int
    timed_out: bool
    error: str | None

class VerificationStatus(str, Enum):
    PASSED = "passed"
    FAILED_SCHEMA = "failed_schema"
    FAILED_SCOPE = "failed_scope"
    FAILED_TIMEOUT = "failed_timeout"
    FAILED_ERROR = "failed_error"

class VerifiedResult(BaseModel):
    tool_result: ToolResult
    status: VerificationStatus
    verified_at: datetime
    facts: list[str]
    anomalies: list[str]
