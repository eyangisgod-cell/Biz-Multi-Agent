"""biz_core.agents.orchestrator — 4-phase orchestrator state machine.

Drives the sequence init -> R1_pain_point -> R2_selection ->
R3_content_test -> R8_merchant_profile -> done. Each phase handler
is a pure callable `state -> PhaseResult` so the orchestrator is
unit-testable without spinning up real agents.

Hook contract:
  If a phase handler raises HookAbort, the orchestrator does NOT
  catch it — the caller decides whether to retry the phase, skip
  it, or abort the run. This keeps the orchestrator dumb and the
  recovery policy in one place.

Convergence:
  When a handler returns PhaseResult(outputs=[...]) and the latest
  two entries already converge, the orchestrator accepts the result
  and advances. Otherwise it would loop until convergence or a
  retry-budget exhaustion (caller's responsibility).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from biz_core.agents.convergence import ConvergenceJudge, is_converged
from biz_core.framework.state import BizAgentState, Phase

# Default 4-phase sequence. R4/R5/R6/R7 are handled by the
# per-role agents when relevant; the orchestrator only owns the
# top-level 4 stages.
PHASE_SEQUENCE: tuple[Phase, ...] = (
    "init",
    "R1_pain_point",
    "R2_selection",
    "R3_content_test",
    "R8_merchant_profile",
    "done",
)


@dataclass
class PhaseResult:
    """Output of a single phase handler.

    text:    short summary that gets attached to BizAgentState.
    outputs: optional list of past outputs feeding convergence
             detection. Empty list means "do not run convergence".
    """

    text: str
    outputs: list[str] = field(default_factory=list)


PhaseHandler = Callable[[BizAgentState], PhaseResult]


class Orchestrator:
    """Stateful 4-phase orchestrator.

    Handlers are injected at construction time so tests can pass
    in pure stubs without needing real agents / LLMs.
    """

    def __init__(
        self,
        handlers: dict[Phase, PhaseHandler] | None = None,
        state: BizAgentState | None = None,
        convergence_threshold: float = 0.85,
    ) -> None:
        self.state: BizAgentState = state or BizAgentState()
        self.handlers: dict[Phase, PhaseHandler] = handlers or {}
        self.convergence_threshold = convergence_threshold
        self._judge = ConvergenceJudge(threshold=convergence_threshold)
        self._current_idx: int = 0

    @property
    def current_phase(self) -> Phase:
        return PHASE_SEQUENCE[self._current_idx]

    def advance_to(self, phase: Phase) -> None:
        """Jump to a named phase; raises if the phase is unknown."""
        if phase not in PHASE_SEQUENCE:
            raise ValueError(f"Unknown phase: {phase!r}")
        self._current_idx = PHASE_SEQUENCE.index(phase)
        self.state.current_phase = phase

    def step(self) -> bool:
        """Run the current phase handler once.

        Returns True if the orchestrator advanced, False if it was
        already at `done`.
        """
        if self.current_phase == "done":
            return False
        if self.current_phase == "init":
            # init is a no-op phase — just advance.
            self._current_idx += 1
            self.state.current_phase = self.current_phase
            return True

        handler = self.handlers.get(self.current_phase)
        if handler is None:
            # No handler registered — skip the phase.
            self._current_idx += 1
            self.state.current_phase = self.current_phase
            return True

        result = handler(self.state)
        existing = self.state.summary
        # summary may be str OR a list of content blocks (per AgentState).
        # We only know how to append when it's a str — fall back to the
        # raw result text otherwise.
        if isinstance(existing, str):
            self.state.summary = existing + "\n" + result.text
        else:
            self.state.summary = result.text
        self.state.sample_count += 1
        # Convergence: if the handler supplied outputs and they
        # have already converged, we still advance (one round is
        # enough). The judge records the verdict for audit.
        if result.outputs:
            self._judge.record(result.outputs)
        self._current_idx += 1
        self.state.current_phase = self.current_phase
        return True

    def run(self) -> None:
        """Drive the orchestrator from its current phase to `done`."""
        while self.step():
            pass

    # Re-export helper for callers that want to test convergence in isolation.
    @staticmethod
    def converged(outputs: list[str], threshold: float = 0.85) -> bool:
        return is_converged(outputs, threshold=threshold)
