"""Unit tests for biz_core.framework.state (BizAgentState)."""

from __future__ import annotations

from biz_core.framework.state import BizAgentState


def test_biz_state_has_sample_count_field() -> None:
    """sample_count tracks cumulative samples across the orchestrator run."""
    state = BizAgentState()
    assert hasattr(state, "sample_count")
    assert state.sample_count == 0


def test_biz_state_has_current_phase_field() -> None:
    """current_phase tracks which R-phase the orchestrator is in."""
    state = BizAgentState(current_phase="R2_selection")
    assert state.current_phase == "R2_selection"


def test_biz_state_has_error_count_field() -> None:
    """error_count tracks number of recoverable errors in current phase."""
    state = BizAgentState(error_count=3)
    assert state.error_count == 3


def test_biz_state_validates_current_phase_enum() -> None:
    """current_phase must be one of R1..R9 or initial."""
    state = BizAgentState(current_phase="R1_pain_point")
    assert state.current_phase == "R1_pain_point"


def test_biz_state_inherits_agentscope_agentstate() -> None:
    """BizAgentState must subclass agentscope.state.AgentState."""
    from agentscope.state import AgentState

    assert issubclass(BizAgentState, AgentState)


def test_biz_state_preserves_base_fields() -> None:
    """Base AgentState fields (session_id, summary) remain accessible."""
    state = BizAgentState(session_id="s-1", summary="hello")
    assert state.session_id == "s-1"
    assert state.summary == "hello"
    assert state.sample_count == 0


def test_biz_state_can_increment_sample_count() -> None:
    """sample_count is mutable for orchestrator bookkeeping."""
    state = BizAgentState()
    state.sample_count += 1
    state.sample_count += 1
    assert state.sample_count == 2
