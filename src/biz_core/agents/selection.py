"""biz_core.agents.selection — R2 Selection (Advocate + Opponent) agent."""

from __future__ import annotations

from biz_core.framework import BizAgent


class SelectionAgent(BizAgent):
    """R2: run Advocate vs Opponent SOP on candidate SKUs."""

    name = "selection"
    sys_prompt = (
        "You are the Selection Advocate (R2). Argue FOR each candidate "
        "SKU with concrete numbers (margin, BSR trend, search volume). "
        "The Opponent agent will rebut; converge on the SKU with the "
        "strongest evidence, not the most optimistic forecast."
    )
