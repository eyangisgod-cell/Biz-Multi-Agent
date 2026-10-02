"""biz_core.agents.convergence — convergence detection for SOP roundtables.

When an Advocate/Opponent/Reviewer SOP keeps re-raising the same
objections, the orchestrator should stop looping and accept the
current best answer. This module provides a tiny token-overlap
heuristic for that decision.

NOTE: this is intentionally simple (Jaccard token similarity). For
M3+, swap in embedding-based cosine similarity or a dedicated LLM
judge. The orchestrator depends only on the boolean return value,
so upgrades are non-breaking.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field


def _normalise(text: str) -> frozenset[str]:
    """Lowercase + split + drop empties; returns a frozenset of tokens."""
    return frozenset(t.lower() for t in text.split() if t)


def _jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    if not union:
        return 1.0
    return len(a & b) / len(union)


def is_converged(outputs: Iterable[str], threshold: float = 0.85) -> bool:
    """Return True when the latest two outputs exceed `threshold` similarity.

    Empty / single-element sequences return False (no convergence
    can be claimed with fewer than two data points).
    """
    seq = list(outputs)
    if len(seq) < 2:
        return False
    latest = _normalise(seq[-1])
    previous = _normalise(seq[-2])
    return _jaccard(latest, previous) >= threshold


@dataclass(frozen=True)
class ConvergenceVerdict:
    """Audit record of one convergence check."""

    converged: bool
    similarity: float
    threshold: float


@dataclass
class ConvergenceJudge:
    """Stateful judge that records its history for later inspection."""

    threshold: float = 0.85
    _history: list[ConvergenceVerdict] = field(default_factory=list)

    def record(self, outputs: Iterable[str]) -> bool:
        seq = list(outputs)
        if len(seq) < 2:
            verdict = ConvergenceVerdict(False, 0.0, self.threshold)
            self._history.append(verdict)
            return False
        latest = _normalise(seq[-1])
        previous = _normalise(seq[-2])
        sim = _jaccard(latest, previous)
        verdict = ConvergenceVerdict(sim >= self.threshold, sim, self.threshold)
        self._history.append(verdict)
        return verdict.converged

    @property
    def history(self) -> tuple[ConvergenceVerdict, ...]:
        return tuple(self._history)
