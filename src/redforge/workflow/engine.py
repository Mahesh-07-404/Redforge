from typing import Any

from .conditions import ConditionValidator
from .events import WorkflowEvents
from .executor import StageExecutor
from .loader import WorkflowLoader
from .scheduler import WorkflowScheduler
from .state_machine import WorkflowState, WorkflowStateMachine
from .validator import WorkflowValidator


class WorkflowEngine:
    def __init__(self):
        self.loader = WorkflowLoader()
        self.state_machine = WorkflowStateMachine()
        self.executor = StageExecutor()
        self.events = WorkflowEvents()

    async def execute_workflow(
        self, workflow_id: str, target: str, context: dict[str, Any] = None
    ) -> WorkflowState:
        if context is None:
            context = {}

        wf = self.loader.get_workflow(workflow_id)
        if not wf:
            self.state_machine.transition_to(WorkflowState.FAILED)
            return WorkflowState.FAILED

        WorkflowValidator.validate(wf)

        if not ConditionValidator.check_conditions(wf.conditions, context):
            self.state_machine.transition_to(WorkflowState.FAILED)
            return WorkflowState.FAILED

        self.state_machine.transition_to(WorkflowState.READY)
        self.state_machine.transition_to(WorkflowState.RUNNING)
        self.events.fire("workflow_started", f"Workflow {workflow_id} started on target {target}")

        scheduled = WorkflowScheduler.schedule_stages(wf.stages)
        for stage in scheduled:
            try:
                await self.executor.execute_stage(stage, context)
            except Exception as e:
                self.state_machine.transition_to(WorkflowState.FAILED)
                self.events.fire("workflow_failed", f"Stage {stage.id} failed: {e}")
                return WorkflowState.FAILED

        self.state_machine.transition_to(WorkflowState.COMPLETED)
        self.events.fire("workflow_completed", f"Workflow {workflow_id} completed successfully.")
        return WorkflowState.COMPLETED
