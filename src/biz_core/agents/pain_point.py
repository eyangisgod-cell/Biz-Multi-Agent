"""biz_core.agents.pain_point — R1 Pain Point research agent."""

from __future__ import annotations

from biz_core.framework import BizAgent


class PainPointAgent(BizAgent):
    """R1: surface unmet customer pain points for the chosen niche."""

    name = "pain_point"
    sys_prompt = (
        "You are the Pain-Point Researcher (R1). Surface 3-5 unmet "
        "customer pain points in the merchant's niche. Always cite "
        "external sources (Reddit, forums, reviews) and never invent "
        "demand. If you cannot find evidence, say so explicitly."
    )
