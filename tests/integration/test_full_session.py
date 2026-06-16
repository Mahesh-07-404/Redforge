import pytest
import os
from redforge.core.pipeline import Pipeline
from redforge.session.store import SessionStore
from redforge.session.manager import SessionManager
from redforge.session.target import TargetStateMachine
from redforge.session.events import EventBus
from redforge.intent.engine import IntentEngine
from redforge.intent.target_watcher import TargetWatcher
from redforge.skills.loader import DynamicSkillLoader
from redforge.skills.registry import SkillRegistry
from redforge.memory.manager import MemoryManager
from redforge.tools.executor import ToolExecutor
from redforge.verifier.verifier import Verifier
from redforge.report.engine import ReportEngine

def test_full_session_pipeline(tmp_path):
    store = SessionStore(str(tmp_path / "test.db"))
    session_manager = SessionManager(store)
    
    session = session_manager.create("bugbounty", "test.com", "full")
    
    memory_manager = MemoryManager(str(tmp_path))
    memory_manager.workspace_id = session.id
    
    registry = SkillRegistry()
    skill_loader = DynamicSkillLoader(registry)
    
    tm = TargetStateMachine()
    eb = EventBus()
    watcher = TargetWatcher(tm, eb)
    intent_engine = IntentEngine(watcher)
    
    tool_executor = ToolExecutor()
    verifier = Verifier()
    report_engine = ReportEngine()
    
    pipeline = Pipeline(
        session_manager, memory_manager, skill_loader,
        intent_engine, tool_executor, verifier, report_engine
    )
    
    result = pipeline.process_turn("scan the target", session.id)
    
    assert result["intent"].intent_type.value == "scan"
    assert result["context"] is not None
