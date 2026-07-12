from .base import BaseAgent


class AndroidAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.id = "android_agent"
        self.name = "Android Testing Agent"
        self.description = "Performs security scans and analyzes Android applications"
        self.supported_modes = ["pentest"]
        self.supported_tools = ["adb", "apktool"]
        self.required_capabilities = ["ANDROID_ANALYSIS"]
