from enum import Enum


class ReasoningState(Enum):
    IDLE = "IDLE"
    PLANNING = "PLANNING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    EXECUTING = "EXECUTING"
    COLLECTING = "COLLECTING"
    REASONING = "REASONING"
    REFLECTING = "REFLECTING"
    REPLANNING = "REPLANNING"
    FINISHED = "FINISHED"
    FAILED = "FAILED"


class ReasoningStateMachine:
    def __init__(self):
        self.state = ReasoningState.IDLE

    def transition_to(self, new_state: ReasoningState):
        self.state = new_state
