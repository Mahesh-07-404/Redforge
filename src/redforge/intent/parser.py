import re
from ..contracts.intent import ParsedIntent, IntentType, RiskLevel

class IntentParser:
    def parse(self, raw_input: str, current_mode: str, session_id: str) -> ParsedIntent:
        intent_type = IntentType.UNKNOWN
        risk_level = RiskLevel.SAFE
        target = None
        
        lower_input = raw_input.lower()
        if "scan" in lower_input:
            intent_type = IntentType.SCAN
            risk_level = RiskLevel.MEDIUM
        elif "recon" in lower_input:
            intent_type = IntentType.RECON
            risk_level = RiskLevel.LOW
        elif "exploit" in lower_input:
            intent_type = IntentType.EXPLOIT
            risk_level = RiskLevel.HIGH
            
        match = re.search(r'(?:https?://)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', raw_input)
        if match:
            target = match.group(1)
            
        return ParsedIntent(
            raw_input=raw_input,
            intent_type=intent_type,
            risk_level=risk_level,
            target=target,
            target_changed=False,
            mode=current_mode,
            entities={},
            requires_approval=False,
            session_id=session_id
        )
