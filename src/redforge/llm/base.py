"""Base LLM provider interface"""

from abc import ABC, abstractmethod
from typing import List, Optional, AsyncIterator, Dict, Any
from dataclasses import dataclass
from enum import Enum

from redforge.llm.catalog import DEFAULT_MODELS


class MessageRole(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    role: str
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None


@dataclass
class ChatResponse:
    content: str
    model: str
    finish_reason: Optional[str] = None
    usage: Optional[Dict[str, int]] = None
    raw_response: Optional[Dict[str, Any]] = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(
        self,
        model: str,
        api_key: str = "",
        base_url: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.extra_kwargs = kwargs
    
    @abstractmethod
    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None,
        **kwargs
    ) -> ChatResponse:
        """Send a chat request and get a response"""
        pass
    
    @abstractmethod
    async def chat_stream(
        self,
        messages: List[Message],
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Send a chat request and stream the response"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available/configured"""
        pass
    
    @abstractmethod
    async def list_models(self) -> List[str]:
        """List available models for this provider"""
        pass
    
    def supports_tools(self) -> bool:
        """Check if this provider supports function calling"""
        return False
    
    def supports_streaming(self) -> bool:
        """Check if this provider supports streaming"""
        return True


class ProviderFactory:
    """Factory for creating LLM providers"""
    
    _providers = {
        "ollama": "redforge.llm.ollama.OllamaProvider",
        "openai": "redforge.llm.openai.OpenAIProvider",
        "anthropic": "redforge.llm.anthropic.AnthropicProvider",
        "groq": "redforge.llm.groq.GroqProvider",
        "gemini": "redforge.llm.gemini.GeminiProvider",
    }
    
    @classmethod
    def create(
        cls,
        provider: str,
        model: str,
        api_key: str = "",
        base_url: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> LLMProvider:
        """Create an LLM provider instance"""
        provider_lower = provider.lower()
        model = model or DEFAULT_MODELS.get(provider_lower, DEFAULT_MODELS["gemini"])
        
        if provider_lower == "ollama":
            from redforge.llm.ollama import OllamaProvider
            return OllamaProvider(
                model=model,
                base_url=base_url or "http://localhost:11434",
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
        
        elif provider_lower == "openai":
            from redforge.llm.openai import OpenAIProvider
            return OpenAIProvider(
                model=model,
                api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
        
        elif provider_lower == "anthropic":
            from redforge.llm.anthropic import AnthropicProvider
            return AnthropicProvider(
                model=model,
                api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
        
        elif provider_lower == "groq":
            from redforge.llm.groq import GroqProvider
            return GroqProvider(
                model=model,
                api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
        
        elif provider_lower == "gemini":
            from redforge.llm.gemini import GeminiProvider
            return GeminiProvider(
                model=model,
                api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
        
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    @classmethod
    def list_providers(cls) -> List[str]:
        """List available provider names"""
        return list(cls._providers.keys())
