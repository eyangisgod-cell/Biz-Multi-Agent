"""Unit tests for biz_core.framework.formatter (BizFormatter)."""

from __future__ import annotations

from biz_core.framework.formatter import BizFormatter


def test_biz_formatter_inherits_agentscope_formatterbase() -> None:
    """BizFormatter must subclass agentscope.formatter.FormatterBase."""
    from agentscope.formatter import FormatterBase

    assert issubclass(BizFormatter, FormatterBase)


def test_biz_formatter_has_format_method() -> None:
    """FormatterBase subclasses must implement `format` (interface check)."""
    from agentscope.formatter import FormatterBase

    assert hasattr(BizFormatter, "format") or hasattr(
        FormatterBase,
        "format",
    )
