"""Unit tests for biz_core.framework.skill (BizSkillLoader)."""

from __future__ import annotations

from pathlib import Path

from biz_core.framework.skill import BIZ_SKILLS_DIR, BizSkillLoader


def test_biz_skill_loader_default_directory() -> None:
    """Default skills directory should follow biz naming convention."""
    loader = BizSkillLoader()
    # LocalSkillLoader normalises to absolute path; check the trailing segment.
    assert Path(loader.directory).name == Path(BIZ_SKILLS_DIR).name
    assert str(loader.directory).endswith("skills/biz") or str(
        loader.directory
    ).endswith("skills\\biz")


def test_biz_skill_loader_custom_directory() -> None:
    """Custom directory overrides the default."""
    loader = BizSkillLoader(directory="./custom_skills")
    assert Path(loader.directory).name == "custom_skills"


def test_biz_skill_loader_inherits_agentscope_loader() -> None:
    """BizSkillLoader must subclass agentscope.skill.LocalSkillLoader."""
    from agentscope.skill import LocalSkillLoader

    assert issubclass(BizSkillLoader, LocalSkillLoader)


def test_biz_skill_loader_scan_subdir_default() -> None:
    """scan_subdir should default to True for biz skills (nested layout)."""
    loader = BizSkillLoader()
    assert loader.scan_subdir is True
