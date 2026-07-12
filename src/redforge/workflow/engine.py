import logging
from typing import Any

from redforge.prompts.registry import get_prompt_registry

from .conditions import ConditionValidator
from .events import WorkflowEvents
from .executor import StageExecutor
from .loader import WorkflowLoader
from .scheduler import WorkflowScheduler
from .state_machine import WorkflowState, WorkflowStateMachine
from .validator import WorkflowValidator

logger = logging.getLogger(__name__)


class WorkflowEngine:

    def __init__(self):
        self.loader = WorkflowLoader()
        self.state_machine = WorkflowStateMachine()
        self.executor = StageExecutor()
        self.events = WorkflowEvents()

    async def execute_workflow(
        self, workflow_id: str, target: str, context: dict[str, Any] | None = None
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

        # Retrieve and render workflow coordinator prompt
        try:
            registry = get_prompt_registry()
            rendered = registry.render(
                "workflow_stage_coordinator",
                current_stage=workflow_id,
                stage_history=str(context.get("history", [])),
                execution_status="RUNNING",
            )
            context["workflow_coordinator_prompt"] = rendered
            logger.debug("Rendered workflow coordinator prompt:\n%s", rendered)
        except Exception as e:
            logger.debug("Failed to render workflow prompt: %s", e)

        # Retrieve and render the general workflow generator template
        from redforge.prompt_library.registry import get_prompt_library_registry

        try:
            lib_registry = get_prompt_library_registry()
            rendered_gen = lib_registry.render(
                "workflow_generator", process_goal=workflow_id, steps_count=str(len(wf.stages))
            )
            context["workflow_generator_prompt"] = rendered_gen
            logger.debug("Rendered general workflow generator prompt:\n%s", rendered_gen)
        except Exception as e:
            logger.debug("Failed to render general workflow prompt: %s", e)

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
