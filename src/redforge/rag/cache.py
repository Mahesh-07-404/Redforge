import time
from typing import Dict, Any, Optional

class RAGCache:
    def __init__(self, ttl_seconds: int = 300):
        self.ttl = ttl_seconds
        self.store: Dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Optional[Any]:
        if key in self.store:
            val, timestamp = self.store[key]
            if time.time() - timestamp < self.ttl:
                return val
            else:
                del self.store[key]
        return None

    def set(self, key: str, value: Any):
        self.store[key] = (value, time.time())

    def invalidate(self):
        self.store.clear()
