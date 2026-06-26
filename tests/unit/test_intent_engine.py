import pytest
from redforge.core.intent import IntentService as IntentEngine, TargetWatcher
from redforge.core.session import TargetStateMachine, EventBus

def test_intent_engine():
    tm = TargetStateMachine()
    eb = EventBus()
    watcher = TargetWatcher(tm, eb)
    engine = IntentEngine(watcher)
    
    intent = engine.process("scan http://test.com", "bugbounty", "123", "manual")
    assert intent.intent_type.value == "scan"
    assert intent.target == "test.com"
    assert intent.requires_approval is True
