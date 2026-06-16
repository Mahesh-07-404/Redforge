from .pipeline import Pipeline

class RedForgeAgent:
    def __init__(self, pipeline: Pipeline):
        self.pipeline = pipeline

    def run(self, raw_input: str, session_id: str):
        return self.pipeline.process_turn(raw_input, session_id)
