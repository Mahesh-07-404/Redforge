from .base import BaseAgent


class LearningAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.id = "learning_agent"
        self.name = "Learning Agent"
        self.description = "Assists in security training and explanation workflows"
        self.supported_modes = ["learning"]
        self.supported_tools = []
        self.required_capabilities = ["EDUCATIONAL_GUIDANCE"]
