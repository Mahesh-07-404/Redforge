import pytest
from redforge.planner.task import Task
from redforge.normalize.entities import HostEntity, PortEntity
from redforge.reasoning.contracts import Goal, ReasoningDecision
from redforge.reasoning.goal_manager import GoalManager
from redforge.reasoning.task_decomposer import TaskDecomposer
from redforge.reasoning.strategy_selector import StrategySelector
from redforge.reasoning.world_state import WorldState
from redforge.reasoning.self_evaluator import SelfEvaluator
from redforge.reasoning.reflection import SelfReflection
from redforge.reasoning.replanner import Replanner
from redforge.reasoning.failure_handler import FailureHandler
from redforge.reasoning.state_machine import ReasoningStateMachine, ReasoningState
from redforge.reasoning.reasoner import Reasoner
from redforge.reasoning.engine import ReasoningEngine

def test_goal_manager():
    manager = GoalManager()
    g = manager.create_goal("Find exposed panels")
    assert g.text == "Find exposed panels"
    assert g.status == "pending"
    
    manager.update_goal_status(g.id, "active")
    assert manager.goals[g.id].status == "active"

def test_task_decomposition():
    tasks = TaskDecomposer.decompose("Perform passive recon on example.com")
    assert len(tasks) == 3
    assert tasks[0].id == "subfinder"
    assert tasks[1].id == "httpx"
    assert tasks[2].id == "katana"
    
    tasks_port = TaskDecomposer.decompose("Scan ports")
    assert len(tasks_port) == 1
    assert tasks_port[0].id == "nmap"

def test_strategy_selector():
    assert StrategySelector.select_strategy("Perform passive scanning") == "Passive Recon"
    assert StrategySelector.select_strategy("Scan android app") == "Android"
    assert StrategySelector.select_strategy("Check API endpoints") == "API"

def test_world_state_and_evaluation():
    ws = WorldState()
    meta_args = {"session_id": "s", "execution_id": "e", "target": "t", "timestamp": "now", "source_tool": "test"}
    
    # 1. Update from host entity
    ws.update_from_entities([HostEntity(id="h1", value="example.com", **meta_args)])
    assert "example.com" in ws.hosts
    
    # 2. Progress evaluation
    progress = SelfEvaluator.evaluate_progress(ws, "Perform passive recon")
    assert progress["completed"] is True
    assert progress["coverage"] == 0.8
    
    # 3. Port update
    ws.update_from_entities([PortEntity(id="p1", value="80", **meta_args)])
    assert 80 in ws.ports

def test_self_reflection_and_replanning():
    ws = WorldState()
    
    # Task success but empty host state should trigger replan to amass
    decision = SelfReflection.reflect("subfinder", True, ws)
    assert decision.action == "replan"
    assert decision.next_task_id == "amass"
    
    # Replanner should switch subfinder with amass
    current_tasks = [Task(id="subfinder", title="Subfinder", description="scan", tool_hint="subfinder")]
    new_tasks = Replanner.replan(current_tasks, ws)
    assert new_tasks[0].id == "amass"

def test_failure_handling():
    handler = FailureHandler(max_retries=2)
    
    # Retry twice
    assert handler.handle_failure("subfinder") == "retry"
    assert handler.handle_failure("subfinder") == "retry"
    
    # Then switch tool
    assert handler.handle_failure("subfinder") == "switch_to_amass"

def test_state_machine_and_engine():
    engine = ReasoningEngine()
    
    tasks = engine.process_goal("Perform passive recon")
    assert len(tasks) > 0
    assert engine.state_machine.state == ReasoningState.REASONING
    
    # Reasoner thinking check
    dec = engine.reasoner.think("Perform passive recon")
    assert dec.action == "execute" # Since world state is empty
    
    engine.reasoner.world_state.hosts.add("example.com")
    dec_completed = engine.reasoner.think("Perform passive recon")
    assert dec_completed.action == "stop"
