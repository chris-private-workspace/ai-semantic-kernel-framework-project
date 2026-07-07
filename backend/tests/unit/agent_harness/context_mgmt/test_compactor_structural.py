"""
File: tests/unit/agent_harness/context_mgmt/test_compactor_structural.py
Purpose: Unit tests for StructuralCompactor (impl: compactor/structural.py).
Category: Tests / 範疇 4 (Context Management)
Scope: Sprint 52.1 Day 2.2 · Sprint 57.161 (real token re-count)

9 tests:
  - test_not_triggered_below_threshold
  - test_triggered_by_token_threshold
  - test_triggered_by_turn_count
  - test_preserves_system_message
  - test_preserves_hitl_decisions
  - test_drops_redundant_tool_retry
  - test_realcount_on_tombstone_reflects_reduction (Sprint 57.161 — fix positive)
  - test_no_counter_is_message_count_ratio_blind_to_tombstone (Sprint 57.161 — the fix delta)
  - test_realcount_matches_preclear_reduction (Sprint 57.161 — parity with PreClearCompactor)
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
from agent_harness.context_mgmt.compactor.structural import StructuralCompactor
from agent_harness.context_mgmt.token_counter._abc import TokenCounter

_BLOB = "X" * 500


class _LenCounter(TokenCounter):
    """Deterministic stub: token count = total str-content length (mirrors preclear test)."""

    def count(
        self,
        *,
        messages: list[Message],
        tools: list[ToolSpec] | None = None,
    ) -> int:
        return sum(len(m.content) for m in messages if isinstance(m.content, str))

    def accuracy(self) -> Literal["exact", "approximate"]:
        return "approximate"


def _tool_transcript(n_users: int, *, blob: str = _BLOB) -> list[Message]:
    """n user turns, each: user -> assistant(tool_call, distinct args) -> tool(blob result).

    Distinct args per turn → no redundant-retry drop → the ONLY reduction is the
    masker's in-place tombstoning → len(kept) == original (the case where the
    message-count ratio is blind but a real re-count is not).
    """
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


@pytest.mark.asyncio
async def test_not_triggered_below_threshold() -> None:
    """token < 75% of budget AND turn < 30 → no compaction."""
    compactor = StructuralCompactor(token_budget=100_000)
    state = _make_state(
        messages=[Message(role="user", content="hi")],
        token_used=50_000,
        turn_count=5,
    )

    result = await compactor.compact_if_needed(state)

    assert result.triggered is False
    assert result.strategy_used is None
    assert result.compacted_state is None
    assert result.messages_compacted == 0
    assert result.tokens_after == result.tokens_before


@pytest.mark.asyncio
async def test_triggered_by_token_threshold() -> None:
    """token > 75% of budget triggers compaction."""
    compactor = StructuralCompactor(token_budget=10_000, token_threshold_ratio=0.75)
    state = _make_state(
        messages=[Message(role="user", content=f"q{i}") for i in range(10)],
        token_used=8_000,
        turn_count=3,
    )

    result = await compactor.compact_if_needed(state)

    assert result.triggered is True
    assert result.strategy_used == CompactionStrategy.STRUCTURAL
    assert result.compacted_state is not None
    assert result.duration_ms >= 0


@pytest.mark.asyncio
async def test_triggered_by_turn_count() -> None:
    """turn > 30 triggers even when token usage is low."""
    compactor = StructuralCompactor(token_budget=1_000_000, turn_threshold=30)
    state = _make_state(
        messages=[Message(role="user", content=f"u{i}") for i in range(40)],
        token_used=10_000,
        turn_count=35,
    )

    result = await compactor.compact_if_needed(state)

    assert result.triggered is True
    assert result.strategy_used == CompactionStrategy.STRUCTURAL


@pytest.mark.asyncio
async def test_preserves_system_message() -> None:
    """role=system messages must always survive compaction."""
    sys_msg = Message(role="system", content="You are a helpful assistant.")
    other = [Message(role="user", content=f"q{i}") for i in range(20)]
    compactor = StructuralCompactor(token_budget=1_000, keep_recent_turns=3)
    state = _make_state(
        messages=[sys_msg, *other],
        token_used=900,
        turn_count=20,
    )

    result = await compactor.compact_if_needed(state)

    assert result.triggered is True
    assert result.compacted_state is not None
    kept = result.compacted_state.transient.messages
    assert any(m.role == "system" and m.content == sys_msg.content for m in kept)


@pytest.mark.asyncio
async def test_preserves_hitl_decisions() -> None:
    """metadata['hitl']=True messages must survive compaction."""
    hitl_msg = Message(
        role="assistant",
        content="approval recorded",
        metadata={"hitl": True},
    )
    other = [Message(role="user", content=f"u{i}") for i in range(40)]
    compactor = StructuralCompactor(token_budget=1_000, preserve_hitl=True)
    state = _make_state(
        messages=[*other[:20], hitl_msg, *other[20:]],
        token_used=950,
        turn_count=41,
    )

    result = await compactor.compact_if_needed(state)

    assert result.triggered is True
    assert result.compacted_state is not None
    kept = result.compacted_state.transient.messages
    assert any(m.metadata.get("hitl") is True for m in kept)


@pytest.mark.asyncio
async def test_drops_redundant_tool_retry() -> None:
    """Same (tool_name, args_hash) appearing twice → only the latest pair survives."""
    compactor = StructuralCompactor(token_budget=1_000, turn_threshold=0)

    tool_call_args = {"q": "select 1"}
    msgs = [
        Message(role="user", content="please query"),
        Message(
            role="assistant",
            content="",
            tool_calls=[ToolCall(id="c1", name="db_query", arguments=tool_call_args)],
        ),
        Message(role="tool", content="error: timeout", tool_call_id="c1", name="db_query"),
        Message(
            role="assistant",
            content="",
            tool_calls=[ToolCall(id="c2", name="db_query", arguments=tool_call_args)],
        ),
        Message(role="tool", content="ok: [1]", tool_call_id="c2", name="db_query"),
        Message(role="assistant", content="result is 1"),
    ]
    state = _make_state(messages=msgs, token_used=900, turn_count=4)

    result = await compactor.compact_if_needed(state)

    assert result.triggered is True
    assert result.compacted_state is not None
    kept = result.compacted_state.transient.messages

    db_query_calls = [
        m for m in kept if m.tool_calls and any(tc.name == "db_query" for tc in m.tool_calls)
    ]
    assert len(db_query_calls) == 1
    assert db_query_calls[0].tool_calls is not None
    assert db_query_calls[0].tool_calls[0].id == "c2"


# === Sprint 57.161: real token re-count (closes AD-Compaction-Structural-RealTokenCount) ===


@pytest.mark.asyncio
async def test_realcount_on_tombstone_reflects_reduction() -> None:
    """With a TokenCounter injected, in-place tombstoning surfaces a REAL reduction
    (tokens_after < tokens_before) even though the message COUNT is unchanged."""
    counter = _LenCounter()
    compactor = StructuralCompactor(
        keep_recent_turns=5,
        token_budget=1_000,
        token_threshold_ratio=0.75,
        token_counter=counter,
    )
    messages = _tool_transcript(7)  # 7 user turns > keep_recent 5 → masking fires
    state = _make_state(messages, token_used=900, turn_count=7)

    result = await compactor.compact_if_needed(state)

    assert result.triggered is True
    assert result.compacted_state is not None
    kept = result.compacted_state.transient.messages
    # ONLY tombstoning happened (distinct args → no drop) → message count preserved.
    assert len(kept) == len(messages)
    # ...yet real tokens dropped, so tokens_after moved below tokens_before.
    assert result.tokens_after < result.tokens_before
    assert any("[REDACTED" in m.content for m in kept if isinstance(m.content, str))


@pytest.mark.asyncio
async def test_no_counter_is_message_count_ratio_blind_to_tombstone() -> None:
    """THE FIX DELTA: without a counter, the message-count ratio reports tokens_after
    == tokens_before on the SAME tombstoned transcript (len unchanged → ratio 1.0) —
    the 57.159 no-op the counter fixes. Proves the counter is what changed the behaviour."""
    compactor = StructuralCompactor(
        keep_recent_turns=5,
        token_budget=1_000,
        token_threshold_ratio=0.75,
        # token_counter=None (default) → legacy message-count ratio
    )
    messages = _tool_transcript(7)
    state = _make_state(messages, token_used=900, turn_count=7)

    result = await compactor.compact_if_needed(state)

    assert result.triggered is True
    assert result.compacted_state is not None
    kept = result.compacted_state.transient.messages
    assert len(kept) == len(messages)  # tombstone-only → count preserved
    # message-count ratio = len(kept)/original = 1.0 → blind no-op (the bug).
    assert result.tokens_after == result.tokens_before


@pytest.mark.asyncio
async def test_realcount_matches_preclear_reduction() -> None:
    """PARITY (AC-2): structural-with-counter's tokens_after equals PreClearCompactor's
    on the same tombstoned input — both use int(tokens_before * masked/original)."""
    counter = _LenCounter()
    messages = _tool_transcript(7)
    token_used = 900

    structural = StructuralCompactor(
        keep_recent_turns=5,
        token_budget=1_000,
        token_threshold_ratio=0.75,
        token_counter=counter,
    )
    preclear = PreClearCompactor(
        token_counter=counter,
        preclear_ratio=0.50,
        keep_recent_turns=5,
        token_budget=1_000,
    )
    s_result = await structural.compact_if_needed(_make_state(messages, token_used=token_used))
    p_result = await preclear.compact_if_needed(_make_state(messages, token_used=token_used))

    assert s_result.triggered is True
    assert p_result.triggered is True
    # Same masker + same keep_recent + same counter + same tokens_before → same ratio.
    assert s_result.tokens_after == p_result.tokens_after
    # And it equals the documented preclear formula computed directly.
    original = counter.count(messages=messages)
    assert s_result.compacted_state is not None
    masked = counter.count(messages=s_result.compacted_state.transient.messages)
    assert s_result.tokens_after == int(token_used * (masked / original))
