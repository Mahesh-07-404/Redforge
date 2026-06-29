import pytest
from unittest.mock import MagicMock, AsyncMock
from redforge.contracts.intent import ParsedIntent, IntentType
from redforge.contracts.session import Session, SessionMode
from redforge.planner.planner_context import PlannerContext
from redforge.planner.task import Task
from redforge.planner.task_graph import TaskGraph
from redforge.planner.plan import Plan
from redforge.planner.planner import Planner
from redforge.planner.validators import PlannerValidator
from redforge.planner.strategy import (
    PassiveReconStrategy, WebEnumerationStrategy,
    BugBountyStrategy, CTFStrategy, LearningStrategy, ReportStrategy
)

def test_planner_creation():
    planner = Planner()
    assert len(planner.strategies) >= 6
    assert isinstance(planner.validator, PlannerValidator)

def test_task_graph_generation_and_dependency_ordering():
    graph = TaskGraph()
    t1 = Task(id="t1", title="Task 1", description="First")
    t2 = Task(id="t2", title="Task 2", description="Second", dependencies=["t1"])
    t3 = Task(id="t3", title="Task 3", description="Third", dependencies=["t2"])
    
    graph.add_task(t3)
    graph.add_task(t2)
    graph.add_task(t1)
    
    ordered = graph.get_ordered_tasks()
    assert len(ordered) == 3
    assert ordered[0].id == "t1"
    assert ordered[1].id == "t2"
    assert ordered[2].id == "t3"

def test_task_graph_cycle_detection():
    graph = TaskGraph()
    t1 = Task(id="t1", title="Task 1", description="First", dependencies=["t2"])
    t2 = Task(id="t2", title="Task 2", description="Second", dependencies=["t1"])
    
    graph.add_task(t1)
    graph.add_task(t2)
    
    with pytest.raises(ValueError) as excinfo:
        graph.get_ordered_tasks()
    assert "Cycle detected" in str(excinfo.value)

def test_planner_validator():
    validator = PlannerValidator()
    
    # 1. Missing session
    ctx_no_session = PlannerContext(active_session=None, intent=ParsedIntent(
        raw_input="test", intent_type=IntentType.GENERAL_CHAT,
        risk_level="safe", target=None, target_changed=False,
        mode="chat", requires_approval=False, session_id="1"
    ))
    errors = validator.validate(ctx_no_session)
    assert any("Active session is missing" in e for e in errors)
    
    # 2. Missing target for security intent
    from datetime import datetime, timezone
    session = Session(
        id="1", mode="bugbounty", target=None, autonomy="manual", status="active", metadata={},
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
    )
    ctx_security_no_target = PlannerContext(
        active_session=session,
        intent=ParsedIntent(
            raw_input="scan", intent_type=IntentType.SCAN,
            risk_level="safe", target=None, target_changed=False,
            mode="chat", requires_approval=False, session_id="1"
        ),
        target=None
    )
    errors = validator.validate(ctx_security_no_target)
    assert any("Target is required for security tasks" in e for e in errors)
    
    # 3. Valid context for general chat (target-free)
    ctx_general = PlannerContext(
        active_session=session,
        intent=ParsedIntent(
            raw_input="hi", intent_type=IntentType.GENERAL_CHAT,
            risk_level="safe", target=None, target_changed=False,
            mode="chat", requires_approval=False, session_id="1"
        ),
        target=None
    )
    errors = validator.validate(ctx_general)
    assert not errors

def test_strategy_selection():
    planner = Planner()
    from datetime import datetime, timezone
    session = Session(
        id="1", mode="bugbounty", target="example.com", autonomy="manual", status="active", metadata={},
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
    )
    
    # Passive Recon
    ctx_recon = PlannerContext(
        active_session=session,
        intent=ParsedIntent(
            raw_input="Perform passive recon on example.com", intent_type=IntentType.RECON,
            risk_level="safe", target="example.com", target_changed=False,
            mode="chat", requires_approval=False, session_id="1"
        ),
        target="example.com"
    )
    plan = planner.create_plan(ctx_recon)
    assert plan.goal == "Perform passive recon on example.com"
    assert len(plan.ordered_tasks) == 7
    assert plan.ordered_tasks[0].id in ("dns", "whois", "subfinder")
    
    # Bug Bounty
    ctx_bb = PlannerContext(
        active_session=session,
        intent=ParsedIntent(
            raw_input="Generate bug bounty workflow", intent_type=IntentType.BUG_BOUNTY,
            risk_level="safe", target="example.com", target_changed=False,
            mode="chat", requires_approval=False, session_id="1"
        ),
        target="example.com"
    )
    plan_bb = planner.create_plan(ctx_bb)
    assert "bug bounty" in plan_bb.goal.lower()
    
    # Learning
    ctx_learn = PlannerContext(
        active_session=session,
        intent=ParsedIntent(
            raw_input="Explain SQL Injection", intent_type=IntentType.LEARNING,
            risk_level="safe", target=None, target_changed=False,
            mode="chat", requires_approval=False, session_id="1"
        ),
        target=None
    )
    plan_learn = planner.create_plan(ctx_learn)
    assert "Explain SQL Injection" in plan_learn.goal

@pytest.mark.asyncio
async def test_conversation_bypass_integration(tmp_path):
    # If the user says "Hi", it should NOT activate the planner.
    from redforge.core.pipeline import Pipeline
    from redforge.core.session import SessionService, SessionStore
    from redforge.core.intent import IntentService, TargetWatcher
    from redforge.core.session import TargetStateMachine, EventBus
    from redforge.providers.base import ChatResponse
    from redforge.memory.manager import MemoryManager
    
    db_path = str(tmp_path / "sessions.db")
    store = SessionStore(db_path)
    session_service = SessionService(store)
    session = session_service.create(mode="bugbounty", target=None, autonomy="manual")
    
    llm = AsyncMock()
    llm.chat.return_value = ChatResponse(content="Hello user!", model="mock")
    llm.supports_streaming.return_value = False
    
    tm = TargetStateMachine()
    eb = EventBus()
    watcher = TargetWatcher(tm, eb)
    intent_engine = IntentService(watcher)
    
    pipeline = Pipeline(
        session_manager=session_service,
        memory_manager=MemoryManager(str(tmp_path)),
        skill_loader=MagicMock(),
        intent_engine=intent_engine,
        tool_executor=MagicMock(),
        verifier=MagicMock(),
        report_engine=MagicMock(),
        safety_engine=MagicMock(**{"check_target.return_value": None}),
        llm_provider=llm
    )
    
    # Process "hello" (triggers conversation routing, bypasses planner)
    res = await pipeline.process_turn("hello", session.id)
    assert "Hello" in res["response"]
    assert res["intent"].intent_type == IntentType.GENERAL_CHAT
    
    # Process "Perform passive recon on example.com" (triggers planner)
    res_plan = await pipeline.process_turn("Perform passive recon on example.com", session.id)
    assert "### Execution Plan" in res_plan["response"]
    assert "Resolve DNS" in res_plan["response"]
    assert res_plan["intent"].intent_type == IntentType.RECON
