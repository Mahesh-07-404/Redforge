"""Tests for RedForge core components"""

import pytest
from redforge.core.config import Settings, load_config
from redforge.core.agent import Agent, AgentMode
from redforge.memory.workspace import WorkspaceManager, Workspace


class TestConfig:
    """Test configuration module"""
    
    def test_default_settings(self):
        """Test default settings are created"""
        settings = Settings()
        assert settings.llm.provider == "gemini"
        assert settings.autonomy.default_level == "manual"
        assert settings.memory.vector_db == "qdrant"
    
    def test_settings_serialization(self):
        """Test settings can be serialized"""
        settings = Settings()
        data = settings.model_dump()
        assert "llm" in data
        assert "autonomy" in data
        assert "memory" in data


class TestAgent:
    """Test agent module"""
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test agent can be initialized"""
        agent = Agent()
        assert agent._llm_provider in ("ollama", "gemini", "openai")
        assert agent.agent_config.mode == AgentMode.GOAL_BASED
    
    def test_agent_status(self):
        """Test agent status reporting"""
        agent = Agent()
        status = agent.get_status()
        assert "provider" in status
        assert "model" in status
        assert "mode" in status
    
    def test_add_finding(self):
        """Test adding findings"""
        agent = Agent()
        finding = {"type": "xss", "severity": "high"}
        agent.add_finding(finding)
        findings = agent.get_findings()
        assert len(findings) == 1
        assert findings[0]["finding"] == finding


class TestWorkspace:
    """Test workspace module"""
    
    def test_workspace_creation(self, tmp_path):
        """Test workspace creation"""
        wm = WorkspaceManager(str(tmp_path))
        ws = wm.create_workspace("test-project")
        
        assert ws.name == "test-project"
        assert ws.id is not None
        assert ws.mode == "bugbounty"
    
    def test_workspace_persistence(self, tmp_path):
        """Test workspace persists after creation"""
        wm = WorkspaceManager(str(tmp_path))
        ws = wm.create_workspace("test-project")
        
        retrieved = wm.get_workspace(ws.id)
        assert retrieved is not None
        assert retrieved.name == "test-project"
    
    def test_workspace_by_name(self, tmp_path):
        """Test getting workspace by name"""
        wm = WorkspaceManager(str(tmp_path))
        ws = wm.create_workspace("unique-name")
        
        found = wm.get_workspace_by_name("unique-name")
        assert found is not None
        assert found.id == ws.id
    
    def test_list_workspaces(self, tmp_path):
        """Test listing workspaces"""
        wm = WorkspaceManager(str(tmp_path))
        wm.create_workspace("project1")
        wm.create_workspace("project2")
        
        workspaces = wm.list_workspaces()
        assert len(workspaces) == 2
    
    def test_workspace_context(self):
        """Test workspace context conversion"""
        from datetime import datetime
        ws = Workspace(
            id="test-id",
            name="test",
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            mode="ctf",
            scope=["*.example.com"]
        )
        context = ws.to_context()
        assert context["workspace_id"] == "test-id"
        assert context["workspace_mode"] == "ctf"
