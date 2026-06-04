"""
File: tests/unit/agent_harness/prompt_builder/test_builder_tool_adjacency.py
Purpose: Unit tests for DefaultPromptBuilder._enforce_tool_adjacency (Cat 5) +
    build()-through-LostInMiddleStrategy tool-turn assembly.
Category: Tests / Cat 5
Scope: Sprint 57.80

Description:
    Regression coverage for AD-Chat-RealLLM-Orphan-Tool-Message. LostInMiddleStrategy
    moves recent assistant messages to the tail while their tool results stay in
    mid-history, orphaning the tool (real_llm chat 400 "messages[N] role 'tool' must
    follow tool_calls"). The builder enforces the provider hard-constraint with a
    single post-arrange() pass. These tests assert the structural invariant directly
    (the MockChatClient never validated adjacency → AP-10 gap that hid this until
    real Azure in Sprint 57.79 Day-3).

Created: 2026-06-04 (Sprint 57.80)
Modified: 2026-06-04
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from agent_harness._contracts import Message, ToolCall
from agent_harness.prompt_builder.builder import DefaultPromptBuilder
from tests.unit.agent_harness.prompt_builder.conftest import make_state

_enforce = DefaultPromptBuilder._enforce_tool_adjacency


def _assistant(tool_call_ids: list[str], content: str = "") -> Message:
    return Message(
        role="assistant",
        content=content,
        tool_calls=[ToolCall(id=i, name="echo_tool", arguments={}) for i in tool_call_ids],
    )


def _tool(tool_call_id: str, content: str = "ok") -> Message:
    return Message(role="tool", content=content, tool_call_id=tool_call_id)


def _idx(messages: list[Message], predicate) -> int:
    return next(i for i, m in enumerate(messages) if predicate(m))


# ---------------------------------------------------------------------------
# (a)-(e): _enforce_tool_adjacency direct unit cases
# ---------------------------------------------------------------------------


def test_tool_already_after_assistant_unchanged() -> None:
    """(a) tool already directly after its assistant → order preserved."""
    sys = Message(role="system", content="s")
    asst = _assistant(["c1"])
    tool = _tool("c1")
    out = _enforce([sys, asst, tool])
    assert out == [sys, asst, tool]


def test_tool_before_assistant_reanchored() -> None:
    """(b) the bug shape — tool ahead of its assistant → re-anchored after it."""
    sys = Message(role="system", content="s")
    asst = _assistant(["c1"])
    tool = _tool("c1")
    # LostInMiddle-style: tool stranded in mid-history, assistant at the tail.
    out = _enforce([sys, tool, asst])
    a_idx = _idx(out, lambda m: m.role == "assistant")
    t_idx = _idx(out, lambda m: m.role == "tool")
    assert t_idx == a_idx + 1
    assert out[t_idx] is tool and out[a_idx] is asst


def test_two_assistants_scrambled_each_tool_after_own_assistant() -> None:
    """(c) two assistants, tools scrambled → each tool follows its OWN assistant."""
    asst_a = _assistant(["a1"])
    asst_b = _assistant(["b1"])
    tool_a = _tool("a1", "ra")
    tool_b = _tool("b1", "rb")
    out = _enforce([asst_a, asst_b, tool_b, tool_a])
    assert out == [asst_a, tool_a, asst_b, tool_b]


def test_orphan_tool_left_in_place() -> None:
    """(d) a tool whose tool_call_id resolves to no assistant is NOT dropped."""
    asst = _assistant(["a1"])
    tool_ok = _tool("a1")
    orphan = _tool("does-not-exist")
    out = _enforce([asst, tool_ok, orphan])
    # valid pair stays adjacent; orphan kept (never silently lose a message)
    assert asst in out and tool_ok in out and orphan in out
    assert len(out) == 3
    a_idx = _idx(out, lambda m: m is asst)
    assert out[a_idx + 1] is tool_ok


def test_no_tool_messages_returns_same_list() -> None:
    """(e) no tool turn → no-op (same list object, zero overhead for plain chat)."""
    msgs = [
        Message(role="system", content="s"),
        Message(role="user", content="hi"),
        Message(role="assistant", content="hello"),  # no tool_calls
    ]
    out = _enforce(msgs)
    assert out is msgs


# ---------------------------------------------------------------------------
# build() through the default LostInMiddleStrategy (the real_llm chat path)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_build_through_lost_in_middle_keeps_tool_after_assistant(
    builder: DefaultPromptBuilder,
) -> None:
    """A [system, user, assistant(tool_calls), tool] conversation assembled via the
    default LostInMiddleStrategy emits a tool message directly after its assistant —
    the exact case that 400s on real Azure before the fix."""
    asst = _assistant(["c1"], content="")
    tool = _tool("c1", "hello")
    state = make_state(
        messages=[
            Message(role="system", content="sys"),
            Message(role="user", content="echo hello"),
            asst,
            tool,
        ]
    )

    artifact = await builder.build(state=state, tenant_id=uuid4(), tools=[])

    a_idx = _idx(artifact.messages, lambda m: m.role == "assistant" and m.tool_calls)
    t_idx = _idx(artifact.messages, lambda m: m.role == "tool")
    assert t_idx == a_idx + 1, (
        "tool must immediately follow its assistant(tool_calls) after build(); "
        f"got assistant@{a_idx}, tool@{t_idx}"
    )
