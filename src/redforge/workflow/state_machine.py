from enum import Enum

class WorkflowState(Enum):
    CREATED = "CREATED"
    READY = "READY"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class WorkflowStateMachine:
    def __init__(self):
        self.state = WorkflowState.CREATED

    def transition_to(self, new_state: WorkflowState):
        self.state = new_state
