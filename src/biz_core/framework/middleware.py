"""biz_core.framework.middleware — Hook layer with intercept semantics.

Contract:
  Middleware subclasses either return None (pass-through) OR raise
  HookAbort (intercept).  Callers see the exception and decide
  whether to regenerate, escalate, or stop.

This mirrors AgentScope 2.0's MiddlewareBase but adds a typed
interruption channel (`HookAbort`) so biz_core code can branch on
the reason (echo_detected, compliance_violation, ...) instead of
inspecting strings.

Hook budget (per design §12.5, evaluated and tightened by sub-agents):
  business       <= 3   (echo prevention + 5 objection categories + convergence)
  observability  <= 2   (OTel span + Langfuse trace)
  compliance     <= 1   (data redaction / cross-tenant guard)
  TOTAL          <= 6
"""

from __future__ import annotations

from agentscope.middleware import MiddlewareBase as _ASMiddlewareBase


class HookAbort(Exception):  # noqa: N818 - design-doc mandated name
    """Raised by a middleware to abort the current step.

    Attributes:
        reason: machine-readable category, e.g. "echo_detected",
            "compliance_violation", "convergence_fail".
        suggestion: human-readable hint for callers — typically
            describes the recovery action, e.g. "regenerate_with_external".
    """

    def __init__(self, reason: str, suggestion: str = "") -> None:
        super().__init__(f"HookAbort(reason={reason!r}, suggestion={suggestion!r})")
        self.reason = reason
        self.suggestion = suggestion


class MiddlewareBase(_ASMiddlewareBase):
    """Adapter subclass — semantic anchor for pass-through / intercept.

    Subclasses override hooks (e.g. `on_message`) and either return
    None or raise HookAbort.  No other return value is meaningful.
    """
