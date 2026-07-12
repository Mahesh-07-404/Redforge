from .base import BaseAgent


class CTFAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.id = "ctf_agent"
        self.name = "CTF Agent"
        self.description = "Identifies flags and solves capture the flag challenges"
        self.supported_modes = ["ctf"]
        self.supported_tools = ["hashcat", "john"]
        self.required_capabilities = ["CTF_SOLVER"]
