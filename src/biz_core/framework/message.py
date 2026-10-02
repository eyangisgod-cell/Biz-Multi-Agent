"""biz_core.framework.message — Msg helpers.

Provides a single attachment key (BIZ_MSG_META_KEY) so application
code can stash phase / sample_count / error info onto a Msg without
inventing ad-hoc metadata keys per role.
"""

from __future__ import annotations

from typing import Any

from agentscope.message import Msg as _ASMsg

BIZ_MSG_META_KEY = "biz_meta"


def with_biz_metadata(msg: _ASMsg, **fields: Any) -> _ASMsg:
    """Return a copy of `msg` with biz_meta attached.

    Existing biz_meta entries are merged (new fields win on conflict).
    Non-biz metadata is preserved as-is.
    """
    merged = dict(msg.metadata) if msg.metadata else {}
    existing = dict(merged.get(BIZ_MSG_META_KEY, {}))
    existing.update(fields)
    merged[BIZ_MSG_META_KEY] = existing
    return msg.model_copy(update={"metadata": merged})
