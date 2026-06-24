"""
File: tests/unit/agent_harness/context_mgmt/test_compactor_preclear.py
Purpose: Unit tests for PreClearCompactor (impl: compactor/preclear.py).
Category: Tests / 範疇 4 (Context Management)
Scope: Sprint 57.139 (#4 layered compaction)

8 tests:
  - test_not_triggered_below_preclear_ratio
  - test_triggers_earlier_than_structural_threshold
  - test_masks_old_tool_results_when_enough_user_turns
  - test_noop_when_too_few_user_turns (the user-anchored NO-OP finding)
  - test_preserves_system_message
  - test_preserves_hitl_tool_result
  - test_tokens_after_reflects_real_reduction_ratio
  - test_strategy_is_structural (reuse, no new wire enum)
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import uuid4

import pytest

from agent_harness._contracts import (
    CompactionStrategy,
    DurableState,
    LoopState,
    Message,
    StateVersion,
    ToolCall,
    ToolSpec,
    TransientState,
)
from agent_harness.context_mgmt.compactor.preclear import PreClearCompactor
from agent_harness.context_mgmt.token_counter._abc import TokenCounter

_BLOB = "X" * 500


class _LenCounter(TokenCounter):
    """Deterministic stub: token count = total str-content length."""

    def count(
        self,
        *,
        messages: list[Message],
        tools: list[ToolSpec] | None = None,
    ) -> int:
        return sum(len(m.content) for m in messages if isinstance(m.content, str))

    def accuracy(self) -> Literal["exact", "approximate"]:
        return "approximate"


def _make_state(
    messages: list[Message],
    *,
    token_used: int = 0,
    turn_count: int = 0,
) -> LoopState:
    return LoopState(
        transient=TransientState(
            messages=messages,
            current_turn=turn_count,
            token_usage_so_far=token_used,
        ),
        durable=DurableState(session_id=uuid4(), tenant_id=uuid4()),
        version=StateVersion(
            version=1,
            parent_version=None,
            created_at=datetime.now(),
            created_by_category="orchestrator_loop",
        ),
    )


def _tool_transcript(n_users: int, *, blob: str = _BLOB) -> list[Message]:
    """n user turns, each: user -> assistant(tool_call) -> tool(blob result)."""
    msgs: list[Message] = []
    for i in range(n_users):
        msgs.append(Message(role="user", content=f"u{i}"))
        msgs.append(
            Message(
                role="assistant",
                content="",
                tool_calls=[ToolCall(id=f"c{i}", name="t", arguments={"i": i})],
            )
        )
        msgs.append(Message(role="tool", content=blob, tool_call_id=f"c{i}", name="t"))
    return msgs


def _counter() -> _LenCounter:
    return _LenCounter()


@pytest.mark.asyncio
async def test_not_triggered_below_preclear_ratio() -> None:
    """token <= preclear_ratio*budget → passthrough (no work)."""
    compactor = PreClearCompactor(token_counter=_counter(), preclear_ratio=0.50, token_budget=1_000)
    state = _make_state(_tool_transcript(7), token_used=400)  # 400 <= 500

    result = await compactor.compact_if_needed(state)

    assert result.triggered is False
    assert result.compacted_state is None
    assert result.messages_compacted == 0
    assert result.tokens_after == result.tokens_before


@pytest.mark.asyncio
async def test_triggers_earlier_than_structural_threshold() -> None:
    """At ratio 0.50 the preclear fires at 0.60*budget — where structural (0.75) would not."""
    compactor = PreClearCompactor(token_counter=_counter(), preclear_ratio=0.50, token_budget=1_000)
    state = _make_state(_tool_transcript(7), token_used=600)  # 0.60 budget

    assert compactor.should_compact(state) is True


@pytest.mark.asyncio
async def test_masks_old_tool_results_when_enough_user_turns() -> None:
    """> keep_recent user turns → old tool results tombstoned; tokens drop."""
    compactor = PreClearCompactor(
        token_counter=_counter(),
        preclear_ratio=0.50,
        keep_recent_turns=5,
        token_budget=1_000,
    )
    state = _make_state(_tool_transcript(7), token_used=600)

    result = await compactor.compact_if_needed(state)

    assert result.triggered is True
    assert result.messages_compacted >= 1  # at least one old tool result tombstoned
    assert result.compacted_state is not None
    assert result.tokens_after < result.tokens_before  # real reduction reflected
    kept = result.compacted_state.transient.messages
    assert any("[REDACTED" in m.content for m in kept if isinstance(m.content, str))


@pytest.mark.asyncio
async def test_noop_when_too_few_user_turns() -> None:
    """KEY (D-masker-user-anchored): over threshold but <= keep_recent user turns →
    masker NO-OPs → honest passthrough, NOT a no-op 'triggered' event."""
    compactor = PreClearCompactor(
        token_counter=_counter(),
        preclear_ratio=0.50,
        keep_recent_turns=5,
        token_budget=1_000,
    )
    state = _make_state(_tool_transcript(3), token_used=900)  # over threshold, 3 user turns

    result = await compactor.compact_if_needed(state)

    assert result.triggered is False
    assert result.messages_compacted == 0
    assert result.compacted_state is None


@pytest.mark.asyncio
async def test_preserves_system_message() -> None:
    """role=system survives un-tombstoned even when old."""
    sys_msg = Message(role="system", content="You are helpful.")
    compactor = PreClearCompactor(
        token_counter=_counter(),
        preclear_ratio=0.50,
        keep_recent_turns=5,
        token_budget=1_000,
    )
    state = _make_state([sys_msg, *_tool_transcript(7)], token_used=600)

    result = await compactor.compact_if_needed(state)

    assert result.triggered is True
    assert result.compacted_state is not None
    kept = result.compacted_state.transient.messages
    assert any(m.role == "system" and m.content == sys_msg.content for m in kept)


@pytest.mark.asyncio
async def test_preserves_hitl_tool_result() -> None:
    """An old metadata['hitl']=True tool result is preserved (not tombstoned)."""
    hitl_tool = Message(
        role="tool",
        content="APPROVED-PAYLOAD",
        tool_call_id="hitl1",
        name="approve",
        metadata={"hitl": True},
    )
    # hitl tool placed at the very front (old) among 7 user turns
    compactor = PreClearCompactor(
        token_counter=_counter(),
        preclear_ratio=0.50,
        keep_recent_turns=5,
        preserve_hitl=True,
        token_budget=1_000,
    )
    state = _make_state([hitl_tool, *_tool_transcript(7)], token_used=600)

    result = await compactor.compact_if_needed(state)

    assert result.triggered is True
    assert result.compacted_state is not None
    kept = result.compacted_state.transient.messages
    assert any(m.content == "APPROVED-PAYLOAD" for m in kept if isinstance(m.content, str))


@pytest.mark.asyncio
async def test_tokens_after_reflects_real_reduction_ratio() -> None:
    """tokens_after = int(tokens_before * masked/original) — loop-scale, real ratio
    (NOT the message-count ratio that would leave masking-only reduction invisible)."""
    counter = _counter()
    compactor = PreClearCompactor(
        token_counter=counter,
        preclear_ratio=0.50,
        keep_recent_turns=5,
        token_budget=1_000,
    )
    messages = _tool_transcript(7)
    state = _make_state(messages, token_used=600)

    result = await compactor.compact_if_needed(state)

    assert result.triggered is True
    assert result.compacted_state is not None
    original = counter.count(messages=messages)
    masked = counter.count(messages=result.compacted_state.transient.messages)
    expected = int(600 * (masked / original))
    assert result.tokens_after == expected
    assert masked < original  # message COUNT unchanged but token count dropped


@pytest.mark.asyncio
async def test_strategy_is_structural() -> None:
    """preclear reports STRUCTURAL (reuse — no new wire enum per D-compaction-strategy-wire)."""
    compactor = PreClearCompactor(
        token_counter=_counter(), preclear_ratio=0.50, keep_recent_turns=5, token_budget=1_000
    )
    state = _make_state(_tool_transcript(7), token_used=600)

    result = await compactor.compact_if_needed(state)

    assert result.strategy_used == CompactionStrategy.STRUCTURAL
