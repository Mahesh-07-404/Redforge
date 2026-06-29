import pytest
import os
from redforge.core.pipeline import Pipeline
from redforge.core.session import SessionStore, SessionManager, TargetStateMachine, EventBus
from redforge.core.intent import IntentService as IntentEngine, TargetWatcher
from redforge.skills.loader import DynamicSkillLoader
from redforge.skills.registry import SkillRegistry
from redforge.memory.manager import MemoryManager
from redforge.tools.executor import ToolExecutor
from redforge.core.verifier import Verifier
from redforge.reports.engine import ReportEngine
from redforge.core.safety import SafetyEngine
from redforge.providers import get_llm

@pytest.mark.asyncio
async def test_full_session_pipeline(tmp_path):
    store = SessionStore(str(tmp_path / "test.db"))
    session_manager = SessionManager(store)
    
    session = session_manager.create("bugbounty", "test.com", "full")
    
    memory_manager = MemoryManager(str(tmp_path))
    
    registry = SkillRegistry()
    skill_loader = DynamicSkillLoader(registry)
    
    tm = TargetStateMachine()
    eb = EventBus()
    watcher = TargetWatcher(tm, eb)
    intent_engine = IntentEngine(watcher)
    
    tool_executor = ToolExecutor()
    verifier = Verifier()
    report_engine = ReportEngine()
    safety_engine = SafetyEngine()
    
    # Mock LLM for test
    from unittest.mock import AsyncMock
    llm_provider = AsyncMock()
    llm_provider.chat.return_value = AsyncMock(content="I will scan the target.")
    
    pipeline = Pipeline(
        session_manager, memory_manager, skill_loader,
        intent_engine, tool_executor, verifier, report_engine,
        safety_engine, llm_provider
    )
    
    result = await pipeline.process_turn("scan the target", session.id)
    
    assert result["intent"].intent_type.value == "scan"
    assert "response" in result
