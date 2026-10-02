"""Unit tests for biz_core.framework.middleware.

Contract: Hook semantic is split into two pieces:
1. Middleware classes (extending agentscope.middleware.MiddlewareBase)
   return None to pass through, OR raise HookAbort to intercept.
2. HookAbort carries a `reason` string + optional `suggestion` for
   callers to decide whether to regenerate, escalate, or stop.
"""

from __future__ import annotations

import pytest

from biz_core.framework.middleware import HookAbort, MiddlewareBase


class PassThroughMiddleware(MiddlewareBase):
    """A trivial middleware that always returns None."""

    async def on_message(self, message):  # type: ignore[no-untyped-def]
        return None  # pass-through


class AbortMiddleware(MiddlewareBase):
    """A trivial middleware that always raises HookAbort."""

    async def on_message(self, message):  # type: ignore[no-untyped-def]
        raise HookAbort(reason="echo_detected", suggestion="regenerate")


def test_hookabort_carries_reason_and_suggestion() -> None:
    """HookAbort must carry structured reason + suggestion for callers."""
    exc = HookAbort(reason="echo_detected", suggestion="regenerate_with_external")

    assert exc.reason == "echo_detected"
    assert exc.suggestion == "regenerate_with_external"
    assert "echo_detected" in str(exc)


def test_hookabort_default_suggestion_is_empty() -> None:
    """When suggestion omitted, it defaults to empty string."""
    exc = HookAbort(reason="compliance_violation")
    assert exc.suggestion == ""


def test_middleware_none_return_means_pass_through() -> None:
    """A middleware that returns None signals pass-through to the caller."""
    import asyncio

    mw = PassThroughMiddleware()
    result = asyncio.run(mw.on_message("hello"))
    assert result is None


def test_middleware_can_raise_hookabort_to_intercept() -> None:
    """A middleware that raises HookAbort signals intercept."""
    import asyncio

    mw = AbortMiddleware()
    with pytest.raises(HookAbort) as exc_info:
        asyncio.run(mw.on_message("hello"))

    assert exc_info.value.reason == "echo_detected"


def test_middleware_inherits_agentscope_middlewarebase() -> None:
    """The framework MiddlewareBase must subclass agentscope's MiddlewareBase."""
    from agentscope.middleware import MiddlewareBase as ASMiddlewareBase

    assert issubclass(MiddlewareBase, ASMiddlewareBase)
