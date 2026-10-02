"""LiteLLM-backed multi-model router.

Independent of agentscope — depends only on `litellm` + `pydantic`.
Application code imports it as `from biz_core.framework.model import LiteLLMRouter`.
"""

from __future__ import annotations

from typing import Any

try:
    import litellm  # type: ignore[import-not-found, unused-ignore]
except ImportError:  # pragma: no cover - exercised only when litellm missing
    litellm = None  # type: ignore[assignment]


class LiteLLMRouter:
    """Thin wrapper over litellm.completion with primary/fallback models."""

    def __init__(
        self,
        primary_model: str = "claude-sonnet-4-6",
        fallback_models: tuple[str, ...] = ("gpt-5", "gemini-2.5-pro"),
    ) -> None:
        self.primary_model = primary_model
        self.fallback_models = fallback_models

    def complete(self, prompt: str, *, fallback: bool = False) -> Any:
        if litellm is None:  # pragma: no cover
            raise RuntimeError("litellm is not installed")
        models = (
            (self.primary_model, *self.fallback_models)
            if fallback
            else (self.primary_model,)
        )
        last_error: Exception | None = None
        for model in models:
            try:
                return litellm.completion(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                )
            except Exception as exc:  # noqa: BLE001 - intentional catch-all
                last_error = exc
                continue
        raise RuntimeError(f"All models failed: {models}") from last_error
