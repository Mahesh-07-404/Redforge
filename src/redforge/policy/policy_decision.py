from enum import Enum
from typing import List, Optional
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
    reason: Optional[str] = None
    warnings: List[str] = []
    required_permissions: List[str] = []
