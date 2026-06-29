import pytest
from redforge.workflow.contracts import WorkflowStage, WorkflowDefinition
from redforge.workflow.exceptions import WorkflowValidationError
from redforge.workflow.loader import WorkflowLoader
from redforge.workflow.validator import WorkflowValidator
from redforge.workflow.scheduler import WorkflowScheduler
from redforge.workflow.state_machine import WorkflowStateMachine, WorkflowState
from redforge.workflow.engine import WorkflowEngine

def test_workflow_loader():
    loader = WorkflowLoader()
    workflows = loader.list_workflows()
    assert len(workflows) == 8 # 8 default workflows
    
    passive = loader.get_workflow("passive_recon")
    assert passive.name == "Passive Recon"
    assert len(passive.stages) == 1
    assert passive.stages[0].agent == "recon_agent"

def test_workflow_validator():
    # Valid validation
    wf = WorkflowDefinition(
        id="test_wf",
        name="Test",
        description="Desc",
        supported_intents=["PENTEST"],
        stages=[
            WorkflowStage(id="s1", name="Stage 1", agent="a", planner_strategy="s"),
            WorkflowStage(id="s2", name="Stage 2", agent="b", planner_strategy="s", dependencies=["s1"])
        ]
    )
    WorkflowValidator.validate(wf)
    
    # Duplicate ID validation error
    invalid_wf = WorkflowDefinition(
        id="invalid",
        name="Test",
        description="Desc",
        supported_intents=["PENTEST"],
        stages=[
            WorkflowStage(id="s1", name="Stage 1", agent="a", planner_strategy="s"),
            WorkflowStage(id="s1", name="Stage 1 Duplicate", agent="b", planner_strategy="s")
        ]
    )
    with pytest.raises(WorkflowValidationError):
        WorkflowValidator.validate(invalid_wf)

def test_scheduler_ordering():
    s1 = WorkflowStage(id="s1", name="S1", agent="a", planner_strategy="s")
    s2 = WorkflowStage(id="s2", name="S2", agent="a", planner_strategy="s", dependencies=["s1"])
    s3 = WorkflowStage(id="s3", name="S3", agent="a", planner_strategy="s", dependencies=["s2"])
    
    # Passing out-of-order stages should resolve dependencies correctly
    scheduled = WorkflowScheduler.schedule_stages([s3, s2, s1])
    assert len(scheduled) == 3
    assert scheduled[0].id == "s1"
    assert scheduled[1].id == "s2"
    assert scheduled[2].id == "s3"

@pytest.mark.asyncio
async def test_workflow_engine_execution():
    engine = WorkflowEngine()
    
    # Run passive recon workflow
    res = await engine.execute_workflow("passive_recon", "example.com")
    assert res == WorkflowState.COMPLETED
    assert engine.state_machine.state == WorkflowState.COMPLETED

@pytest.mark.asyncio
async def test_workflow_engine_failure():
    engine = WorkflowEngine()
    
    # Custom failed execution trigger (empty target context condition failure)
    custom_wf = WorkflowDefinition(
        id="failed_wf",
        name="Failed Workflow",
        description="Desc",
        supported_intents=["PENTEST"],
        stages=[
            WorkflowStage(id="s1", name="S1", agent="a", planner_strategy="s")
        ],
        conditions=["target_reachable"]
    )
    
    engine.loader.load_custom_workflow(custom_wf)
    
    res = await engine.execute_workflow("failed_wf", "example.com", context={"target_reachable": False})
    assert res == WorkflowState.FAILED
