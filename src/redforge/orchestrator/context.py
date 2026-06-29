from typing import Dict, Any

class OrchestratorContext:
    def __init__(self):
        self.shared_data: Dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        return self.shared_data.get(key, default)

    def set(self, key: str, value: Any):
        self.shared_data[key] = value
