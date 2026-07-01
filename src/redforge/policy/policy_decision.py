from enum import Enum

from pydantic import BaseModel


class DecisionStatus(Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRES_APPROVAL = "REQUIRES_APPROVAL"


class RiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PolicyDecision(BaseModel):
    status: DecisionStatus
    risk_level: RiskLevel
    reason: str | None = None
    warnings: list[str] = []
    required_permissions: list[str] = []
