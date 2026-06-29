from typing import Dict

class FailureHandler:
    def __init__(self, max_retries: int = 2):
        self.max_retries = max_retries
        self.retry_counts: Dict[str, int] = {}

    def handle_failure(self, task_id: str) -> str:
        count = self.retry_counts.get(task_id, 0)
        if count < self.max_retries:
            self.retry_counts[task_id] = count + 1
            return "retry"
            
        tool_switch = {
            "subfinder": "amass",
            "httpx": "curl",
            "nmap": "naabu"
        }
        if task_id in tool_switch:
            return f"switch_to_{tool_switch[task_id]}"
            
        return "fail"
