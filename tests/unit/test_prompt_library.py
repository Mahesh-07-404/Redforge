"""Unit tests for RedForge General Prompt Library"""

import pytest

from redforge.prompt_library.registry import (
    PromptLibraryRegistry,
    get_prompt_library_registry,
)


def test_prompt_library_loading():
    registry = get_prompt_library_registry()
    assert len(registry.prompts) >= 10

    p_chat = registry.get_prompt("chat_general_chat")
    assert p_chat.id == "chat_general_chat"
    assert p_chat.category == "chat"
    assert "query" in p_chat.variables
    assert "history" in p_chat.variables


def test_prompt_library_rendering():
    registry = get_prompt_library_registry()

    rendered = registry.render(
        "chat_general_chat", query="Hello", history="No history"
    )

    assert "Hello" in rendered
    assert "No history" in rendered


def test_prompt_library_rendering_missing_variable():
    registry = get_prompt_library_registry()

    with pytest.raises(ValueError):
        # Missing history variable
        registry.render("chat_general_chat", query="Hello")


def test_get_suitable_general_prompt():
    registry = get_prompt_library_registry()

    # Test mapping of intent
    p_chat = registry.get_suitable_prompt("GENERAL_CHAT")
    assert p_chat.id == "chat_general_chat"

    # Test category fallback
    p_cat = registry.get_suitable_prompt("UNKNOWN_INTENT", category="coding")
    assert p_cat.id == "coding_developer"

    # Test default fallback
    p_fall = registry.get_suitable_prompt("UNKNOWN_INTENT")
    assert p_fall.id in ("chat_general_chat", "reasoning_critical_thought")
