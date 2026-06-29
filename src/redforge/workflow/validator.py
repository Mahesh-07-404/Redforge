from .contracts import WorkflowDefinition
from .exceptions import WorkflowValidationError

class WorkflowValidator:
    @staticmethod
    def validate(definition: WorkflowDefinition):
        if not definition.id:
            raise WorkflowValidationError("Workflow ID cannot be empty.")
        if not definition.stages:
            raise WorkflowValidationError("Workflow must contain at least one stage.")
        
        stage_ids = set()
        for stage in definition.stages:
            if stage.id in stage_ids:
                raise WorkflowValidationError(f"Duplicate stage ID detected: {stage.id}")
            stage_ids.add(stage.id)
            
        for stage in definition.stages:
            for dep in stage.dependencies:
                if dep not in stage_ids:
                    raise WorkflowValidationError(f"Stage dependency {dep} for stage {stage.id} not found in stages list.")
