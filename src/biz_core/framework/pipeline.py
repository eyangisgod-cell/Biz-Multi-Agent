"""biz_core.framework.pipeline — Pipeline adapter.

BizGoalPipeline is a thin subclass of agentscope.pipeline.GoalPipeline.
Real pipelines (R1->R9 orchestrator, evaluation harness, ...) will
inherit this base and configure their own goal / step sequence.
"""

from __future__ import annotations

from agentscope.pipeline import GoalPipeline as _ASGoalPipeline


class BizGoalPipeline(_ASGoalPipeline):
    """Adapter subclass — application pipelines should inherit this."""
