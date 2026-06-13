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

from redforge.safety import SafetyEngine, SafetyLevel, Scope, ScopeEntry
from redforge.tools import ToolManager, ToolRegistry, Platform
from redforge.modes.mode_implementations import (
    BugBountyMode, CTFMode, LearningMode, ModeFactory, Mode, ModeConfig
)
from redforge.advanced import CVEGenerator, ReportGenerator
from redforge.platforms import PlatformManager, Platform, Submission, create_submission


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


# Mode Tests
class TestModes:
    """Test mode implementations"""
    
    def test_mode_factory(self):
        """Test mode factory"""
        bugbounty = ModeFactory.create(Mode.BUGBOUNTY)
        assert isinstance(bugbounty, BugBountyMode)
        
        ctf = ModeFactory.create(Mode.CTF)
        assert isinstance(ctf, CTFMode)
    
    def test_bugbounty_capabilities(self):
        """Test bug bounty mode capabilities"""
        config = ModeConfig(
            name="bugbounty",
            description="Test",
            skills_dir="skills/MODES/BUGBOUNTY"
        )
        mode = BugBountyMode(config)
        
        caps = mode.get_capabilities()
        assert len(caps) > 0
        assert any("Reconnaissance" in c for c in caps)
    
    def test_ctf_challenges(self):
        """Test CTF mode challenge handling"""
        config = ModeConfig(
            name="ctf",
            description="Test",
            skills_dir="skills/MODES/CTF"
        )
        mode = CTFMode(config)
        
        # Add a challenge
        from redforge.modes.mode_implementations import CTFChallenge
        challenge = CTFChallenge(
            id="web-1",
            name="SQL Injection",
            category="web",
            points=100,
            flag="flag{sql_injection_test}",
            hints=["Check for quotes", "Try OR 1=1"]
        )
        mode.add_challenge(challenge)
        
        assert mode.challenges.get("web-1") is not None
        
        # Solve challenge
        result = mode._solve_challenge("solve", {
            "challenge_id": "web-1",
            "solution": "flag{sql_injection_test}"
        })
        
        assert result["status"] == "correct"
        assert result["points"] == 100


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
    
    def test_full_workflow(self):
        """Test full bug bounty workflow"""
        # Create mode
        config = ModeConfig(
            name="bugbounty",
            description="Test",
            skills_dir="skills/MODES/BUGBOUNTY"
        )
        mode = BugBountyMode(config)
        
        # Execute task
        result = mode.execute("recon on example.com", {"target": "example.com"})
        
        assert "task" in result
        assert "recon" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
