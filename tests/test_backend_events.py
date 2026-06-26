"""Backend event and streaming tests for RedForge."""

from __future__ import annotations

import pytest

from redforge.config.config import Settings
from redforge.core.agent import RedForgeAgent
from redforge.core.skill_loader import SkillLoader
from redforge.core.state import AutonomyLevel, AgentMode
from redforge.providers.base import ChatResponse, ProviderFactory


class StreamingLLM:
    """Fake streaming provider for LangGraph agent tests."""

    async def chat(self, messages, tools=None, **kwargs):
        return ChatResponse(content="fallback", model="fake", usage={"total_tokens": 9})

    async def chat_stream(self, messages, tools=None, **kwargs):
        for chunk in ("Hello", " ", "world"):
            yield chunk

    def is_available(self):
        return True

    async def list_models(self):
        return ["fake"]

    def supports_streaming(self):
        return True


class SequencedLLM:
    """Fake non-streaming provider for tool execution tests."""

    def __init__(self):
        self._responses = [
            ChatResponse(
                content="TOOL: bash\nCOMMAND: echo backend-ok",
                model="fake",
                usage={"total_tokens": 5},
            ),
            ChatResponse(
                content="Finished.\nFINDING: backend | SEVERITY: info | command completed cleanly",
                model="fake",
                usage={"total_tokens": 6},
            ),
        ]

    async def chat(self, messages, tools=None, **kwargs):
        return self._responses.pop(0)

    async def chat_stream(self, messages, tools=None, **kwargs):
        raise AssertionError("streaming not expected in this test")

    def is_available(self):
        return True

    async def list_models(self):
        return ["fake"]

    def supports_streaming(self):
        return False


class LegacyStreamingLLM:
    """Fake streaming provider for the legacy Agent path."""

    async def chat(self, messages, tools=None, **kwargs):
        return ChatResponse(content="unused", model="fake", usage={"total_tokens": 8})

    async def chat_stream(self, messages, tools=None, **kwargs):
        for chunk in ("legacy", " backend"):
            yield chunk

    def is_available(self):
        return True

    async def list_models(self):
        return ["fake"]

    def supports_streaming(self):
        return True


@pytest.fixture(autouse=True)
def patch_skill_loader(monkeypatch):
    """Keep agent prompt building deterministic in tests."""
    monkeypatch.setattr(SkillLoader, "load_skills", lambda self: None)
    monkeypatch.setattr(SkillLoader, "get_top_k", lambda self, query, k=6: "")
    monkeypatch.setattr(SkillLoader, "get_context_for_mode", lambda self, mode: "")


@pytest.mark.asyncio
async def test_langgraph_agent_emits_streaming_events(monkeypatch, tmp_path):
    monkeypatch.setattr(ProviderFactory, "create", lambda *args, **kwargs: StreamingLLM())

    settings = Settings()
    settings.memory.persist_dir = str(tmp_path / "workspaces")
    agent = RedForgeAgent(config=settings, llm_provider="ollama", model="fake")
    events: list[dict] = []
    agent.on("*", lambda payload: events.append(payload))

    state = await agent.run(
        user_input="say hello",
        target="example.com",
        autonomy_level=AutonomyLevel.MANUAL,
        mode=AgentMode.KNOWLEDGE_BASED,
    )

    assert any(msg.get("content") == "Hello world" for msg in state.messages)
    assert state.total_tokens > 0
    assert [event["event"] for event in events].count("assistant_start") == 1
    assert [event["event"] for event in events].count("token") == 3
    assert events[-1]["event"] == "run_end"


@pytest.mark.asyncio
async def test_langgraph_agent_emits_tool_and_finding_events(monkeypatch, tmp_path):
    monkeypatch.setattr(ProviderFactory, "create", lambda *args, **kwargs: SequencedLLM())

    settings = Settings()
    settings.memory.persist_dir = str(tmp_path / "workspaces")
    agent = RedForgeAgent(config=settings, llm_provider="ollama", model="fake")
    events: list[dict] = []
    agent.on("*", lambda payload: events.append(payload))

    state = await agent.run(
        user_input="run a safe command",
        target="example.com",
        autonomy_level=AutonomyLevel.PARTIAL,
        mode=AgentMode.GOAL_BASED,
    )

    event_names = [event["event"] for event in events]
    assert "tool_start" in event_names
    assert "tool_end" in event_names
    assert "finding" in event_names
    assert "bash" in state.tools_used
    assert any("backend-ok" in msg.get("content", "") for msg in state.messages if msg.get("role") == "tool")
    assert state.findings[0]["type"] == "backend"


