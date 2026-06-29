import pytest
from unittest.mock import AsyncMock, MagicMock
from redforge.contracts.intent import IntentType, ParsedIntent
from redforge.contracts.conversation import ConversationContext
from redforge.core.intent import IntentParser, IntentService, TargetWatcher
from redforge.core.session import SessionStore, SessionService, TargetStateMachine, EventBus
from redforge.core.conversation import ConversationManager
from redforge.core.router import IntentRouter
from redforge.providers.base import Message, ChatResponse

def test_intent_classification():
    parser = IntentParser()
    
    # General chat
    intent = parser.parse("Hello, how are you?", "chat", "session123")
    assert intent.intent_type == IntentType.GENERAL_CHAT
    
    # Session management
    intent = parser.parse("continue yesterday's session", "chat", "session123")
    assert intent.intent_type == IntentType.SESSION
    
    # Report management
    intent = parser.parse("generate report for findings", "chat", "session123")
    assert intent.intent_type == IntentType.REPORT
    
    # Bug bounty
    intent = parser.parse("start bug bounty test", "chat", "session123")
    assert intent.intent_type == IntentType.BUG_BOUNTY
    
    # Pentest
    intent = parser.parse("perform penetration testing", "chat", "session123")
    assert intent.intent_type == IntentType.PENTEST
    
    # CTF
    intent = parser.parse("solve CTF challenge", "chat", "session123")
    assert intent.intent_type == IntentType.CTF

def test_target_extraction():
    parser = IntentParser()
    
    intent = parser.parse("scan example.com", "bugbounty", "session123")
    assert intent.target == "example.com"
    
    intent = parser.parse("test http://vulnerable-site.org/index.html", "bugbounty", "session123")
    assert intent.target == "vulnerable-site.org"

@pytest.mark.asyncio
async def test_general_conversation():
    # Mock LLM provider
    from unittest.mock import MagicMock
    llm = AsyncMock()
    llm.chat.return_value = ChatResponse(content="I'm doing great, how can I help you?", model="mock")
    llm.supports_streaming = MagicMock(return_value=False)
    
    conv_mgr = ConversationManager(llm)
    context = ConversationContext()
    
    # Greeting
    greeting = await conv_mgr.get_response("hi", context)
    assert "Hello" in greeting
    
    # Natural conversation (goes to LLM)
    reply = await conv_mgr.get_response("tell me a joke", context)
    assert reply == "I'm doing great, how can I help you?"
    llm.chat.assert_called_once()

@pytest.mark.asyncio
async def test_conversation_routing(tmp_path):
    db_path = str(tmp_path / "sessions.db")
    store = SessionStore(db_path)
    session_service = SessionService(store)
    
    # Setup mocks
    conv_mgr = AsyncMock()
    conv_mgr.get_response.return_value = "casual reply"
    report_engine = MagicMock()
    
    router = IntentRouter(
        conversation_mgr=conv_mgr,
        session_service=session_service,
        report_engine=report_engine
    )
    
    # Setup context
    session = session_service.create(mode="bugbounty", target=None, autonomy="manual")
    context = ConversationContext(active_session=session)
    
    # Route GENERAL_CHAT
    intent_chat = ParsedIntent(
        raw_input="hello", intent_type=IntentType.GENERAL_CHAT,
        risk_level="safe", target=None, target_changed=False,
        mode="chat", requires_approval=False, session_id=session.id
    )
    res = await router.route(intent_chat, context)
    assert res == "casual reply"
    conv_mgr.get_response.assert_called_once()
    
    # Route SESSION (load last session)
    intent_session = ParsedIntent(
        raw_input="continue yesterday's session", intent_type=IntentType.SESSION,
        risk_level="safe", target=None, target_changed=False,
        mode="chat", requires_approval=False, session_id=session.id
    )
    res = await router.route(intent_session, context)
    assert "loaded successfully" in res
    assert context.active_session.id == session.id

@pytest.mark.asyncio
async def test_session_integration_and_follow_up(tmp_path):
    db_path = str(tmp_path / "sessions.db")
    store = SessionStore(db_path)
    session_service = SessionService(store)
    
    session = session_service.create(mode="bugbounty", target=None, autonomy="manual")
    
    # Follow-up conversational context stored inside session metadata
    from redforge.core.pipeline import Pipeline
    from redforge.core.intent import IntentService
    from redforge.memory.manager import MemoryManager
    
    # Minimal mocks for pipeline
    from unittest.mock import MagicMock
    llm = AsyncMock()
    llm.chat.return_value = ChatResponse(content="How can I assist you with your testing?", model="mock")
    llm.supports_streaming = MagicMock(return_value=False)
    
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
        safety_engine=MagicMock(),
        llm_provider=llm
    )
    
    # First turn: Greeting
    res1 = await pipeline.process_turn("hello", session.id)
    assert "Hello" in res1["response"]
    
    # Load session and check metadata
    loaded = session_service.load(session.id)
    assert len(loaded.metadata["previous_messages"]) == 2
    assert loaded.metadata["previous_messages"][0]["content"] == "hello"
    
    # Second turn: Follow up
    res2 = await pipeline.process_turn("How are you?", session.id)
    assert "functioning" in res2["response"].lower() or "assist" in res2["response"].lower()
    
    loaded2 = session_service.load(session.id)
    assert len(loaded2.metadata["previous_messages"]) == 4
    assert loaded2.metadata["previous_messages"][2]["content"] == "How are you?"
