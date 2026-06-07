"""OpenAI LLM provider"""

from typing import List, Optional, AsyncIterator, Dict, Any
from redforge.llm.base import LLMProvider, Message, ChatResponse
from redforge.llm.catalog import DEFAULT_MODELS, FALLBACK_MODELS, resolve_api_key


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""
    
    def __init__(
        self,
        model: str = DEFAULT_MODELS["openai"],
        api_key: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ):
        super().__init__(
            model=model,
            api_key=resolve_api_key("openai", api_key),
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client
    
    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None,
        **kwargs
    ) -> ChatResponse:
        """Send a chat request to OpenAI"""
        openai_messages = [self._convert_message(m) for m in messages]
        
        request_params = {
            "model": self.model,
            "messages": openai_messages,
            "max_completion_tokens": self.max_tokens,
        }
        if not self._uses_fixed_sampling():
            request_params["temperature"] = self.temperature
        
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
            raise RuntimeError(f"OpenAI request failed: {e}")
    
    async def chat_stream(
        self,
        messages: List[Message],
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream chat response from OpenAI"""
        openai_messages = [self._convert_message(m) for m in messages]
        
        request_params = {
            "model": self.model,
            "messages": openai_messages,
            "max_completion_tokens": self.max_tokens,
            "stream": True,
        }
        if not self._uses_fixed_sampling():
            request_params["temperature"] = self.temperature
        
        if tools:
            request_params["tools"] = tools
        
        try:
            stream = await self.client.chat.completions.create(**request_params)
            async for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        except Exception as e:
            raise RuntimeError(f"OpenAI stream failed: {e}")
    
    def is_available(self) -> bool:
        """Check if OpenAI API key is configured"""
        return bool(self.api_key)
    
    async def list_models(self) -> List[str]:
        """List available OpenAI models"""
        try:
            models = await self.client.models.list()
            return [
                m.id for m in models.data
                if m.id.startswith(("gpt", "o"))
            ]
        except:
            return FALLBACK_MODELS["openai"]
    
    def supports_tools(self) -> bool:
        """OpenAI supports function calling"""
        return True
    
    def supports_streaming(self) -> bool:
        return True
    
    def _convert_message(self, message: Message) -> Dict[str, Any]:
        """Convert Message to OpenAI format"""
        msg = {
            "role": message.role,
            "content": message.content
        }
        if message.name:
            msg["name"] = message.name
        if message.tool_call_id:
            msg["tool_call_id"] = message.tool_call_id
        return msg

    def _uses_fixed_sampling(self) -> bool:
        """New reasoning-first models use provider defaults for sampling."""
        return self.model.startswith(("gpt-5", "o"))
