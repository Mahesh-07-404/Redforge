from ..contracts.session import TargetState

class TargetStateMachine:
    def __init__(self):
        self._state = TargetState(target=None, changed=False)

    def set(self, target_str: str) -> TargetState:
        self._state.target = target_str
        self._state.changed = True
        return self._state

    def get(self) -> TargetState | None:
        return self._state

    def change(self, new_target: str) -> None:
        pass

    def validate(self, target_str: str) -> bool:
        return True
