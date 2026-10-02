"""biz_core.framework.state — extended AgentState with biz-specific fields.

Adds three bookkeeping fields used by the orchestrator:
  - sample_count:    total samples processed in current run
  - current_phase:   which R-phase is active (R1..R9)
  - error_count:     recoverable errors accumulated in current phase
"""

from __future__ import annotations

from typing import Literal

from agentscope.state import AgentState as _ASAgentState

Phase = Literal[
    "init",
    "R1_pain_point",
    "R2_selection",
    "R3_content_test",
    "R4_creative",
    "R5_pricing",
    "R6_inventory",
    "R7_compliance",
    "R8_merchant_profile",
    "R9_self_evolution",
    "done",
]


class BizAgentState(_ASAgentState):
    """AgentState + orchestrator bookkeeping fields."""

    sample_count: int = 0
    current_phase: Phase = "init"
    error_count: int = 0
