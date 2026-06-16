import pytest
from redforge.skills.loader import DynamicSkillLoader
from redforge.skills.registry import SkillRegistry, SkillMetadata

def test_dynamic_skill_loader():
    registry = SkillRegistry()
    registry.skills = {
        "sys_core": SkillMetadata(name="sys_core", category="SYSTEM", content="sys content"),
        "bugbounty_mode": SkillMetadata(name="bugbounty_mode", category="MODES", mode="BUGBOUNTY", content="mode content"),
    }
    loader = DynamicSkillLoader(registry)
    selected = loader.select_skills("SCAN", "bugbounty", "test")
    assert len(selected) > 0
