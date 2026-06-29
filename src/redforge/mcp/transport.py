import json
from typing import Dict, Any

class MCPTransport:
    async def send_message(self, message: Dict[str, Any]) -> str:
        return json.dumps({"jsonrpc": "2.0", "result": message})
