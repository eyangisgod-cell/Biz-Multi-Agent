"""biz_core.framework.formatter — Formatter adapter.

BizFormatter is a thin subclass of agentscope.formatter.FormatterBase;
real per-platform formatters (TikTok / Shopify / 1688) will live in
the application layer and inherit this base.
"""

from __future__ import annotations

from agentscope.formatter import FormatterBase as _ASFormatterBase


class BizFormatter(_ASFormatterBase):
    """Adapter subclass — application formatters should inherit this."""
