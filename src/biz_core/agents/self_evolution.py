"""biz_core.agents.self_evolution — R9 Self-Evolution agent."""

from __future__ import annotations

from biz_core.framework import BizAgent


class SelfEvolutionAgent(BizAgent):
    """R9: review past runs and propose strategy / prompt improvements."""

    name = "self_evolution"
    sys_prompt = (
        "You are the Self-Evolution Analyst (R9). Audit the last 50 SKU "
        "runs and identify the top 3 patterns (winning / losing). Propose "
        "concrete prompt or strategy updates. Never touch raw merchant "
        "data — only aggregated learnings."
    )
