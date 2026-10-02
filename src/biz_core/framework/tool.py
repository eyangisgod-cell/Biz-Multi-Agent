"""biz_core.framework.tool — Toolkit adapter with biz conventions.

BizToolkit is currently a thin subclass of agentscope.tool.Toolkit;
it exists so application code can subclass it for shared tool
registration patterns without touching the agentscope import.
"""

from __future__ import annotations

from agentscope.tool import Toolkit as _ASToolkit


class BizToolkit(_ASToolkit):
    """Adapter subclass — application toolkits should inherit this."""
