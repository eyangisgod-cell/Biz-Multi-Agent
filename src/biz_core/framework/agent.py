"""biz_core.framework.agent — BizAgent base for application role agents.

Application role agents (R1 pain_point, R2 selection, R3 content_test,
...) inherit BizAgent and pass their role-specific sys_prompt.
BizAgent itself is just a typed alias for Agent with a known
default sys prompt; no behavioral changes at this layer.
"""

from __future__ import annotations

from agentscope.agent import Agent as _ASAgent

DEFAULT_SYS_PROMPT = (
    "You are an agent in BizForecast-Shop, a multi-agent system for "
    "SMB e-commerce forecasting. Follow your role instructions and "
    "always cite external sources when making claims."
)


class BizAgent(_ASAgent):
    """Adapter subclass — application agents should inherit this."""
