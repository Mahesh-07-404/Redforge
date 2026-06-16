from pathlib import Path
from typing import Optional, Dict

from .agent import RedForgeAgent
from .pipeline import Pipeline
from .config import Settings, get_settings
from ..session.manager import SessionManager
from ..session.store import SessionStore
from ..memory.manager import MemoryManager
from ..skills.loader import DynamicSkillLoader
from ..skills.registry import SkillRegistry
from ..intent.engine import IntentEngine
from ..intent.target_watcher import TargetWatcher
from ..session.target import TargetStateMachine
from ..session.events import EventBus
from ..tools.executor import ToolExecutor
from ..verifier.verifier import Verifier
from ..report.engine import ReportEngine
from ..safety import SafetyEngine
from ..llm import get_llm

def create_redforge_agent(
    config: Optional[Settings] = None,
    llm_provider: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    event_handlers: Optional[Dict] = None,
) -> RedForgeAgent:
    """
    Factory function to create a fully configured RedForgeAgent with its Pipeline.
    """
    settings = config or get_settings()
    
    # 1. Session Manager
    store = SessionStore() # defaults to sessions.db
    session_manager = SessionManager(store)
    
    # 2. Memory Manager
    memory_manager = MemoryManager(settings.memory.persist_dir)
    
    # 3. Intent Engine
    target_state = TargetStateMachine()
    event_bus = EventBus()
    target_watcher = TargetWatcher(target_state, event_bus)
    intent_engine = IntentEngine(target_watcher)
    
    # 4. Dynamic Skill Loader
    skill_registry = SkillRegistry()
    skill_loader = DynamicSkillLoader(skill_registry)
    
    # 5. Tools & Verifier
    tool_executor = ToolExecutor()
    verifier = Verifier()
    
    # 6. Report Engine
    report_engine = ReportEngine()
    
    # 7. Safety Engine
    safety_engine = SafetyEngine()
    
    # 8. LLM Provider
    provider = llm_provider or settings.llm.provider
    model_name = model or settings.llm.model
    key = api_key or settings.llm.api_key
    url = base_url or settings.llm.base_url
    
    llm = get_llm(
        provider=provider,
        model=model_name,
        api_key=key,
        base_url=url
    )
    
    # 9. Pipeline
    pipeline = Pipeline(
        session_manager=session_manager,
        memory_manager=memory_manager,
        skill_loader=skill_loader,
        intent_engine=intent_engine,
        tool_executor=tool_executor,
        verifier=verifier,
        report_engine=report_engine,
        safety_engine=safety_engine,
        llm_provider=llm
    )
    
    # 10. Agent
    agent = RedForgeAgent(pipeline)
    if event_handlers:
        for event, callbacks in event_handlers.items():
            for callback in callbacks:
                agent.on(event, callback)
    return agent
