from ..contracts.intent import ParsedIntent
from ..session.target import TargetStateMachine
from ..session.events import EventBus

class TargetWatcher:
    def __init__(self, state_machine: TargetStateMachine, event_bus: EventBus):
        self.state_machine = state_machine
        self.event_bus = event_bus

    def check(self, intent: ParsedIntent) -> ParsedIntent:
        current_state = self.state_machine.get()
        if intent.target and (current_state.target != intent.target):
            intent.target_changed = True
            self.state_machine.set(intent.target)
        return intent
