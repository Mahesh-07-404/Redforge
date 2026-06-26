"""Current provider defaults and fallback model catalogs."""

from __future__ import annotations

import os

DEFAULT_MODELS = {
    "ollama": "llama3.2",
    "openai": "gpt-5.5",
    "anthropic": "claude-sonnet-4-6",
    "groq": "llama-3.3-70b-versatile",
    "gemini": "gemini-2.0-flash",
}

FALLBACK_MODELS = {
    "ollama": [
        "llama3.2",
        "llama3.1",
        "qwen2.5-coder",
        "mistral",
        "deepseek-r1",
    ],
    "openai": [
        "gpt-5.5",
        "gpt-5.4",
        "gpt-5.4-mini",
        "gpt-5.4-nano",
        "gpt-4.1",
        "gpt-4.1-mini",
        "gpt-4o",
        "gpt-4o-mini",
    ],
    "anthropic": [
        "claude-opus-4-8",
        "claude-sonnet-4-6",
        "claude-haiku-4-5",
        "claude-haiku-4-5-20251001",
        "claude-opus-4-1-20250805",
        "claude-sonnet-4-20250514",
        "claude-3-7-sonnet-latest",
        "claude-3-5-haiku-latest",
    ],
    "groq": [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "groq/compound",
        "groq/compound-mini",
        "meta-llama/llama-4-scout-17b-16e-instruct",
        "qwen/qwen3-32b",
    ],
    "gemini": [
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-2.0-pro",
        "gemini-3.1-flash-lite",
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-flash-latest",
    ],
}

API_KEY_ENV_VARS = {
    "openai": ("OPENAI_API_KEY",),
    "anthropic": ("ANTHROPIC_API_KEY", "CLAUDE_API_KEY"),
    "groq": ("GROQ_API_KEY",),
    "gemini": ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
}


def resolve_api_key(provider: str, api_key: str = "") -> str:
    """Return the explicit key or the first standard env var for a provider."""
    if api_key:
        return api_key

    for env_var in API_KEY_ENV_VARS.get(provider.lower(), ()):
        value = os.getenv(env_var)
        if value:
            return value

    return ""

