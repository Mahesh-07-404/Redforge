from enum import Enum
from pydantic import BaseModel

class IntentType(str, Enum):
    # Legacy intents
    SCAN = "scan"
    RECON = "recon"
    EXPLOIT = "exploit"
    LEARN = "learn"
    CONFIGURE = "configure"
    CLARIFY = "clarify"
    
    # Phase 2 intents
    GENERAL_CHAT = "general_chat"
    BUG_BOUNTY = "bugbounty"
    PENTEST = "pentest"
    CTF = "ctf"
    LEARNING = "learning"
    REPORT = "report"
    SESSION = "session"
    HELP = "help"
    TOOL = "tool"
    CONFIG = "config"
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
    entities: dict[str, str] = {}
    requires_approval: bool
    session_id: str
