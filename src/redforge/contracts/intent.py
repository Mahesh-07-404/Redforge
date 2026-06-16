from enum import Enum
from pydantic import BaseModel

class IntentType(str, Enum):
    SCAN = "scan"
    RECON = "recon"
    EXPLOIT = "exploit"
    REPORT = "report"
    LEARN = "learn"
    CONFIGURE = "configure"
    CLARIFY = "clarify"
    UNKNOWN = "unknown"

class RiskLevel(str, Enum):
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    DESTRUCTIVE = "destructive"

class ParsedIntent(BaseModel):
    raw_input: str
    intent_type: IntentType
    risk_level: RiskLevel
    target: str | None
    target_changed: bool
    mode: str
    entities: dict[str, str]
    requires_approval: bool
    session_id: str
