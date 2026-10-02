"""Unit tests for biz_core.agents role agents.

These tests verify the CLASS-LEVEL contract of each role agent
(sys_prompt, subclass relationship, role registration). They do
NOT instantiate agents — that requires a real ChatModelBase and
is exercised in integration tests.
"""

from __future__ import annotations

from biz_core.agents.content_test import ContentTestAgent
from biz_core.agents.merchant_profile import MerchantProfileAgent
from biz_core.agents.pain_point import PainPointAgent
from biz_core.agents.selection import SelectionAgent
from biz_core.agents.self_evolution import SelfEvolutionAgent


def test_pain_point_agent_inherits_biz_agent() -> None:
    """PainPointAgent must subclass biz_core.framework.BizAgent."""
    from biz_core.framework import BizAgent

    assert issubclass(PainPointAgent, BizAgent)


def test_selection_agent_inherits_biz_agent() -> None:
    """SelectionAgent must subclass biz_core.framework.BizAgent."""
    from biz_core.framework import BizAgent

    assert issubclass(SelectionAgent, BizAgent)


def test_content_test_agent_inherits_biz_agent() -> None:
    """ContentTestAgent must subclass biz_core.framework.BizAgent."""
    from biz_core.framework import BizAgent

    assert issubclass(ContentTestAgent, BizAgent)


def test_merchant_profile_agent_inherits_biz_agent() -> None:
    """MerchantProfileAgent must subclass biz_core.framework.BizAgent."""
    from biz_core.framework import BizAgent

    assert issubclass(MerchantProfileAgent, BizAgent)


def test_self_evolution_agent_inherits_biz_agent() -> None:
    """SelfEvolutionAgent must subclass biz_core.framework.BizAgent."""
    from biz_core.framework import BizAgent

    assert issubclass(SelfEvolutionAgent, BizAgent)


def test_each_role_has_distinct_name() -> None:
    """Each role agent class must expose a distinct `name` class attribute."""
    names = {
        PainPointAgent.name,
        SelectionAgent.name,
        ContentTestAgent.name,
        MerchantProfileAgent.name,
        SelfEvolutionAgent.name,
    }
    assert len(names) == 5


def test_each_role_has_sys_prompt() -> None:
    """Each role agent must declare a non-empty sys_prompt class attribute."""
    for cls in (
        PainPointAgent,
        SelectionAgent,
        ContentTestAgent,
        MerchantProfileAgent,
        SelfEvolutionAgent,
    ):
        prompt = getattr(cls, "sys_prompt", "")
        assert isinstance(prompt, str)
        assert len(prompt) > 0
