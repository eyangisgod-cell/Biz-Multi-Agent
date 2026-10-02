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

__all__ = [
    # Agent base classes
    "Agent",
    "A2AAgent",
    "RealtimeAgent",
    # Tools
    "Toolkit",
    "ToolBase",
    # State / memory
    "AgentState",
    "Task",
    # Middleware (replaces the originally-proposed "Hook" semantics)
    "MiddlewareBase",
    # Output formatting
    "FormatterBase",
    # Multi-agent roundtable (replaces MsgHub for SOP-style flows)
    "SOPEngine",
    "SOP",
    # Pipeline orchestration
    "GoalPipeline",
    # Skill hot-loading
    "LocalSkillLoader",
    "Skill",
    # Message envelope
    "Msg",
    # Sub-module
    "model",
]
