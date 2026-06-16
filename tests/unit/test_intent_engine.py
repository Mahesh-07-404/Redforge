import pytest
from redforge.intent.engine import IntentEngine
from redforge.intent.target_watcher import TargetWatcher
from redforge.session.target import TargetStateMachine
from redforge.session.events import EventBus

def test_intent_engine():
    tm = TargetStateMachine()
    eb = EventBus()
    watcher = TargetWatcher(tm, eb)
    engine = IntentEngine(watcher)
    
    intent = engine.process("scan http://test.com", "bugbounty", "123", "manual")
    assert intent.intent_type.value == "scan"
    assert intent.target == "test.com"
    assert intent.requires_approval is True
