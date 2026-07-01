from __future__ import annotations

import pytest
import os
import asyncio
from unittest.mock import AsyncMock
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
from redforge.distributed.manager import DistributedManager
from redforge.distributed.contracts import TaskStatus
from redforge.observability.manager import ObservabilityManager
from redforge.rag.engine import RAGEngine
from redforge.rag.contracts import RAGQuery
from redforge.reporting import ReportingEngine


@pytest.mark.asyncio
async def test_end_to_end_pipeline(tmp_path) -> None:
    # 1. Observability Manager
    obs = ObservabilityManager(service_name="e2e-test")
    obs.metrics.increment("e2e_start")

    # 2. Session setup
    store = SessionStore(str(tmp_path / "test.db"))
    session_manager = SessionManager(store)
    session = session_manager.create("bugbounty", "test.com", "full")

    # 3. Memory & RAG setup
    memory_manager = MemoryManager(str(tmp_path))
    rag = RAGEngine()

    # 4. Kernel / Engine Pipeline setup
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

    llm_provider = AsyncMock()
    llm_provider.chat.return_value = AsyncMock(content="Executing planned scans on target.")

    pipeline = Pipeline(
        session_manager,
        memory_manager,
        skill_loader,
        intent_engine,
        tool_executor,
        verifier,
        report_engine,
        safety_engine,
        llm_provider,
    )

    # 5. Execute Conversation & Intent stage
    with obs.tracer.span("E2E_Conversation") as span:
        result = await pipeline.process_turn("scan target.com for ports", session.id)
        assert "response" in result
        assert result["intent"].intent_type.value == "scan"

    # 6. Distributed Scheduler & Tool Executor stage
    dist_mgr = DistributedManager(heartbeat_timeout=1.0)
    await dist_mgr.start()
    await dist_mgr.create_local_worker("e2e-worker", capabilities=["all"])

    with obs.tracer.span("E2E_Distributed_Execution"):
        task = await dist_mgr.submit(
            task_id="t-e2e-1",
            session_id=session.id,
            tool="nmap",
            command=["nmap", "test.com"],
        )
        
        # Poll completion
        for _ in range(10):
            await asyncio.sleep(0.1)
            if dist_mgr.get_status("t-e2e-1") == TaskStatus.COMPLETED:
                break
        
        assert dist_mgr.get_status("t-e2e-1") == TaskStatus.COMPLETED

    # 7. Memory RAG Indexing & Retrieval stage
    with obs.tracer.span("E2E_RAG"):
        # Query context
        rag_res = await rag.query(
            rag_query=RAGQuery(session_id=session.id, query_text="port scan"),
            all_chunks=[],
        )
        assert rag_res is not None

    # 8. Reporting Engine compilation
    with obs.tracer.span("E2E_Reporting"):
        report = ReportingEngine.generate_report(
            session_id=session.id,
            execution_id="exec-123",
            target="test.com",
            raw_evidence=[{"tool": "nmap", "output": "ports 80, 443 up"}],
            entities=[],
            world_state_findings=["Vulnerable open port 80 detected"],
        )
        assert report.session_id == session.id
        assert len(report.findings) > 0

    await dist_mgr.stop()
    obs.metrics.increment("e2e_complete")
