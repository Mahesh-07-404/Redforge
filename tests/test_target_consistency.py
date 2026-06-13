"""Unit tests for target consistency and anti-hallucination features"""

import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from redforge.core.state import AgentState, create_initial_state
from redforge.core.langgraph_agent import RedForgeAgent
from redforge.core.validator import ResponseValidator
from redforge.advanced import ReportGenerator
from redforge.llm.base import Message


class TestResponseValidator:
    """Test ResponseValidator middleware logic"""

    def test_domain_extraction(self):
        validator = ResponseValidator()
        text = "Scan target.com and check google.com and sub.domain.org."
        domains = validator.extract_domains(text)
        assert "target.com" in domains
        assert "google.com" in domains
        assert "sub.domain.org" in domains

    def test_placeholder_prohibition(self):
        # Setting target to a different host
        validator = ResponseValidator(target="myrealtestsite.com")
        
        # Test placeholder url is rejected
        is_valid, reason = validator.validate("Check results on http://example.com/login")
        assert not is_valid
        assert "example.com" in reason

        # Test localhost is rejected
        is_valid, reason = validator.validate("Try testing localhost")
        assert not is_valid
        assert "localhost" in reason

        # Test 127.0.0.1 is rejected
        is_valid, reason = validator.validate("Try testing 127.0.0.1")
        assert not is_valid
        assert "127.0.0.1" in reason

        # Test that active target matching placeholder is allowed
        validator_ph = ResponseValidator(target="localhost")
        is_valid, reason = validator_ph.validate("I am checking localhost ports")
        assert is_valid

    def test_target_mismatch(self):
        validator = ResponseValidator(target="felinelube.vercel.app")
        
        # Matches subdomains
        is_valid, reason = validator.validate("The host is sub.felinelube.vercel.app")
        assert is_valid

        # Matches benign tools domains
        is_valid, reason = validator.validate("Run nmap.org or read python.org docs")
        assert is_valid

        # Reject entirely different unknown target
        is_valid, reason = validator.validate("I will scan othertargetsite.com for XSS")
        assert not is_valid
        assert "othertargetsite.com" in reason

    def test_hallucinated_tool_output(self):
        validator = ResponseValidator(target="felinelube.vercel.app")

        # LLM simulating tool OUTPUT header
        is_valid, reason = validator.validate("OUTPUT [✓ nmap] (Exit: 0)\nSome scan results")
        assert not is_valid
        assert "OUTPUT" in reason or "simulated" in reason

        # Fictional output keywords
        is_valid, reason = validator.validate("This is simulated output of the test exploit.")
        assert not is_valid
        assert "simulated output" in reason


class TestTargetImmutability:
    """Test target immutability checks in AgentState and LangGraph agent"""

    def test_merge_state_target_immutability(self):
        agent = RedForgeAgent()
        state = create_initial_state(user_input="test", target="original.com")
        
        # Valid merge updates target with same target
        updated = agent._merge_state(state, {"target": "original.com"})
        assert updated.target == "original.com"

        # Invalid merge with different target raises ValueError
        with pytest.raises(ValueError) as exc:
            agent._merge_state(state, {"target": "mismatch.com"})
        assert "Target immutability violation" in str(exc.value)


class TestFindingsVerification:
    """Test that findings are marked correctly with status based on evidence"""

    @pytest.mark.asyncio
    async def test_findings_validation(self):
        agent = RedForgeAgent()
        state = create_initial_state(user_input="test", target="mytarget.com")
        state.messages.append({
            "role": "tool",
            "content": "Port 80 is open"
        })
        
        # Simulate last result with stdout (evidence)
        mock_result = MagicMock()
        mock_result.tool = "nmap"
        mock_result.command = "nmap mytarget.com"
        mock_result.stdout = "Port 80 is open"
        mock_result.stderr = ""
        mock_result.returncode = 0
        agent.tool_executor._history.append(mock_result)

        # Mock LLM to return a finding
        with patch.object(agent, "_generate_validated_response", AsyncMock(return_value=(
            "FINDING: open_port | SEVERITY: medium | Port 80 open on mytarget.com", 10
        ))):
            updated_state = await agent.verify_node(state)
            assert len(updated_state["findings"]) == 1
            finding = updated_state["findings"][0]
            assert finding["target"] == "mytarget.com"
            assert finding["tool"] == "nmap"
            assert finding["command"] == "nmap mytarget.com"
            assert finding["status"] == "VERIFIED"
            assert finding["evidence"]["stdout"] == "Port 80 is open"

    @pytest.mark.asyncio
    async def test_findings_without_evidence_unverified(self):
        agent = RedForgeAgent()
        state = create_initial_state(user_input="test", target="mytarget.com")
        state.messages.append({
            "role": "tool",
            "content": "Port 80 is open"
        })
        
        # Clear tool executor history
        agent.tool_executor.clear_history()

        with patch.object(agent, "_generate_validated_response", AsyncMock(return_value=(
            "FINDING: open_port | SEVERITY: medium | Port 80 open on mytarget.com", 10
        ))):
            updated_state = await agent.verify_node(state)
            assert len(updated_state["findings"]) == 1
            finding = updated_state["findings"][0]
            assert finding["status"] == "UNVERIFIED"
            assert finding["evidence"] is None


class TestReportValidation:
    """Test report target validation"""

    def test_report_generator_mismatch(self):
        rg = ReportGenerator()
        
        # Allowed target matching
        report = rg.create_report({"target": "real.com"}, session_target="real.com")
        assert report.target == "real.com"

        # Raise error on target mismatch
        with pytest.raises(ValueError) as exc:
            rg.create_report({"target": "mismatch.com"}, session_target="real.com")
        assert "does not match session target" in str(exc.value)

        # Raise error on placeholder targets when session target is not set
        with pytest.raises(ValueError) as exc:
            rg.create_report({"target": "example.com"})
        assert "forbidden placeholder" in str(exc.value)
