"""Phase 0 structural tests.

Contract:
- AgentScope is editable-installed from E:/my-project/agentscope (NOT a copy)
- biz_core has a framework layer that re-exports curated AgentScope symbols
- Application layers (agents/, tools/, data/, review/) MUST NOT import agentscope directly
- All 9 AgentScope 2.0 modules are reachable through biz_core.framework
"""

from __future__ import annotations

import ast
from pathlib import Path


def test_agentscope_imports_from_editable_install() -> None:
    """Verify AgentScope loads from editable local install, not PyPI."""
    import agentscope

    assert "E:/my-project/agentscope" in agentscope.__file__.replace(
        "\\",
        "/",
    ), f"agentscope must be editable-installed from local path, got {agentscope.__file__}"


def test_biz_core_has_framework_layer() -> None:
    """Verify biz_core.framework re-exports curated AgentScope primitives
    and biz-specific extensions."""
    import biz_core.framework as fw

    expected = {
        # AgentScope raw re-exports
        "Agent",
        "Toolkit",
        "ToolBase",
        "AgentState",
        "MiddlewareBase",
        "FormatterBase",
        "SOPEngine",
        "SOP",
        "GoalPipeline",
        "LocalSkillLoader",
        "Skill",
        "Msg",
        # Phase 1.5 biz extensions
        "BizAgent",
        "BizAgentState",
        "BizToolkit",
        "BizFormatter",
        "BizSOPEngine",
        "BizGoalPipeline",
        "BizSkillLoader",
        "HookAbort",
        "with_biz_metadata",
    }
    missing = expected - set(dir(fw))
    assert not missing, f"biz_core.framework missing re-exports: {missing}"


def test_framework_layer_does_not_import_agentscope_outside() -> None:
    """Verify application layers don't directly import agentscope.

    The framework layer is the ONLY legal importer of agentscope.
    AST scanning of biz_core/{agents,tools,data,review,router,telemetry,prediction}
    must find no `import agentscope` or `from agentscope...` statements.
    """
    repo_root = Path(__file__).resolve().parents[2]
    src_root = repo_root / "src" / "biz_core"
    forbidden_subdirs = {
        "agents",
        "tools",
        "data",
        "review",
        "router",
        "telemetry",
        "prediction",
    }

    violations: list[tuple[Path, int, str]] = []
    for sub in forbidden_subdirs:
        for py_file in (src_root / sub).rglob("*.py"):
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name == "agentscope" or alias.name.startswith(
                            "agentscope."
                        ):
                            violations.append((py_file, node.lineno, alias.name))
                elif isinstance(node, ast.ImportFrom) and node.module:
                    if node.module == "agentscope" or node.module.startswith(
                        "agentscope."
                    ):
                        violations.append(
                            (py_file, node.lineno, node.module),
                        )

    assert not violations, (
        f"Application layers must not import agentscope directly. "
        f"Violations: {[(str(p), ln, m) for p, ln, m in violations]}"
    )


def test_real_agentscope_modules_available() -> None:
    """Verify all 9 AgentScope 2.0 modules referenced by design are importable."""
    from agentscope.agent import A2AAgent, Agent
    from agentscope.formatter import FormatterBase
    from agentscope.message import Msg
    from agentscope.middleware import MiddlewareBase
    from agentscope.pipeline import GoalPipeline
    from agentscope.skill import LocalSkillLoader, Skill
    from agentscope.sop import SOP, SOPEngine
    from agentscope.state import AgentState, Task
    from agentscope.tool import ToolBase, Toolkit

    assert all(
        [
            Agent,
            A2AAgent,
            Toolkit,
            ToolBase,
            AgentState,
            Task,
            MiddlewareBase,
            FormatterBase,
            SOPEngine,
            SOP,
            GoalPipeline,
            LocalSkillLoader,
            Skill,
            Msg,
        ],
    )
