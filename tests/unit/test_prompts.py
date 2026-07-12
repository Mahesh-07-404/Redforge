"""Unit tests for RedForge Prompt Library"""

import pytest

from redforge.prompts.registry import PromptRegistry, get_prompt_registry


def test_prompt_registry_loading():
    registry = get_prompt_registry()
    assert len(registry.prompts) >= 15

    # Check some known prompts
    p_thought = registry.get_prompt("reasoning_thought_loop")
    assert p_thought.id == "reasoning_thought_loop"
    assert p_thought.category == "reasoning"
    assert "query" in p_thought.variables
    assert "context" in p_thought.variables


def test_prompt_rendering():
    registry = get_prompt_registry()

    rendered = registry.render(
        "reasoning_thought_loop", query="Scan google.com", context="Target: google.com"
    )

    assert "Scan google.com" in rendered
    assert "Target: google.com" in rendered


def test_prompt_rendering_missing_variable():
    registry = get_prompt_registry()

    with pytest.raises(ValueError):
        # Missing context variable
        registry.render("reasoning_thought_loop", query="Scan google.com")


def test_get_suitable_prompt():
    registry = get_prompt_registry()

    # Test mapping of intent
    p_recon = registry.get_suitable_prompt("RECON")
    assert p_recon.id == "recon_passive_active"

    # Test category fallback
    p_cat = registry.get_suitable_prompt("UNKNOWN_INTENT", category="cloud")
    assert p_cat.id == "cloud_resource_auditor"

    # Test default fallback
    p_fall = registry.get_suitable_prompt("UNKNOWN_INTENT")
    assert p_fall.id in ("reasoning_thought_loop", "planning_dynamic_plan")
