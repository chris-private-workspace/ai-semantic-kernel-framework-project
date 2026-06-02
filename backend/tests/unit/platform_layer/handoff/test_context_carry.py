"""
File: backend/tests/unit/platform_layer/handoff/test_context_carry.py
Purpose: Unit tests for cap_and_serialize + render_carried_context_block (Sprint 57.69 A-3b)
Category: Tests
Created: 2026-06-02
Modified: 2026-06-02

Verifies the LLM-neutral context-carry helpers: capping/serialization of the
parent conversation (empty/None → []; under/over the last-N cap; str vs
ContentBlock content rendering) and the system-prompt block render (empty → "";
non-empty → header + role/content lines).
"""

from __future__ import annotations

from agent_harness._contracts.chat import ContentBlock, Message
from platform_layer.handoff.context_carry import (
    DEFAULT_MAX_CARRY_MESSAGES,
    cap_and_serialize,
    render_carried_context_block,
)

# === cap_and_serialize =======================================================


def test_cap_and_serialize_none_returns_empty() -> None:
    assert cap_and_serialize(None) == []


def test_cap_and_serialize_empty_returns_empty() -> None:
    assert cap_and_serialize([]) == []


def test_cap_and_serialize_under_budget_keeps_all_in_order() -> None:
    messages = [
        Message(role="user", content="hello"),
        Message(role="assistant", content="hi there"),
        Message(role="user", content="bye"),
    ]
    out = cap_and_serialize(messages)
    assert out == [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi there"},
        {"role": "user", "content": "bye"},
    ]


def test_cap_and_serialize_over_budget_drops_oldest() -> None:
    # 3 messages, cap at 2 → oldest (index 0) dropped, last 2 kept in order.
    messages = [
        Message(role="user", content="first"),
        Message(role="assistant", content="second"),
        Message(role="user", content="third"),
    ]
    out = cap_and_serialize(messages, max_messages=2)
    assert out == [
        {"role": "assistant", "content": "second"},
        {"role": "user", "content": "third"},
    ]


def test_cap_and_serialize_default_cap_drops_oldest() -> None:
    over = DEFAULT_MAX_CARRY_MESSAGES + 3
    messages = [Message(role="user", content=f"m{i}") for i in range(over)]
    out = cap_and_serialize(messages)
    assert len(out) == DEFAULT_MAX_CARRY_MESSAGES
    # Oldest 3 dropped — first kept is original index `over - cap`.
    assert out[0] == {"role": "user", "content": f"m{over - DEFAULT_MAX_CARRY_MESSAGES}"}
    assert out[-1] == {"role": "user", "content": f"m{over - 1}"}


def test_cap_and_serialize_str_content_passthrough() -> None:
    out = cap_and_serialize([Message(role="user", content="plain string")])
    assert out == [{"role": "user", "content": "plain string"}]


def test_cap_and_serialize_block_content_joins_text() -> None:
    content = [
        ContentBlock(type="text", text="line one"),
        ContentBlock(type="image", image_url="http://x/y.png"),  # no .text → skipped
        ContentBlock(type="text", text="line two"),
    ]
    out = cap_and_serialize([Message(role="assistant", content=content)])
    assert out == [{"role": "assistant", "content": "line one\nline two"}]


def test_cap_and_serialize_block_content_all_non_text_empty() -> None:
    content = [ContentBlock(type="image", image_url="http://x/y.png")]
    out = cap_and_serialize([Message(role="assistant", content=content)])
    assert out == [{"role": "assistant", "content": ""}]


# === render_carried_context_block ===========================================


def test_render_empty_returns_empty_string() -> None:
    assert render_carried_context_block([]) == ""


def test_render_non_empty_contains_header_and_lines() -> None:
    carried = [
        {"role": "user", "content": "what is X?"},
        {"role": "assistant", "content": "X is Y"},
    ]
    block = render_carried_context_block(carried)
    assert "## Prior conversation (handed off from the previous agent)" in block
    assert "[user] what is X?" in block
    assert "[assistant] X is Y" in block
    # Header precedes the conversation lines.
    assert block.index("## Prior conversation") < block.index("[user]")
