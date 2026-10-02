"""Unit tests for biz_core.framework.tool (BizToolkit)."""

from __future__ import annotations

from biz_core.framework.tool import BizToolkit


def test_biz_toolkit_inherits_agentscope_toolkit() -> None:
    """BizToolkit must subclass agentscope.tool.Toolkit."""
    from agentscope.tool import Toolkit

    assert issubclass(BizToolkit, Toolkit)


def test_biz_toolkit_default_construction() -> None:
    """BizToolkit() must construct without arguments."""
    toolkit = BizToolkit()
    assert isinstance(toolkit, BizToolkit)


def test_biz_toolkit_empty_by_default() -> None:
    """A fresh BizToolkit should not yet expose any tool schemas."""
    import asyncio

    toolkit = BizToolkit()
    schemas = asyncio.run(toolkit.get_tool_schemas())
    assert schemas == []
