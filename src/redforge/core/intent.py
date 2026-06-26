"""Intent analysis service for RedForge."""

import re
from typing import Optional, Dict, Any
from ..contracts.intent import ParsedIntent, IntentType, RiskLevel
from .session import TargetStateMachine
from .session import EventBus

class IntentParser:
    """Parses user input to extract intent type, risk, and target."""
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


class IntentClassifier:
    """Classifies intent types into risk levels."""
    def classify(self, intent_type: IntentType) -> RiskLevel:
        mapping = {
            IntentType.SCAN: RiskLevel.MEDIUM,
            IntentType.RECON: RiskLevel.LOW,
            IntentType.EXPLOIT: RiskLevel.HIGH,
            IntentType.REPORT: RiskLevel.SAFE,
            IntentType.LEARN: RiskLevel.SAFE,
            IntentType.CONFIGURE: RiskLevel.LOW,
            IntentType.CLARIFY: RiskLevel.SAFE,
            IntentType.UNKNOWN: RiskLevel.SAFE,
        }
        return mapping.get(intent_type, RiskLevel.SAFE)


class TargetWatcher:
    """Monitors if target changes during execution."""
    def __init__(self, state_machine: TargetStateMachine, event_bus: EventBus):
        self.state_machine = state_machine
        self.event_bus = event_bus

    def check(self, intent: ParsedIntent) -> ParsedIntent:
        current_state = self.state_machine.get()
        if intent.target and (current_state.target != intent.target):
            intent.target_changed = True
            self.state_machine.set(intent.target)
        return intent


class IntentService:
    """Service to process user inputs and extract security intent."""
    def __init__(self, target_watcher: TargetWatcher):
        self.parser = IntentParser()
        self.classifier = IntentClassifier()
        self.watcher = target_watcher

    def process(self, raw_input: str, current_mode: str, session_id: str, current_autonomy: str) -> ParsedIntent:
        intent = self.parser.parse(raw_input, current_mode, session_id)
        intent.risk_level = self.classifier.classify(intent.intent_type)
        intent = self.watcher.check(intent)
        
        if current_autonomy == "manual":
            intent.requires_approval = True
        elif current_autonomy == "partial" and intent.risk_level in ["high", "destructive"]:
            intent.requires_approval = True
        else:
            intent.requires_approval = False
            
        return intent
