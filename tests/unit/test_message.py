"""Unit tests for biz_core.framework.message helpers."""

from __future__ import annotations

from biz_core.framework.message import BIZ_MSG_META_KEY, with_biz_metadata


def test_biz_msg_meta_key_is_string() -> None:
    """BIZ_MSG_META_KEY is the canonical key for biz metadata in Msg."""
    assert isinstance(BIZ_MSG_META_KEY, str)
    assert BIZ_MSG_META_KEY == "biz_meta"


def test_with_biz_metadata_attaches_dict() -> None:
    """with_biz_metadata returns a new Msg with biz_meta attached."""
    from agentscope.message import Msg, TextBlock

    base = Msg(
        name="user",
        role="user",
        content=[TextBlock(type="text", text="hello")],
    )
    enriched = with_biz_metadata(base, phase="R1", sample_count=1)
    # Enriched Msg keeps original role/name/text.
    assert enriched.role == "user"
    assert enriched.get_text_content() == "hello"
    assert enriched.metadata[BIZ_MSG_META_KEY] == {
        "phase": "R1",
        "sample_count": 1,
    }
