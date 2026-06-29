import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from redforge.planner.plan import Plan
from redforge.planner.task import Task
from redforge.policy.policy_decision import PolicyDecision, DecisionStatus, RiskLevel
from redforge.executor.contracts import ApprovedPlan, TaskResult, ExecutionResult
from redforge.executor.state import ExecutionStatus
from redforge.executor.events import ExecutionEvent
from redforge.executor.stream import StreamManager
from redforge.executor.parser import OutputParser
from redforge.executor.process import ProcessManager
from redforge.executor.runner import Runner
from redforge.executor.scheduler import TaskScheduler
from redforge.executor.executor import Executor

def test_output_parsing():
    # Subfinder parse
    sub_raw = "example.com\n[debug] test\nwww.example.com\n"
    res = OutputParser.parse("subfinder", sub_raw)
    assert res["subdomains"] == ["example.com", "www.example.com"]
    
    # Nmap parse
    nmap_raw = "80/tcp open http\n443/tcp open https\n"
    res = OutputParser.parse("nmap", nmap_raw)
    assert len(res["ports"]) == 2
    assert res["ports"][0]["port"] == 80
    assert res["ports"][1]["service"] == "https"
    
    # Httpx parse
    httpx_raw = "http://example.com\nhttps://example.com\n"
    res = OutputParser.parse("httpx", httpx_raw)
    assert res["urls"] == ["http://example.com", "https://example.com"]

@pytest.mark.asyncio
async def test_runner_mock_process():
    # Test executing a task via patched ProcessManager
    runner = Runner()
    task = Task(id="t1", title="Echo task", description="desc", tool_hint="echo")
    
    with patch("redforge.executor.process.ProcessManager.wait") as mock_wait, \
         patch("redforge.executor.process.ProcessManager.spawn") as mock_spawn:
        mock_wait.return_value = ("stdout data", "stderr data", 0)
        
        res = await runner.execute_task(task)
        assert res.status == ExecutionStatus.COMPLETED
        assert res.raw_output == "stdout data"
        assert res.exit_code == 0

@pytest.mark.asyncio
async def test_scheduler_dependencies_and_cancellation():
    scheduler = TaskScheduler()
    
    t1 = Task(id="t1", title="Task 1", description="First")
    t2 = Task(id="t2", title="Task 2", description="Second", dependencies=["t1"])
    t3 = Task(id="t3", title="Task 3", description="Third", dependencies=["t2"])
    
    # Mock runner execute_task to succeed for t1, but fail for t2
    async def mock_execute(task, timeout=60, retries=1):
        if task.id == "t1":
            return TaskResult(task_id=task.id, status=ExecutionStatus.COMPLETED, exit_code=0)
        elif task.id == "t2":
            return TaskResult(task_id=task.id, status=ExecutionStatus.FAILED, exit_code=1, error="t2 failed")
        return TaskResult(task_id=task.id, status=ExecutionStatus.COMPLETED)
        
    scheduler.runner.execute_task = mock_execute
    
    # Execute plan tasks
    results = await scheduler.execute_plan_tasks([t3, t2, t1])
    
    # Assert t1 completed, t2 failed, t3 skipped (since t2 failed)
    r1 = next(r for r in results if r.task_id == "t1")
    r2 = next(r for r in results if r.task_id == "t2")
    r3 = next(r for r in results if r.task_id == "t3")
    
    assert r1.status == ExecutionStatus.COMPLETED
    assert r2.status == ExecutionStatus.FAILED
    assert r3.status == ExecutionStatus.SKIPPED
    
    # Test cancellation mid-scheduler
    scheduler_cancel = TaskScheduler()
    scheduler_cancel.cancel()
    results_cancel = await scheduler_cancel.execute_plan_tasks([t1, t2])
    assert all(r.status == ExecutionStatus.CANCELLED for r in results_cancel)

@pytest.mark.asyncio
async def test_executor_enforcement_and_stream_events():
    stream = StreamManager()
    events = []
    stream.subscribe(lambda e: events.append(e))
    
    executor = Executor(stream)
    
    # Plan definition
    plan = Plan(
        goal="Test plan",
        ordered_tasks=[Task(id="t1", title="Task 1", description="First", tool_hint="echo")]
    )
    
    # Approved Plan - ALLOW status
    approved = ApprovedPlan(
        plan=plan,
        decision=PolicyDecision(status=DecisionStatus.ALLOW, risk_level=RiskLevel.LOW, reason="Approved")
    )
    
    # Denied Plan - DENY status
    denied = ApprovedPlan(
        plan=plan,
        decision=PolicyDecision(status=DecisionStatus.DENY, risk_level=RiskLevel.HIGH, reason="Blocked")
    )
    
    # 1. Enforce ALLOW decision checking
    with pytest.raises(ValueError) as exc:
        await executor.execute(denied)
    assert "Cannot execute plan" in str(exc.value)
    
    # 2. Run approved execution
    with patch("redforge.executor.process.ProcessManager.wait") as mock_wait, \
         patch("redforge.executor.process.ProcessManager.spawn") as mock_spawn:
        mock_wait.return_value = ("success", "", 0)
        
        result = await executor.execute(approved)
        assert result.status == ExecutionStatus.COMPLETED
        assert len(result.task_results) == 1
        
    # Check that stream events were emitted
    event_types = [e.event_type for e in events]
    assert "ExecutionStarted" in event_types
    assert "TaskStarted" in event_types
    assert "TaskFinished" in event_types
    assert "ExecutionFinished" in event_types
