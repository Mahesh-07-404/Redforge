import pytest
from unittest.mock import AsyncMock, MagicMock
from redforge.core.state import AgentState, AgentMode, AutonomyLevel
from redforge.core.skill_loader import SkillLoader, Skill
from redforge.core.validator import ResponseValidator
from redforge.core.langgraph_agent import RedForgeAgent

@pytest.fixture
def skill_loader():
    loader = SkillLoader()
    # Mock self._skills
    loader._skills = {
        "SYSTEM/01_persona": Skill(
            name="SYSTEM/01_persona", path="default", content="Persona Content", category="SYSTEM"
        ),
        "SYSTEM/01_prompt": Skill(
            name="SYSTEM/01_prompt", path="default", content="Prompt Content", category="SYSTEM"
        ),
        "SAFETY/01_scope": Skill(
            name="SAFETY/01_scope", path="default", content="Scope Content", category="SAFETY"
        ),
        "SAFETY/06_legal_compliance": Skill(
            name="SAFETY/06_legal_compliance", path="default", content="Legal Content", category="SAFETY"
        ),
        "MODES/BUGBOUNTY/01_scope": Skill(
            name="MODES/BUGBOUNTY/01_scope", path="default", content="Bug Bounty Mode Content", category="MODES", mode="BUGBOUNTY"
        ),
        "MODES/CTF/01_web": Skill(
            name="MODES/CTF/01_web", path="default", content="CTF Mode Content", category="MODES", mode="CTF"
        ),
        "TOOLS/01_recon_tools": Skill(
            name="TOOLS/01_recon_tools", path="default", content="Recon Tools Info", category="TOOLS"
        ),
        "TOOLS/02_web_tools": Skill(
            name="TOOLS/02_web_tools", path="default", content="Web Tools Info", category="TOOLS"
        ),
        "AUTONOMY/GOAL_BASED/02_planning": Skill(
            name="AUTONOMY/GOAL_BASED/02_planning", path="default", content="Planning Flow", category="AUTONOMY", mode="GOAL_BASED"
        ),
        "AUTONOMY/GOAL_BASED/03_execution": Skill(
            name="AUTONOMY/GOAL_BASED/03_execution", path="default", content="Execution Flow", category="AUTONOMY", mode="GOAL_BASED"
        ),
        "AUTONOMY/GOAL_BASED/04_verification": Skill(
            name="AUTONOMY/GOAL_BASED/04_verification", path="default", content="Verification Flow", category="AUTONOMY", mode="GOAL_BASED"
        ),
        "MODES/BUGBOUNTY/16_reporting": Skill(
            name="MODES/BUGBOUNTY/16_reporting", path="default", content="Reporting Flow", category="MODES", mode="BUGBOUNTY"
        )
    }
    loader._loaded = True
    return loader

def test_hierarchical_context_tiers(skill_loader):
    # Test CHAT intent (does NOT load Tier 4 execution skills)
    ctx_chat = skill_loader.get_hierarchical_context(
        active_mode="bugbounty",
        intent="CHAT",
        query="hello teammate"
    )
    
    # Core (Tier 0) and Safety (Tier 1) must be present
    assert "=== TIER 0: CORE SYSTEM ===" in ctx_chat
    assert "Persona Content" in ctx_chat
    assert "Prompt Content" in ctx_chat
    assert "=== TIER 1: SAFETY ===" in ctx_chat
    assert "Scope Content" in ctx_chat
    
    # Active mode (Tier 2) must be present
    assert "=== TIER 2: ACTIVE MODE (BUGBOUNTY) ===" in ctx_chat
    assert "Bug Bounty Mode Content" in ctx_chat
    # Inactive mode must NOT be present
    assert "CTF Mode Content" not in ctx_chat

    # Required Tools (Tier 3) - query has no keywords, so no tools loaded for CHAT
    assert "=== TIER 3: REQUIRED TOOLS ===" in ctx_chat
    assert "Recon Tools Info" not in ctx_chat
    
    # Tier 4 Execution must NOT be present for CHAT
    assert "=== TIER 4: EXECUTION ===" not in ctx_chat

def test_hierarchical_context_tool_matching(skill_loader):
    # Test tool keywords trigger loading of tools
    ctx_tool = skill_loader.get_hierarchical_context(
        active_mode="bugbounty",
        intent="SCAN",
        query="run subdomain recon and look for certs"
    )
    # Should load tools matching "subdomain", "recon", "cert" -> 01_recon_tools
    assert "Recon Tools Info" in ctx_tool
    assert "Web Tools Info" not in ctx_tool

def test_hierarchical_context_default_tools_for_scan(skill_loader):
    # Test scan/recon intent loads default tools when no keywords match
    ctx_default = skill_loader.get_hierarchical_context(
        active_mode="bugbounty",
        intent="SCAN",
        query="do some testing"
    )
    # Should load default tools (01_recon_tools, etc.)
    assert "Recon Tools Info" in ctx_default

def test_hierarchical_context_tier4_execution(skill_loader):
    # Test SCAN intent (loads Tier 4 execution skills in order)
    ctx_scan = skill_loader.get_hierarchical_context(
        active_mode="bugbounty",
        intent="SCAN",
        query="test scope"
    )
    assert "=== TIER 4: EXECUTION ===" in ctx_scan
    assert "Planning Flow" in ctx_scan
    assert "Execution Flow" in ctx_scan
    assert "Verification Flow" in ctx_scan
    assert "Reporting Flow" in ctx_scan
    
    # Check strict order of execution skills
    idx_plan = ctx_scan.find("02_planning")
    idx_exec = ctx_scan.find("03_execution")
    idx_verify = ctx_scan.find("04_verification")
    idx_report = ctx_scan.find("16_reporting")
    assert idx_plan < idx_exec < idx_verify < idx_report

def test_response_validator_intent_bypass():
    validator = ResponseValidator(target="myserver.com")
    
    # 1. Operational intent: Target mismatch or placeholder should be rejected
    is_valid, reason = validator.validate("Scanning example.com and test.com", intent="SCAN")
    assert not is_valid
    assert "Target consistency failure" in reason or "Target mismatch" in reason

    # 2. Conversational/Learning intent: Target mismatch or placeholder should be allowed
    is_valid_chat, _ = validator.validate("Sure! Here is a script pointing to localhost and example.com", intent="CHAT")
    assert is_valid_chat
    
    is_valid_code, _ = validator.validate("Let's debug the code for localhost on example.com", intent="CODING")
    assert is_valid_code
    
    # 3. Simulated output should STILL be blocked even in conversational intent to prevent hallucinations
    is_valid_fake, reason_fake = validator.validate("OUTPUT [✓ bash] exit: 0 time: 0.1s\nhello", intent="CHAT")
    assert not is_valid_fake
    assert "Hallucination detected" in reason_fake

@pytest.mark.asyncio
async def test_agent_intent_classification():
    # Setup dummy agent config/llm
    mock_llm = MagicMock()
    mock_llm.chat = AsyncMock(return_value=MagicMock(content="SCAN"))
    
    agent = RedForgeAgent(llm_provider="gemini")
    agent.llm = mock_llm
    
    # Instant heuristic classification for greetings
    intent_greet = await agent._classify_intent("Yo bro, how are you?")
    assert intent_greet == "CHAT"
    
    intent_thanks = await agent._classify_intent("thanks")
    assert intent_thanks == "CHAT"
    
    # LLM fallback classification
    intent_llm = await agent._classify_intent("run an nmap scan on the target site")
    assert intent_llm == "SCAN"
    mock_llm.chat.assert_called_once()


def test_real_skills_loading():
    # Test that the loader correctly parses categories and modes from the actual file structure
    loader = SkillLoader()
    loader.load_skills()
    
    assert loader.is_loaded()
    skills = loader.list_skills()
    assert len(skills) > 0
    
    # Check that categories are correctly extracted
    system_skills = [s for s in skills if s.category == "SYSTEM"]
    safety_skills = [s for s in skills if s.category == "SAFETY"]
    modes_skills = [s for s in skills if s.category == "MODES"]
    tools_skills = [s for s in skills if s.category == "TOOLS"]
    execution_skills = [s for s in skills if s.category == "EXECUTION"]
    
    assert len(system_skills) > 0
    assert len(safety_skills) > 0
    assert len(modes_skills) > 0
    assert len(tools_skills) > 0
    assert len(execution_skills) > 0
    
    # Verify that MODES files (bugbounty, ctf, learning, coding, android)
    # direct children of skills/MODES/ have their mode attribute set correctly
    bugbounty_skill = next((s for s in modes_skills if "bugbounty" in s.name.lower()), None)
    assert bugbounty_skill is not None
    assert bugbounty_skill.mode == "BUGBOUNTY"
    
    ctf_skill = next((s for s in modes_skills if "ctf" in s.name.lower()), None)
    assert ctf_skill is not None
    assert ctf_skill.mode == "CTF"
    
    # Test hierarchical context compilation from disk
    ctx = loader.get_hierarchical_context(
        active_mode="bugbounty",
        intent="SCAN",
        query="run nmap scan on target"
    )
    
    assert "=== TIER 0: CORE SYSTEM ===" in ctx
    assert "=== TIER 1: SAFETY ===" in ctx
    assert "=== TIER 2: ACTIVE MODE (BUGBOUNTY) ===" in ctx
    assert "=== TIER 3: REQUIRED TOOLS ===" in ctx
    assert "=== TIER 4: EXECUTION ===" in ctx
    
    # Verify nmap tool or network tools are included due to SCAN intent and query
    assert any(x in ctx for x in ("nmap", "network", "TOOL"))
