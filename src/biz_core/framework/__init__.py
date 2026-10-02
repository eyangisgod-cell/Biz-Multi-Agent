"""biz_core.framework: The sole adapter layer for AgentScope 2.0.

This module is the ONLY legal importer of `agentscope.*` symbols.
All business code (agents/, tools/, data/, review/) must import from
`biz_core.framework` rather than touching `agentscope` directly.

Why this layer exists:
- Stable public surface: classes / helpers can be added, renamed, or
  re-exported without touching downstream code.
- Testability: a fake / mock framework layer can be injected during
  unit tests without monkey-patching agentscope internals.
- Versioning: when AgentScope bumps its public API, only this file
  changes — application code stays put.
- Static enforcement: the integration test
  `tests/integration/test_project_structure.py` walks the AST of every
  application submodule and fails if it sees `import agentscope`.

Layered sub-modules (Phase 1.5):
  agent.py       — BizAgent (subclass of agentscope.Agent)
  state.py       — BizAgentState (subclass of agentscope.AgentState)
  tool.py        — BizToolkit (subclass of agentscope.Toolkit)
  middleware.py  — MiddlewareBase + HookAbort (interception channel)
  formatter.py   — BizFormatter (subclass of agentscope.FormatterBase)
  sop.py         — BizSOPEngine + phase constants
  pipeline.py    — BizGoalPipeline (subclass of agentscope.GoalPipeline)
  skill.py       — BizSkillLoader (subclass of agentscope.LocalSkillLoader)
  message.py     — with_biz_metadata() helper
  model.py       — LiteLLMRouter (independent of agentscope)
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# AgentScope 2.0 primitive re-exports.
# Names below mirror the actual AgentScope 2.0.8 public surface.
# If AgentScope renames a class in a future release, only this file changes.
# ---------------------------------------------------------------------------
from agentscope.agent import A2AAgent, Agent, RealtimeAgent
from agentscope.formatter import FormatterBase
from agentscope.message import Msg
from agentscope.middleware import MiddlewareBase
from agentscope.pipeline import GoalPipeline
from agentscope.skill import LocalSkillLoader, Skill
from agentscope.sop import SOP, SOPEngine
from agentscope.state import AgentState, Task
from agentscope.tool import ToolBase, Toolkit

# LiteLLM router lives in this layer but is independent of agentscope —
# it depends only on litellm. Application code accesses it via
# `from biz_core.framework.model import LiteLLMRouter`.
from biz_core.framework import model as model  # noqa: F401

# ---------------------------------------------------------------------------
# Biz-specific extensions (Phase 1.5).
# Application code uses these names rather than the bare AgentScope ones.
# ---------------------------------------------------------------------------
from biz_core.framework.agent import BizAgent
from biz_core.framework.formatter import BizFormatter
from biz_core.framework.message import BIZ_MSG_META_KEY, with_biz_metadata
from biz_core.framework.middleware import HookAbort
from biz_core.framework.pipeline import BizGoalPipeline
from biz_core.framework.skill import BIZ_SKILLS_DIR, BizSkillLoader
from biz_core.framework.sop import PHASE_ADVOCATE, PHASE_OPPONENT, PHASE_REVIEWER, BizSOPEngine
from biz_core.framework.state import BizAgentState
from biz_core.framework.tool import BizToolkit

__all__ = [
    # AgentScope raw re-exports
    "Agent",
    "A2AAgent",
    "RealtimeAgent",
    "Toolkit",
    "ToolBase",
    "AgentState",
    "Task",
    "MiddlewareBase",
    "FormatterBase",
    "SOPEngine",
    "SOP",
    "GoalPipeline",
    "LocalSkillLoader",
    "Skill",
    "Msg",
    # Biz extensions
    "BizAgent",
    "BizAgentState",
    "BizToolkit",
    "BizFormatter",
    "BizSOPEngine",
    "BizGoalPipeline",
    "BizSkillLoader",
    "HookAbort",
    "with_biz_metadata",
    "BIZ_MSG_META_KEY",
    "BIZ_SKILLS_DIR",
    "PHASE_ADVOCATE",
    "PHASE_OPPONENT",
    "PHASE_REVIEWER",
    # Sub-module
    "model",
]
