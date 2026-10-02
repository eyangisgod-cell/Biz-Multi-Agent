"""biz_core.agents.merchant_profile — R8 Merchant Profile agent."""

from __future__ import annotations

from biz_core.framework import BizAgent


class MerchantProfileAgent(BizAgent):
    """R8: maintain the merchant's evolving profile / strategy memory."""

    name = "merchant_profile"
    sys_prompt = (
        "You are the Merchant Profile Curator (R8). After every run, "
        "update the merchant's strategy memory: niche, audience, "
        "successful SKU archetypes, content patterns, and ROI guardrails. "
        "Never mix profiles across merchants (single-tenant per design §R8)."
    )
