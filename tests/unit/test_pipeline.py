"""Unit tests for biz_core.framework.pipeline (BizGoalPipeline)."""

from __future__ import annotations

from biz_core.framework.pipeline import BizGoalPipeline


def test_biz_goal_pipeline_inherits_agentscope_pipeline() -> None:
    """BizGoalPipeline must subclass agentscope.pipeline.GoalPipeline."""
    from agentscope.pipeline import GoalPipeline

    assert issubclass(BizGoalPipeline, GoalPipeline)


def test_biz_goal_pipeline_exposes_reply_stream() -> None:
    """BizGoalPipeline inherits the streaming reply surface from
    agentscope.pipeline.GoalPipeline (Protocol class itself is not
    @runtime_checkable, so we assert on the concrete method instead)."""
    assert hasattr(BizGoalPipeline, "reply_stream")
