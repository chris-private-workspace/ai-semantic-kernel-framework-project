"""
File: backend/tests/unit/agent_harness/verification/test_trace_block.py
Purpose: Unit tests for build_trace_block (A3 trace-aware judge input — bounds + rendering).
Category: Tests / Unit / 範疇 10
Scope: Sprint 57.111 (A3)
Created: 2026-06-13

Related:
    - backend/src/agent_harness/verification/_trace.py
"""

from __future__ import annotations

from typing import Any

from agent_harness._contracts.chat import Message, ToolCall
from agent_harness.verification._trace import build_trace_block


def _msg(role: str, content: str, **kw: Any) -> Message:
    return Message(role=role, content=content, **kw)  # type: ignore[arg-type]


def test_empty_messages_returns_empty() -> None:
    assert build_trace_block([]) == ""


def test_system_only_returns_empty() -> None:
    assert build_trace_block([_msg("system", "you are a bot")]) == ""


def test_renders_recent_user_assistant_tool() -> None:
    block = build_trace_block(
        [
            _msg("user", "fetch the data"),
            _msg("assistant", "", tool_calls=[ToolCall(id="t1", name="fetch_data", arguments={})]),
            _msg("tool", "ERROR: connection refused", tool_call_id="t1"),
            _msg("assistant", "Done, fetched successfully."),
        ]
    )
    assert "[user] fetch the data" in block
    assert "[called: fetch_data]" in block  # assistant tool call annotated
    assert "ERROR: connection refused" in block  # the tool error surfaces in the trace
    assert "[tool]" in block


def test_max_messages_keeps_last_n() -> None:
    msgs = [_msg("user", f"m{i}") for i in range(20)]
    block = build_trace_block(msgs, max_messages=3)
    assert "m19" in block and "m18" in block and "m17" in block
    assert "m16" not in block
    assert block.count("\n") == 2  # exactly 3 lines


def test_char_budget_drops_oldest_keeps_tail() -> None:
    msgs = [_msg("user", f"line{i}-" + "X" * 90) for i in range(10)]
    block = build_trace_block(msgs, char_budget=150)
    assert len(block) <= 150
    assert "line9" in block  # the most-recent line is retained
    assert "line0" not in block  # the oldest is dropped


def test_per_message_cap_truncates_long_content() -> None:
    block = build_trace_block([_msg("user", "Y" * 1000)])
    assert "…" in block  # per-message cap ellipsis
    assert len(block) < 1000


def test_max_messages_zero_returns_empty() -> None:
    assert build_trace_block([_msg("user", "hi")], max_messages=0) == ""


def test_char_budget_zero_returns_empty() -> None:
    assert build_trace_block([_msg("user", "hi")], char_budget=0) == ""
