"""Unit tests for RedForge V2 Architecture components"""

import pytest
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from redforge.core.intent import IntentEngine
from redforge.core.planner import Planner
from redforge.core.verifier import Verifier
from redforge.skills.registry import SkillRegistry
from redforge.skills.loader import DynamicSkillLoader
from redforge.memory.memory_manager import MemoryManager
from redforge.memory.session_manager import SessionManager
from redforge.tools.executor import ToolExecutor
from redforge.reports.generator import ReportGenerator


@pytest.mark.asyncio
async def test_intent_engine():
    # Greeting heuristics
    assert await IntentEngine.classify("Yo bro, how is it going?") == "CHAT"
    assert await IntentEngine.classify("thanks!") == "CHAT"
    
    # Mock SequencedLLM check
    mock_llm = MagicMock()
    mock_llm.__class__.__name__ = "SequencedLLM"
    assert await IntentEngine.classify("run an nmap scan on the host", llm=mock_llm) == "SCAN"


@pytest.mark.asyncio
async def test_planner():
    mock_llm = MagicMock()
    mock_llm.chat = AsyncMock(return_value=MagicMock(content="Step 1: Scan target\nStep 2: Verify port"))
    
    plan = await Planner.generate_plan("Scan host", {"target": "real.com"}, mock_llm)
    assert "Step 1" in plan
    assert "Step 2" in plan
    mock_llm.chat.assert_called_once()


def test_verifier_response_and_findings():
    verifier = Verifier(target="testtarget.com")
    
    # Extract domains
    domains = verifier.extract_domains("Test domain.org and host.com")
    assert "domain.org" in domains
    assert "host.com" in domains

    # Reject placeholder
    is_valid, reason = verifier.validate_response("Let's query example.com for data", intent="SCAN")
    assert not is_valid
    assert "example.com" in reason

    # Reject target mismatch
    is_valid, reason = verifier.validate_response("I will attack otherdomain.com", intent="SCAN")
    assert not is_valid
    assert "otherdomain.com" in reason

    # Accept benign technical domains
    is_valid, _ = verifier.validate_response("Check security details on nmap.org", intent="SCAN")
    assert is_valid

    # Verify findings check - "no evidence = no finding"
    finding = {"title": "XSS vulnerability", "description": "Verified cross-site scripting"}
    assert verifier.verify_finding(finding, "Alert box popped up with script tag")
    assert not verifier.verify_finding(finding, "Port 80 is open but no script executed")


def test_registry_and_loader(tmp_path):
    # Setup mock skills folder
    skills_dir = tmp_path / "skills"
    system_dir = skills_dir / "SYSTEM"
    system_dir.mkdir(parents=True)
    
    p_file = system_dir / "personality.md"
    p_file.write_text("---\npriority: 10\ntags: system, core\n---\nRedForge personality prompt", encoding="utf-8")
    
    registry = SkillRegistry(skills_dir=str(skills_dir))
    registry.load_registry()
    
    skills = registry.list_skills()
    assert len(skills) == 1
    assert skills[0].name == "SYSTEM/personality"
    assert skills[0].priority == 10
    
    loader = DynamicSkillLoader(registry)
    selected = loader.select_skills(intent="CHAT", active_mode="bugbounty", query="hello")
    assert len(selected) == 1
    assert selected[0].name == "SYSTEM/personality"
    
    ctx = loader.build_context(selected)
    assert "=== TIER 0: CORE SYSTEM ===" in ctx


def test_sqlite_memory_and_sessions(tmp_path):
    db_file = tmp_path / "test_redforge.db"
    mm = MemoryManager(db_path=str(db_file))
    
    # Save target
    mm.add_target("myserver.org", "Staging system")
    targets = mm.get_targets()
    assert len(targets) == 1
    assert targets[0]["host"] == "myserver.org"

    # Save findings
    finding = {
        "id": "find_1",
        "title": "SQLi discovered",
        "severity": "critical",
        "category": "web",
        "description": "SQL injection on parameter ID",
        "target": "myserver.org",
        "evidence": {"stdout": "SQL Syntax Error"},
        "status": "VERIFIED",
        "timestamp": "2026-06-14"
    }
    mm.add_finding(finding)
    
    findings = mm.get_findings()
    assert len(findings) == 1
    assert findings[0]["title"] == "SQLi discovered"

    # Save note
    mm.add_note("Checked index page")
    assert mm.get_notes() == ["Checked index page"]

    # Session management
    sm = SessionManager(mm)
    session_state = {
        "target": "myserver.org",
        "findings": findings,
        "notes": ["Checked index page"]
    }
    sm.save_session("session_alpha", session_state)
    
    sessions = sm.list_sessions()
    assert len(sessions) == 1
    assert sessions[0]["name"] == "session_alpha"
    
    loaded = sm.load_session("session_alpha")
    assert loaded["target"] == "myserver.org"

    # Command handler
    out = sm.handle_command("/session list")
    assert "session_alpha" in out
    
    out = sm.handle_command("/session delete session_alpha")
    assert "deleted successfully" in out
    assert len(sm.list_sessions()) == 0


def test_tool_executor():
    executor = ToolExecutor()
    res = executor.execute("echo", "echo 'V2 Rebuild works'")
    assert res.success
    assert res.returncode == 0
    assert "V2 Rebuild works" in res.stdout


def test_report_generator():
    findings = [
        {
            "title": "SQLi discovered",
            "severity": "critical",
            "category": "web",
            "status": "VERIFIED",
            "description": "Evidence exists",
            "evidence": {"stdout": "syntax error"}
        },
        {
            "title": "Fake injection",
            "severity": "high",
            "category": "web",
            "status": "UNVERIFIED",
            "description": "Fake findings",
            "evidence": None
        }
    ]
    
    report_md = ReportGenerator.generate_report(findings, "real.com", format_type="md")
    # Verify that ONLY the verified finding is included
    assert "SQLi discovered" in report_md
    assert "Fake injection" not in report_md

    report_json = ReportGenerator.generate_report(findings, "real.com", format_type="json")
    parsed = json.loads(report_json)
    assert len(parsed["findings"]) == 1
    assert parsed["findings"][0]["title"] == "SQLi discovered"


@pytest.mark.asyncio
async def test_agent_approval_routing():
    from redforge.core.langgraph_agent import RedForgeAgent
    from redforge.core.state import AgentState
    
    agent = RedForgeAgent()
    
    # Mock planning, execution, verification nodes to track routing
    agent.plan_node = AsyncMock(return_value={"messages": []})
    agent.execute_node = AsyncMock(return_value={"messages": [], "workflow_phase": "verify"})
    agent.verify_node = AsyncMock(return_value={"messages": [], "workflow_phase": "store"})
    agent.store_node = AsyncMock(return_value={"messages": []})
    agent.report_node = AsyncMock(return_value={"messages": []})
    
    prior_state = AgentState(
        messages=[
            {"role": "assistant", "content": "TOOL: nmap\nTARGET: target.com\nFLAGS: -F"}
        ],
        target="target.com"
    )
    
    await agent.run(
        user_input="[APPROVED] Execute the planned action.",
        target="target.com",
        prior_state=prior_state
    )
    
    # Assert plan_node was NOT called, but execute_node WAS called
    agent.plan_node.assert_not_called()
    agent.execute_node.assert_called_once()
