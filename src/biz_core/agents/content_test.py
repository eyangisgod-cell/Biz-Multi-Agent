"""biz_core.agents.content_test — R3 Content Test agent."""

from __future__ import annotations

from biz_core.framework import BizAgent


class ContentTestAgent(BizAgent):
    """R3: design and run content tests for the selected SKU."""

    name = "content_test"
    sys_prompt = (
        "You are the Content Tester (R3). Generate 3 short-form video "
        "concepts (TikTok / Reels / Shorts) for the chosen SKU. Each "
        "concept must hook within 2 seconds and end on a CTA. Track "
        "CTR and conversion; reject concepts below 1.5x ROI."
    )
