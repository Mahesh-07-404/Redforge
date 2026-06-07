"""Ollama LLM provider"""

import json
import httpx
from typing import List, Optional, AsyncIterator, Dict, Any
from redforge.llm.base import LLMProvider, Message, ChatResponse
from redforge.llm.catalog import DEFAULT_MODELS


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider"""
    
    def __init__(
        self,
        model: str = DEFAULT_MODELS["ollama"],
        base_url: str = "http://localhost:11434",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ):
        super().__init__(
            model=model,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        self.client = httpx.AsyncClient(timeout=120.0)
    
    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None,
        **kwargs
    ) -> ChatResponse:
        """Send a chat request to Ollama"""
        ollama_messages = [self._convert_message(m) for m in messages]
        
        request_data = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            }
        }
        
        if tools:
            request_data["tools"] = tools
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json=request_data
            )
            response.raise_for_status()
            data = response.json()
            
            content = data.get("message", {}).get("content", "")
            
            return ChatResponse(
                content=content,
                model=self.model,
                finish_reason=data.get("done_reason"),
                raw_response=data
            )
        except httpx.HTTPError as e:
            raise RuntimeError(f"Ollama request failed: {e}")
    
    async def chat_stream(
        self,
        messages: List[Message],
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream chat response from Ollama"""
        ollama_messages = [self._convert_message(m) for m in messages]
        
        request_data = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": True,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            }
        }
        
        if tools:
            request_data["tools"] = tools
        
        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=request_data
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            content = data.get("message", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
        except httpx.HTTPError as e:
            raise RuntimeError(f"Ollama stream failed: {e}")
    
    def is_available(self) -> bool:
        """Check if Ollama is running"""
        try:
            import httpx
            response = httpx.get(f"{self.base_url}/api/tags", timeout=5.0)
            return response.status_code == 200
        except:
            return False
    
    async def list_models(self) -> List[str]:
        """List available models in Ollama"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
        except:
            return []
    
    def supports_tools(self) -> bool:
        """Ollama supports tools in recent versions"""
        return True
    
    def _convert_message(self, message: Message) -> Dict[str, Any]:
        """Convert Message to Ollama format"""
        msg = {
            "role": message.role,
            "content": message.content
        }
        if message.name:
            msg["name"] = message.name
        return msg
