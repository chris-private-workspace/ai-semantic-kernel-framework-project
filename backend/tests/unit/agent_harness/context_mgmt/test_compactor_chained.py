"""
File: tests/unit/agent_harness/context_mgmt/test_compactor_chained.py
Purpose: Unit tests for ChainedCompactor (impl: compactor/chained.py).
Category: Tests / 範疇 4 (Context Management)
Scope: Sprint 57.139 (#4 layered compaction)

7 tests:
  - test_empty_raises
  - test_single_child_passthrough_equivalence
  - test_no_trigger_returns_passthrough
  - test_threads_state_to_next_child (the defer-semantic mechanism)
  - test_merges_messages_compacted
  - test_strategy_is_last_triggered
  - test_carries_llm_usage_from_later_stage
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from uuid import uuid4

import pytest

from agent_harness._contracts import (
    CompactionResult,
    CompactionStrategy,
    DurableState,
    LoopState,
    Message,
    StateVersion,
    TraceContext,
    TransientState,
)
from agent_harness.context_mgmt.compactor._abc import Compactor
from agent_harness.context_mgmt.compactor.chained import ChainedCompactor


def _make_state(token_used: int, *, n_msgs: int = 4) -> LoopState:
    return LoopState(
        transient=TransientState(
            messages=[Message(role="user", content=f"m{i}") for i in range(n_msgs)],
            current_turn=0,
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


class _StubCompactor(Compactor):
    """Controllable stub: triggers or not, sets a fixed tokens_after, records the
    token_usage_so_far it was handed (to prove the chain threads state forward)."""

    def __init__(
        self,
        *,
        triggers: bool,
        tokens_after: int = 0,
        messages_compacted: int = 0,
        strategy: CompactionStrategy | None = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        model: str = "",
        drop_one: bool = False,
    ) -> None:
        self._triggers = triggers
        self._tokens_after = tokens_after
        self._messages_compacted = messages_compacted
        self._strategy = strategy
        self._input_tokens = input_tokens
        self._output_tokens = output_tokens
        self._model = model
        self._drop_one = drop_one
        self.received_token_usage: int | None = None

    def should_compact(self, state: LoopState) -> bool:
        return self._triggers

    async def compact_if_needed(
        self,
        state: LoopState,
        *,
        trace_context: TraceContext | None = None,
    ) -> CompactionResult:
        self.received_token_usage = state.transient.token_usage_so_far
        if not self._triggers:
            return CompactionResult(
                triggered=False,
                strategy_used=None,
                tokens_before=state.transient.token_usage_so_far,
                tokens_after=state.transient.token_usage_so_far,
                messages_compacted=0,
                duration_ms=0.0,
                compacted_state=None,
            )
        new_messages = list(state.transient.messages)
        if self._drop_one and new_messages:
            new_messages = new_messages[1:]
        new_transient = replace(
            state.transient, messages=new_messages, token_usage_so_far=self._tokens_after
        )
        new_state = replace(state, transient=new_transient)
        return CompactionResult(
            triggered=True,
            strategy_used=self._strategy,
            tokens_before=state.transient.token_usage_so_far,
            tokens_after=self._tokens_after,
            messages_compacted=self._messages_compacted,
            duration_ms=0.0,
            compacted_state=new_state,
            input_tokens=self._input_tokens,
            output_tokens=self._output_tokens,
            model=self._model,
        )


def test_empty_raises() -> None:
    with pytest.raises(ValueError):
        ChainedCompactor(compactors=[])


@pytest.mark.asyncio
async def test_single_child_passthrough_equivalence() -> None:
    """One triggering child → chained mirrors that child's result."""
    child = _StubCompactor(
        triggers=True, tokens_after=300, messages_compacted=2, strategy=CompactionStrategy.HYBRID
    )
    chained = ChainedCompactor(compactors=[child])

    result = await chained.compact_if_needed(_make_state(1_000))

    assert result.triggered is True
    assert result.tokens_after == 300
    assert result.messages_compacted == 2
    assert result.strategy_used == CompactionStrategy.HYBRID


@pytest.mark.asyncio
async def test_no_trigger_returns_passthrough() -> None:
    """No child triggers → passthrough (compacted_state None)."""
    chained = ChainedCompactor(
        compactors=[_StubCompactor(triggers=False), _StubCompactor(triggers=False)]
    )

    result = await chained.compact_if_needed(_make_state(1_000))

    assert result.triggered is False
    assert result.compacted_state is None
    assert result.messages_compacted == 0
    assert result.tokens_after == result.tokens_before == 1_000


@pytest.mark.asyncio
async def test_threads_state_to_next_child() -> None:
    """The 2nd child must receive the 1st child's REDUCED token count — the
    'tool-result clearing first defers semantic' mechanism."""
    preclear = _StubCompactor(
        triggers=True, tokens_after=400, strategy=CompactionStrategy.STRUCTURAL
    )
    hybrid = _StubCompactor(triggers=False)  # would-be semantic; sees reduced count
    chained = ChainedCompactor(compactors=[preclear, hybrid])

    await chained.compact_if_needed(_make_state(1_000))

    assert preclear.received_token_usage == 1_000
    assert hybrid.received_token_usage == 400  # saw the preclear-reduced state


@pytest.mark.asyncio
async def test_merges_messages_compacted() -> None:
    """Both children trigger → messages_compacted sums; tokens_after = last stage."""
    c1 = _StubCompactor(
        triggers=True,
        tokens_after=700,
        messages_compacted=2,
        strategy=CompactionStrategy.STRUCTURAL,
    )
    c2 = _StubCompactor(
        triggers=True,
        tokens_after=300,
        messages_compacted=3,
        strategy=CompactionStrategy.HYBRID,
    )
    chained = ChainedCompactor(compactors=[c1, c2])

    result = await chained.compact_if_needed(_make_state(1_000))

    assert result.triggered is True
    assert result.messages_compacted == 5
    assert result.tokens_after == 300


@pytest.mark.asyncio
async def test_strategy_is_last_triggered() -> None:
    """First triggers, second does not → strategy = first (last triggered)."""
    c1 = _StubCompactor(triggers=True, tokens_after=700, strategy=CompactionStrategy.STRUCTURAL)
    c2 = _StubCompactor(triggers=False)
    chained = ChainedCompactor(compactors=[c1, c2])

    result = await chained.compact_if_needed(_make_state(1_000))

    assert result.triggered is True
    assert result.strategy_used == CompactionStrategy.STRUCTURAL
    assert result.tokens_after == 700


@pytest.mark.asyncio
async def test_carries_llm_usage_from_later_stage() -> None:
    """A child reporting real summarize usage (C2 attribution) → carried up."""
    preclear = _StubCompactor(
        triggers=True, tokens_after=700, strategy=CompactionStrategy.STRUCTURAL
    )
    semantic = _StubCompactor(
        triggers=True,
        tokens_after=300,
        strategy=CompactionStrategy.HYBRID,
        input_tokens=1_234,
        output_tokens=56,
        model="gpt-cheap",
    )
    chained = ChainedCompactor(compactors=[preclear, semantic])

    result = await chained.compact_if_needed(_make_state(1_000))

    assert result.input_tokens == 1_234
    assert result.output_tokens == 56
    assert result.model == "gpt-cheap"
