"""biz_core.framework.skill — Skill hot-loading with biz naming convention.

Wraps agentscope.skill.LocalSkillLoader so the biz project always uses
`./skills/biz/` as the default scan root and recursively picks up
nested folders (e.g. skills/biz/selection/, skills/biz/content_test/).
"""

from __future__ import annotations

from agentscope.skill import LocalSkillLoader as _ASLocalSkillLoader

BIZ_SKILLS_DIR = "./skills/biz"


class BizSkillLoader(_ASLocalSkillLoader):
    """Skill loader pinned to the biz skills directory."""

    def __init__(
        self,
        directory: str = BIZ_SKILLS_DIR,
        scan_subdir: bool = True,
    ) -> None:
        super().__init__(directory=directory, scan_subdir=scan_subdir)
