import asyncio
from typing import Callable, Any

class AgentRetryStrategy:
    def __init__(self, max_attempts: int = 3):
        self.max_attempts = max_attempts

    async def execute_with_retry(self, action: Callable[[], Any]) -> Any:
        attempts = 0
        last_exception = None
        while attempts < self.max_attempts:
            try:
                # Resolve both async and sync action calls
                if asyncio.iscoroutinefunction(action):
                    return await action()
                else:
                    return action()
            except Exception as e:
                attempts += 1
                last_exception = e
        raise last_exception
