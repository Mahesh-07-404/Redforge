import pytest
import asyncio
from redforge.planner.plan import Plan
from redforge.planner.task import Task
from redforge.agents import BaseAgent, ReconAgent, WebAgent, NetworkAgent
from redforge.orchestrator.contracts import AgentTaskResult
from redforge.orchestrator.communication import AgentMessage, CommunicationBus
from redforge.orchestrator.agent_registry import AgentRegistry
from redforge.orchestrator.agent_loader import AgentLoader
from redforge.orchestrator.result_merger import ResultMerger
from redforge.orchestrator.retry import AgentRetryStrategy
from redforge.orchestrator.dispatcher import AgentDispatcher
from redforge.orchestrator.scheduler import AgentScheduler
from redforge.orchestrator.coordinator import AgentCoordinator
from redforge.orchestrator.engine import OrchestratorEngine

def test_agent_registry_and_loader():
    registry = AgentRegistry()
    AgentLoader.load_agents(registry)
    
    agents = registry.list_agents()
    assert len(agents) == 10
    
    recon = registry.lookup_agent("recon_agent")
    assert recon is not None
    assert recon.name == "Recon Agent"
    assert "subfinder" in recon.supported_tools

def test_coordinator_agent_selection():
    registry = AgentRegistry()
    AgentLoader.load_agents(registry)
    coordinator = AgentCoordinator(registry)
    
    # Plan containing custom tasks
    plan = Plan(
        goal="Port scan and passive recon",
        ordered_tasks=[
            Task(id="t1", title="Port scan", description="scan", tool_hint="nmap"),
            Task(id="t2", title="Subdomains", description="subdomains", tool_hint="subfinder")
        ]
    )
    
    assignments = coordinator.select_agents_for_plan(plan)
    assert len(assignments) == 2
    
    # nmap task should map to network_agent
    assert assignments[0][0].id == "network_agent"
    
    # subfinder task should map to recon_agent or bugbounty
    assert assignments[1][0].id in ("recon_agent", "bugbounty_agent")

def test_communication_bus():
    bus = CommunicationBus()
    messages = []
    bus.subscribe(lambda msg: messages.append(msg))
    
    msg = AgentMessage(
        message_type="TaskAssigned",
        sender="coordinator",
        recipient="recon_agent",
        data={"task": "subfinder"}
    )
    bus.publish(msg)
    
    assert len(messages) == 1
    assert messages[0].message_type == "TaskAssigned"
    assert messages[0].recipient == "recon_agent"

def test_result_merger():
    results = [
        AgentTaskResult(task_id="t1", agent_id="a1", status="completed", output="result one\nduplicate line"),
        AgentTaskResult(task_id="t2", agent_id="a2", status="completed", output="result two\nduplicate line")
    ]
    
    merged = ResultMerger.merge_results(results)
    assert "result one" in merged
    assert "result two" in merged
    assert merged.count("duplicate line") == 1

@pytest.mark.asyncio
async def test_retry_strategy():
    retry = AgentRetryStrategy(max_attempts=3)
    counter = 0
    
    async def mock_action():
        nonlocal counter
        counter += 1
        if counter < 3:
            raise ValueError("Mock Error")
        return "success"
        
    res = await retry.execute_with_retry(mock_action)
    assert res == "success"
    assert counter == 3

@pytest.mark.asyncio
async def test_orchestrator_engine():
    engine = OrchestratorEngine()
    plan = Plan(
        goal="Web scanning task",
        ordered_tasks=[
            Task(id="t1", title="Recon step", description="desc", tool_hint="subfinder")
        ]
    )
    
    res = await engine.orchestrate(plan)
    assert res.plan_goal == "Web scanning task"
    assert res.status == "completed"
    assert len(res.agent_results) == 1
    assert res.agent_results[0].agent_id in ("recon_agent", "bugbounty_agent")
