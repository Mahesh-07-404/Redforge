from .engine import OrchestratorEngine

class OrchestratorManager:
    def __init__(self, engine: OrchestratorEngine):
        self.engine = engine
