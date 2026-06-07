"""LLM providers module"""

from typing import Optional

from redforge.llm.base import LLMProvider, Message, ChatResponse
from redforge.llm.catalog import DEFAULT_MODELS
from redforge.llm.ollama import OllamaProvider
from redforge.llm.openai import OpenAIProvider
from redforge.llm.anthropic import AnthropicProvider
from redforge.llm.groq import GroqProvider
from redforge.llm.gemini import GeminiProvider

__all__ = [
    "LLMProvider",
    "Message",
    "ChatResponse",
    "OllamaProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "GroqProvider",
    "GeminiProvider",
    "get_llm",
]


def get_llm(provider: str = "gemini", model: str = "", 
            api_key: Optional[str] = None, **kwargs) -> LLMProvider:
    """
    Factory function to create LLM provider instances.
    
    Args:
        provider: Provider name (ollama, openai, anthropic, groq, gemini)
        model: Model name
        api_key: API key for cloud providers
        **kwargs: Additional provider-specific options
    
    Returns:
        LLMProvider instance
    """
    providers = {
        "ollama": OllamaProvider,
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "groq": GroqProvider,
        "gemini": GeminiProvider,
    }
    
    provider_class = providers.get(provider.lower())
    if not provider_class:
        raise ValueError(f"Unknown provider: {provider}")
    
    selected_model = model or DEFAULT_MODELS.get(provider.lower(), DEFAULT_MODELS["gemini"])
    return provider_class(model=selected_model, api_key=api_key or "", **kwargs)
