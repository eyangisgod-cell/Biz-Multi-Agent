"""Unit tests for biz_core.agents.convergence."""

from __future__ import annotations

from biz_core.agents.convergence import ConvergenceJudge, is_converged


def test_is_converged_returns_false_for_few_outputs() -> None:
    """With fewer than 2 outputs, convergence is undefined -> False."""
    assert is_converged(["only one"]) is False
    assert is_converged([]) is False


def test_is_converged_returns_false_for_diverse_outputs() -> None:
    """Diverse outputs should NOT converge."""
    outputs = [
        "TikTok is the best platform for gen-z.",
        "We should target eco-conscious millennials.",
        "Price point of $19.99 maximizes conversion.",
    ]
    assert is_converged(outputs) is False


def test_is_converged_returns_true_for_repeated_outputs() -> None:
    """Near-identical outputs should converge."""
    outputs = [
        "TikTok is the best platform for gen-z.",
        "TikTok is the best platform for gen-z.",
    ]
    assert is_converged(outputs) is True


def test_is_converged_accepts_custom_threshold() -> None:
    """A stricter threshold should reject borderline-similar outputs."""
    outputs = [
        "TikTok is the best platform for gen-z.",
        "TikTok is a good platform for gen-z.",
    ]
    # Loose threshold — converges.
    assert is_converged(outputs, threshold=0.5) is True
    # Strict threshold — does not converge.
    assert is_converged(outputs, threshold=0.99) is False


def test_convergence_judge_records_history() -> None:
    """ConvergenceJudge tracks past verdicts for auditability."""
    judge = ConvergenceJudge(threshold=0.85)
    v1 = judge.record(["a b", "a b"])
    v2 = judge.record(["a b", "a b"])
    assert v1 is True
    assert v2 is True


def test_convergence_judge_history_is_readonly() -> None:
    """history property returns a tuple (no accidental mutation)."""
    judge = ConvergenceJudge()
    judge.record(["x", "x"])
    history = judge.history
    assert isinstance(history, tuple)
