"""
RedForge Test Suite
Unit and integration tests
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from redforge.core.safety import SafetyEngine, SafetyLevel, Scope, ScopeEntry
from redforge.tools import ToolManager, ToolRegistry, Platform
from redforge.reports import CVEGenerator, ReportGenerator
from redforge.plugins import PlatformManager, Platform, Submission, create_submission
from redforge.core.agent import RedForgeAgent


# Safety Engine Tests
class TestSafetyEngine:
    """Test safety engine functionality"""
    
    def test_scope_allow(self):
        """Test scope allows matching targets"""
        engine = SafetyEngine()
        engine.scope.add("example.com", "domain")
        
        assert engine.scope.is_allowed("example.com")
        assert engine.scope.is_allowed("www.example.com")
        assert not engine.scope.is_allowed("other.com")
    
    def test_scope_ip_range(self):
        """Test IP range matching"""
        engine = SafetyEngine()
        engine.scope.add("192.168.1.0/24", "ip")
        
        assert engine.scope.is_allowed("192.168.1.1")
        assert engine.scope.is_allowed("192.168.1.100")
        assert not engine.scope.is_allowed("192.168.2.1")
    
    def test_scope_exclusion(self):
        """Test scope exclusions"""
        engine = SafetyEngine()
        engine.scope.add("example.com", "domain")
        engine.scope.exclude("staging.example.com", "subdomain")
        
        assert engine.scope.is_allowed("example.com")
        assert not engine.scope.is_allowed("staging.example.com")
    
    def test_dangerous_command_detection(self):
        """Test dangerous command detection"""
        engine = SafetyEngine()
        
        # Test rm -rf
        violation = engine.check_command("rm -rf /")
        assert violation is not None
        assert violation.blocked
        
        # Test fork bomb
        violation = engine.check_command(":(){ :|:& };:")
        assert violation is not None
        
        # Test safe command
        violation = engine.check_command("ls -la")
        assert violation is None
    
    def test_rate_limiting(self):
        """Test rate limiting"""
        engine = SafetyEngine()
        
        # First 10 requests should pass
        for i in range(10):
            violation = engine.check_rate_limit("test_endpoint", limit=10)
            assert violation is None
        
        # 11th should fail
        violation = engine.check_rate_limit("test_endpoint", limit=10)
        assert violation is not None
    
    def test_pii_detection(self):
        """Test PII detection"""
        engine = SafetyEngine()
        
        data = "User password=secret123 and SSN 123-45-6789"
        violations = engine.check_data_exposure(data)
        
        assert len(violations) > 0
        assert any("SSN" in v.message for v in violations)


# Tool Manager Tests
class TestToolManager:
    """Test tool manager functionality"""
    
    def test_tool_registry(self):
        """Test tool registry"""
        assert ToolRegistry.get_tool("nmap") is not None
        assert ToolRegistry.get_tool("ffuf") is not None
        assert ToolRegistry.get_tool("nonexistent") is None
    
    def test_tool_categories(self):
        """Test tool categories"""
        recon_tools = ToolRegistry.get_tools_by_category("recon")
        assert len(recon_tools) > 0
        assert any(t.name == "nmap" for t in recon_tools)
    
    def test_essential_tools(self):
        """Test essential tools"""
        essential = ToolRegistry.get_essential_tools()
        assert len(essential) > 0
        assert any(t.name == "nmap" for t in essential)


# Agent Tests
class TestRedForgeAgent:
    """Test RedForgeAgent functionality"""

    def test_agent_initialization(self):
        """Test agent initializes correctly"""
        agent = RedForgeAgent()
        assert agent.pipeline is not None
        status = agent.get_status()
        assert "llm_provider" in status
        assert "skills_total" in status



# CVE Generator Tests
class TestCVEGenerator:
    """Test CVE generation"""
    
    def test_cvss_calculation(self):
        """Test CVSS score calculation"""
        generator = CVEGenerator()
        
        impact = {
            "attack_vector": "N",  # Network
            "attack_complexity": "L",  # Low
            "privileges_required": "N",  # None
            "user_interaction": "N",  # None
            "scope": "U",  # Unchanged
            "confidentiality": "H",  # High
            "integrity": "H",  # High
            "availability": "H"  # High
        }
        
        score, vector = generator.calculate_cvss(impact)
        
        assert score > 0
        assert "CVSS:3.1" in vector
    
    def test_cve_generation(self):
        """Test CVE generation from vulnerability"""
        generator = CVEGenerator()
        
        vuln = {
            "type": "sql_injection",
            "description": "SQL injection in login form",
            "product": "Example App",
            "vendor": "Example Corp",
            "cvss": {
                "attack_vector": "N",
                "attack_complexity": "L",
                "privileges_required": "N",
                "user_interaction": "N",
                "scope": "U",
                "confidentiality": "H",
                "integrity": "H",
                "availability": "H"
            }
        }
        
        cve = generator.generate_cve(vuln)
        
        assert cve.cve_id.startswith("RF-")
        assert cve.cwe_id == "CWE-89"  # SQL Injection
        assert cve.severity in ("CRITICAL", "HIGH", "MEDIUM", "LOW")


# Report Generator Tests
class TestReportGenerator:
    """Test report generation"""
    
    def test_markdown_report(self):
        """Test Markdown report generation"""
        generator = ReportGenerator()
        
        data = {
            "title": "Test Report",
            "target": "mytestdomain.com",
            "author": "RedForge",
            "findings": [
                {
                    "title": "SQL Injection",
                    "severity": "high",
                    "description": "Found SQL injection",
                    "impact": "Data breach possible",
                    "steps": ["Step 1", "Step 2"],
                    "remediation": "Use parameterized queries",
                    "cvss_score": 8.5,
                    "cwe_id": "CWE-89"
                }
            ],
            "summary": "Test summary",
            "methodology": "OWASP testing"
        }
        
        report = generator.create_report(data)
        md = generator.generate_markdown()
        
        assert "Test Report" in md
        assert "SQL Injection" in md
        assert "mytestdomain.com" in md
    
    def test_json_report(self):
        """Test JSON report generation"""
        generator = ReportGenerator()
        
        data = {
            "title": "Test Report",
            "target": "mytestdomain.com",
            "author": "RedForge"
        }
        
        generator.create_report(data)
        json_output = generator.generate_json()
        
        assert '"title": "Test Report"' in json_output


# Platform Manager Tests
class TestPlatformManager:
    """Test platform manager"""
    
    def test_platform_manager_creation(self):
        """Test platform manager creation"""
        manager = PlatformManager()
        
        assert len(manager.platforms) == 0
        assert manager.active_platform is None
    
    def test_submission_creation(self):
        """Test submission creation"""
        finding = {
            "title": "XSS Vulnerability",
            "description": "Cross-site scripting in search",
            "type": "xss",
            "severity": "medium",
            "impact": "Session hijacking possible",
            "steps": ["Go to search", "Enter <script>"],
            "poc": "<script>alert(1)</script>",
            "remediation": "Escape user input"
        }
        
        submission = create_submission(finding, "hackerone")
        
        assert submission.title == "XSS Vulnerability"
        assert submission.severity == "medium"
        assert "XSS" in submission.vulnerability_type.upper() or "XSS" in submission.vulnerability_type


# Integration Tests
class TestIntegration:
    """Integration tests"""

    @pytest.mark.asyncio
    async def test_full_workflow(self, tmp_path):
        """Test full agent workflow"""
        from redforge.config.config import get_settings
        from unittest.mock import MagicMock, AsyncMock

        settings = get_settings()
        settings.memory.persist_dir = str(tmp_path)
        settings.session.data_dir = str(tmp_path)

        agent = RedForgeAgent(config=settings)

        # Inject mock LLM provider to avoid calling external services or requiring google-genai
        mock_llm = MagicMock()
        mock_llm.chat = AsyncMock(return_value=MagicMock(content="I will scan the target."))
        mock_llm.supports_streaming = MagicMock(return_value=False)
        agent.pipeline.llm_provider = mock_llm

        # Execute query
        state = await agent.run("scan the target", session_id="test_sess", target="example.com")

        assert state is not None
        assert state.error is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
