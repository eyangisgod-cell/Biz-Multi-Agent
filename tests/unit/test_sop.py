"""Unit tests for biz_core.framework.sop (BizSOPEngine)."""

from __future__ import annotations

from biz_core.framework.sop import BizSOPEngine


def test_biz_sop_engine_inherits_agentscope_sop() -> None:
    """BizSOPEngine must subclass agentscope.sop.SOPEngine."""
    from agentscope.sop import SOPEngine

    assert issubclass(BizSOPEngine, SOPEngine)


def test_sop_phase_enum_constants_exposed() -> None:
    """Common SOP phase names must be available as constants."""
    from biz_core.framework.sop import (
        PHASE_ADVOCATE,
        PHASE_OPPONENT,
        PHASE_REVIEWER,
    )

    assert PHASE_ADVOCATE == "advocate"
    assert PHASE_OPPONENT == "opponent"
    assert PHASE_REVIEWER == "reviewer"
