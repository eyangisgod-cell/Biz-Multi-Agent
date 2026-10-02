"""biz_core.framework.sop — Multi-agent roundtable (SOP) adapter.

The biz_core design replaces the originally-proposed MsgHub with an
SOP (Standard Operating Procedure) engine that runs Advocate /
Opponent / Reviewer roles in sequence. BizSOPEngine is a thin
adapter; per-role SOP steps live in the application layer.
"""

from __future__ import annotations

from agentscope.sop import SOPEngine as _ASSOPEngine

# Phase name constants used by R2 selection (Advocate vs Opponent)
# and the review engine (Reviewer).
PHASE_ADVOCATE = "advocate"
PHASE_OPPONENT = "opponent"
PHASE_REVIEWER = "reviewer"


class BizSOPEngine(_ASSOPEngine):
    """Adapter subclass — application SOPs should inherit this."""
