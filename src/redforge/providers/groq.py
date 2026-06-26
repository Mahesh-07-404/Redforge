"""Groq LLM provider"""

from typing import List, Optional, AsyncIterator, Dict, Any
from redforge.providers.base import LLMProvider, Message, ChatResponse
from redforge.providers.catalog import DEFAULT_MODELS, FALLBACK_MODELS, resolve_api_key


class GroqProvider(LLMProvider):
    """Groq API provider (fast inference)"""
    
    def __init__(
        self,
        model: str = DEFAULT_MODELS["groq"],
        api_key: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        base_url: str = "https://api.groq.com/openai/v1",
        **kwargs
    ):
        super().__init__(
            model=model,
            api_key=resolve_api_key("groq", api_key),
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        return self._client
    
    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None,
        **kwargs
    ) -> ChatResponse:
        """Send a chat request to Groq"""
        groq_messages = [self._convert_message(m) for m in messages]
        
        request_params = {
            "model": self.model,
            "messages": groq_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        
        if tools:
            request_params["tools"] = tools
            if tool_choice:
                request_params["tool_choice"] = tool_choice
        
        try:
            response = await self.client.chat.completions.create(**request_params)
            
            choice = response.choices[0]
            content = choice.message.content or ""
            
            return ChatResponse(
                content=content,
                model=response.model,
                finish_reason=choice.finish_reason,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                raw_response=response.model_dump()
            )
        except Exception as e:
            raise RuntimeError(f"Groq request failed: {e}")
    
    async def chat_stream(
        self,
        messages: List[Message],
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream chat response from Groq"""
        groq_messages = [self._convert_message(m) for m in messages]
        
        request_params = {
            "model": self.model,
            "messages": groq_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": True,
        }
        
        if tools:
            request_params["tools"] = tools
        
        try:
            stream = await self.client.chat.completions.create(**request_params)
            async for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        except Exception as e:
            raise RuntimeError(f"Groq stream failed: {e}")
    
    def is_available(self) -> bool:
        """Check if Groq API key is configured"""
        return bool(self.api_key)
    
    async def list_models(self) -> List[str]:
        """List available Groq models"""
        try:
            models = await self.client.models.list()
            return [m.id for m in models.data]
        except Exception:
            return FALLBACK_MODELS["groq"]
    
    def supports_tools(self) -> bool:
        """Groq supports function calling"""
        return True
    
    def supports_streaming(self) -> bool:
        return True
    
    def _convert_message(self, message: Message) -> Dict[str, Any]:
        """Convert Message to Groq format"""
        msg = {
            "role": message.role,
            "content": message.content
        }
        if message.name:
            msg["name"] = message.name
        if message.tool_call_id:
            msg["tool_call_id"] = message.tool_call_id
        return msg
