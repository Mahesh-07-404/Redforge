from typing import Dict, List
from .contracts import WorkflowDefinition
from .workflow import BuiltInWorkflows

class WorkflowLoader:
    def __init__(self):
        self.definitions: Dict[str, WorkflowDefinition] = {}
        for wf in BuiltInWorkflows.get_defaults():
            self.definitions[wf.id] = wf

    def load_custom_workflow(self, definition: WorkflowDefinition):
        self.definitions[definition.id] = definition

    def get_workflow(self, workflow_id: str) -> WorkflowDefinition:
        return self.definitions.get(workflow_id)

    def list_workflows(self) -> List[WorkflowDefinition]:
        return list(self.definitions.values())
