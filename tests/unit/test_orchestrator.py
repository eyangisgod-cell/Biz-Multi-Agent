"""Unit tests for biz_core.agents.orchestrator."""

from __future__ import annotations

import pytest

from biz_core.agents.orchestrator import (
    PHASE_SEQUENCE,
    Orchestrator,
    PhaseHandler,
    PhaseResult,
)
from biz_core.framework.middleware import HookAbort


def test_phase_sequence_starts_at_init_and_ends_at_done() -> None:
    """Default phase order is init -> R1 -> R2 -> R3 -> R8 -> done."""
    assert PHASE_SEQUENCE[0] == "init"
    assert PHASE_SEQUENCE[-1] == "done"
    assert "R1_pain_point" in PHASE_SEQUENCE
    assert "R2_selection" in PHASE_SEQUENCE
    assert "R3_content_test" in PHASE_SEQUENCE
    assert "R8_merchant_profile" in PHASE_SEQUENCE


def test_orchestrator_initial_state_is_init() -> None:
    """Fresh orchestrator must be at the `init` phase."""
    orch = Orchestrator()
    assert orch.state.current_phase == "init"


def test_orchestrator_advance_moves_through_sequence() -> None:
    """advance() walks through every phase until done."""
    calls: list[str] = []

    def make_handler(phase: str) -> PhaseHandler:
        def _h(state) -> PhaseResult:
            calls.append(phase)
            return PhaseResult(text=f"output-of-{phase}")

        return _h

    handlers = {p: make_handler(p) for p in PHASE_SEQUENCE if p not in ("init", "done")}
    orch = Orchestrator(handlers=handlers)
    orch.run()
    assert orch.state.current_phase == "done"
    # Each non-terminal phase handler should have been called exactly once.
    assert calls == [p for p in PHASE_SEQUENCE if p not in ("init", "done")]


def test_orchestrator_convergence_short_circuits_phase() -> None:
    """When a phase's handler returns outputs that already converge,
    the orchestrator moves on without forcing additional rounds."""
    calls: list[str] = []

    def r2_handler(state) -> PhaseResult:
        calls.append("R2_selection")
        # Already-converged outputs -> orchestrator should accept and advance.
        return PhaseResult(
            text="final-answer",
            outputs=["a b", "a b"],
        )

    def noop(phase: str) -> PhaseHandler:
        def _h(state):  # type: ignore[no-untyped-def]
            return PhaseResult(text=phase)

        return _h

    other_phases = [p for p in PHASE_SEQUENCE if p not in ("init", "R2_selection", "done")]
    orch = Orchestrator(
        handlers={
            "R2_selection": r2_handler,
            **{p: noop(p) for p in other_phases},
        },
    )
    orch.run()
    assert calls == ["R2_selection"]


def test_orchestrator_re_raises_hookabort() -> None:
    """HookAbort raised by a phase handler propagates out of run()."""
    def r1_handler(state) -> PhaseResult:
        raise HookAbort(reason="echo_detected", suggestion="regenerate")

    def noop(phase: str) -> PhaseHandler:
        def _h(state):  # type: ignore[no-untyped-def]
            return PhaseResult(text=phase)

        return _h

    other_phases = [p for p in PHASE_SEQUENCE if p not in ("init", "R1_pain_point", "done")]
    orch = Orchestrator(
        handlers={
            "R1_pain_point": r1_handler,
            **{p: noop(p) for p in other_phases},
        },
    )
    with pytest.raises(HookAbort) as exc_info:
        orch.run()
    assert exc_info.value.reason == "echo_detected"


def test_orchestrator_unknown_phase_raises() -> None:
    """Asking the orchestrator to advance to an unknown phase must fail loudly."""
    orch = Orchestrator()
    with pytest.raises(ValueError, match="Unknown phase"):
        orch.advance_to("R99_does_not_exist")
