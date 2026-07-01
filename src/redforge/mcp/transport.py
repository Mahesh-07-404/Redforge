import json
from typing import Any


class MCPTransport:
    async def send_message(self, message: dict[str, Any]) -> str:
        return json.dumps({"jsonrpc": "2.0", "result": message})
