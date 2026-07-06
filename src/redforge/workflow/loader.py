from .contracts import WorkflowDefinition
from .workflow import BuiltInWorkflows


class WorkflowLoader:
    def __init__(self):
        self.definitions: dict[str, WorkflowDefinition] = {}
        for wf in BuiltInWorkflows.get_defaults():
            self.definitions[wf.id] = wf

    def load_custom_workflow(self, definition: WorkflowDefinition) -> None:
        self.definitions[definition.id] = definition

    def get_workflow(self, workflow_id: str) -> WorkflowDefinition | None:
        return self.definitions.get(workflow_id)

    def list_workflows(self) -> list[WorkflowDefinition]:
        return list(self.definitions.values())
