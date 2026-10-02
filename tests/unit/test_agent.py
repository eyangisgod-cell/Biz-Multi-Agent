"""Unit tests for biz_core.framework.agent (BizAgent).

Note: full Agent instantiation requires a real ChatModelBase; here we
test only the class-level contract (subclass, default args, factory).
Application code is expected to pass a real model.
"""

from __future__ import annotations

from biz_core.framework.agent import DEFAULT_SYS_PROMPT, BizAgent


def test_biz_agent_inherits_agentscope_agent() -> None:
    """BizAgent must subclass agentscope.agent.Agent."""
    from agentscope.agent import Agent

    assert issubclass(BizAgent, Agent)


def test_default_sys_prompt_is_non_empty() -> None:
    """DEFAULT_SYS_PROMPT is the sys prompt applied when callers omit it."""
    assert isinstance(DEFAULT_SYS_PROMPT, str)
    assert len(DEFAULT_SYS_PROMPT) > 0


def test_biz_agent_class_exposed_at_module_root() -> None:
    """BizAgent must be importable as `from biz_core.framework.agent import BizAgent`."""
    from biz_core.framework import agent as module

    assert hasattr(module, "BizAgent")
    assert module.BizAgent is BizAgent
