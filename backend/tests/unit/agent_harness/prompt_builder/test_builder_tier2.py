"""Unit tests for DefaultPromptBuilder Tier2 render + cap + verify (Sprint 57.65 A-1).

Pure (no loop): drive build() with a mocked MemoryRetrieval.search and assert the
assembled prompt's memory block is (a) enriched with confidence + last_verified_at,
(b) capped to max_memory_tokens (lowest-confidence/oldest dropped first), and
(c) prefaced by a lead-then-verify rule when a flagged hint exists.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from agent_harness._contracts import MemoryHint
from agent_harness.context_mgmt.cache_manager import InMemoryCacheManager
from agent_harness.context_mgmt.token_counter.generic_approx import GenericApproxCounter
from agent_harness.memory.retrieval import MemoryRetrieval
from agent_harness.prompt_builder.builder import DefaultPromptBuilder
from agent_harness.prompt_builder.templates import VERIFY_BEFORE_USE_HEADER
from tests.unit.agent_harness.prompt_builder.conftest import make_state, msg


def _hint(
    *,
    layer: str = "user",
    time_scale: str = "long_term",
    summary: str = "hint",
    confidence: float = 0.9,
    relevance_score: float = 0.8,
    verify_before_use: bool = False,
    last_verified_at: datetime | None = None,
    timestamp: datetime | None = None,
) -> MemoryHint:
    return MemoryHint(
        hint_id=uuid4(),
        layer=layer,  # type: ignore[arg-type]
        time_scale=time_scale,  # type: ignore[arg-type]
        summary=summary,
        confidence=confidence,
        relevance_score=relevance_score,
        full_content_pointer=f"db://memory/{uuid4()}",
        timestamp=timestamp or datetime.now(timezone.utc),
        last_verified_at=last_verified_at,
        verify_before_use=verify_before_use,
    )


def _builder_with(
    return_hints: list[MemoryHint], *, max_memory_tokens: int = 2000
) -> DefaultPromptBuilder:
    retrieval = MemoryRetrieval(layers={})
    retrieval.search = AsyncMock(return_value=return_hints)  # type: ignore[method-assign]
    return DefaultPromptBuilder(
        memory_retrieval=retrieval,
        cache_manager=InMemoryCacheManager(),
        token_counter=GenericApproxCounter(),
        max_memory_tokens=max_memory_tokens,
    )


def _all_content(messages) -> str:  # type: ignore[no-untyped-def]
    return "\n".join(str(m.content) for m in messages)


# ---- Render -------------------------------------------------------------


@pytest.mark.asyncio
async def test_render_includes_confidence_and_last_verified() -> None:
    verified_at = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
    builder = _builder_with(
        [_hint(summary="user likes blue", confidence=0.77, last_verified_at=verified_at)]
    )
    tenant_id = uuid4()
    state = make_state(messages=[msg("user", "what color")], tenant_id=tenant_id)

    artifact = await builder.build(state=state, tenant_id=tenant_id)

    content = _all_content(artifact.messages)
    assert "user likes blue" in content
    assert "confidence 0.77" in content
    assert verified_at.isoformat() in content


@pytest.mark.asyncio
async def test_render_full_content_pointer_not_inlined() -> None:
    """full_content_pointer is a DB/vector ref; it must NOT bloat the prompt."""
    h = _hint(summary="some fact")
    builder = _builder_with([h])
    tenant_id = uuid4()
    state = make_state(messages=[msg("user", "q")], tenant_id=tenant_id)

    artifact = await builder.build(state=state, tenant_id=tenant_id)

    assert h.full_content_pointer not in _all_content(artifact.messages)


# ---- Cap ----------------------------------------------------------------


@pytest.mark.asyncio
async def test_cap_keeps_memory_block_under_budget() -> None:
    # Many large hints; tiny budget forces truncation.
    big_summary = "x" * 400
    hints = [_hint(layer="user", summary=f"{i}-{big_summary}", confidence=0.5) for i in range(30)]
    builder = _builder_with(hints, max_memory_tokens=200)
    tenant_id = uuid4()
    state = make_state(messages=[msg("user", "q")], tenant_id=tenant_id)

    artifact = await builder.build(state=state, tenant_id=tenant_id)

    # Measure ONLY the rendered memory messages against the budget.
    memory_msgs = [m for m in artifact.messages if m.metadata.get("memory_layer")]
    counter = GenericApproxCounter()
    block_tokens = counter.count(messages=memory_msgs, tools=None) if memory_msgs else 0
    assert block_tokens <= 200


@pytest.mark.asyncio
async def test_cap_drops_lowest_confidence_first() -> None:
    keep = _hint(layer="user", summary="HIGH-CONF-KEEP", confidence=0.95)
    drop = _hint(layer="user", summary="LOW-CONF-DROP", confidence=0.10)
    # Budget large enough for one of these two but not both.
    one = _builder_with([keep], max_memory_tokens=5000)
    state = make_state(messages=[msg("user", "q")], tenant_id=uuid4())
    one_block = [
        m
        for m in (await one.build(state=state, tenant_id=state.durable.tenant_id)).messages
        if m.metadata.get("memory_layer")
    ]
    counter = GenericApproxCounter()
    budget = counter.count(messages=one_block, tools=None) + 1

    builder = _builder_with([keep, drop], max_memory_tokens=budget)
    state2 = make_state(messages=[msg("user", "q")], tenant_id=uuid4())
    artifact = await builder.build(state=state2, tenant_id=state2.durable.tenant_id)

    content = _all_content(artifact.messages)
    assert "HIGH-CONF-KEEP" in content
    assert "LOW-CONF-DROP" not in content


@pytest.mark.asyncio
async def test_cap_ties_break_on_oldest_timestamp() -> None:
    now = datetime.now(timezone.utc)
    newer = _hint(layer="user", summary="NEWER-KEEP", confidence=0.5, timestamp=now)
    older = _hint(
        layer="user", summary="OLDER-DROP", confidence=0.5, timestamp=now - timedelta(days=10)
    )
    one = _builder_with([newer], max_memory_tokens=5000)
    state = make_state(messages=[msg("user", "q")], tenant_id=uuid4())
    one_block = [
        m
        for m in (await one.build(state=state, tenant_id=state.durable.tenant_id)).messages
        if m.metadata.get("memory_layer")
    ]
    counter = GenericApproxCounter()
    budget = counter.count(messages=one_block, tools=None) + 1

    builder = _builder_with([newer, older], max_memory_tokens=budget)
    state2 = make_state(messages=[msg("user", "q")], tenant_id=uuid4())
    artifact = await builder.build(state=state2, tenant_id=state2.durable.tenant_id)

    content = _all_content(artifact.messages)
    assert "NEWER-KEEP" in content
    assert "OLDER-DROP" not in content


@pytest.mark.asyncio
async def test_cap_no_op_when_under_budget() -> None:
    hints = [_hint(layer="user", summary="small note", confidence=0.9)]
    builder = _builder_with(hints, max_memory_tokens=2000)
    tenant_id = uuid4()
    state = make_state(messages=[msg("user", "q")], tenant_id=tenant_id)

    artifact = await builder.build(state=state, tenant_id=tenant_id)

    assert "small note" in _all_content(artifact.messages)
    assert set(artifact.layer_metadata["memory_layers_used"]) == {"user"}


# ---- verify_before_use --------------------------------------------------


@pytest.mark.asyncio
async def test_verify_before_use_rule_present_when_flagged() -> None:
    builder = _builder_with(
        [_hint(layer="user", summary="STALE-PRICE-2024", verify_before_use=True)]
    )
    tenant_id = uuid4()
    state = make_state(messages=[msg("user", "q")], tenant_id=tenant_id)

    artifact = await builder.build(state=state, tenant_id=tenant_id)

    system_msgs = [
        m for m in artifact.messages if m.role == "system" and not m.metadata.get("echo")
    ]
    system_text = "\n".join(str(m.content) for m in system_msgs)
    assert VERIFY_BEFORE_USE_HEADER in system_text
    assert "STALE-PRICE-2024" in system_text


@pytest.mark.asyncio
async def test_verify_before_use_rule_absent_when_no_flag() -> None:
    builder = _builder_with([_hint(layer="user", summary="fresh fact", verify_before_use=False)])
    tenant_id = uuid4()
    state = make_state(messages=[msg("user", "q")], tenant_id=tenant_id)

    artifact = await builder.build(state=state, tenant_id=tenant_id)

    assert VERIFY_BEFORE_USE_HEADER not in _all_content(artifact.messages)


@pytest.mark.asyncio
async def test_verify_skips_hint_dropped_by_cap() -> None:
    """A flagged hint that the cap removed must NOT trigger the verify rule."""
    flagged_low = _hint(
        layer="user", summary="DROPPED-FLAGGED", confidence=0.05, verify_before_use=True
    )
    keep_high = _hint(layer="user", summary="KEPT-PLAIN", confidence=0.95)
    one = _builder_with([keep_high], max_memory_tokens=5000)
    state = make_state(messages=[msg("user", "q")], tenant_id=uuid4())
    one_block = [
        m
        for m in (await one.build(state=state, tenant_id=state.durable.tenant_id)).messages
        if m.metadata.get("memory_layer")
    ]
    counter = GenericApproxCounter()
    budget = counter.count(messages=one_block, tools=None) + 1

    builder = _builder_with([keep_high, flagged_low], max_memory_tokens=budget)
    state2 = make_state(messages=[msg("user", "q")], tenant_id=uuid4())
    artifact = await builder.build(state=state2, tenant_id=state2.durable.tenant_id)

    content = _all_content(artifact.messages)
    assert "DROPPED-FLAGGED" not in content
    assert VERIFY_BEFORE_USE_HEADER not in content


# ---- Negative: empty retrieval -----------------------------------------


@pytest.mark.asyncio
async def test_empty_retrieval_renders_no_memory_block() -> None:
    builder = DefaultPromptBuilder(
        memory_retrieval=MemoryRetrieval(layers={}),
        cache_manager=InMemoryCacheManager(),
        token_counter=GenericApproxCounter(),
    )
    tenant_id = uuid4()
    state = make_state(messages=[msg("user", "hello")], tenant_id=tenant_id)

    artifact = await builder.build(state=state, tenant_id=tenant_id)

    assert artifact.layer_metadata["memory_layers_used"] == []
    assert not any(m.metadata.get("memory_layer") for m in artifact.messages)
    assert VERIFY_BEFORE_USE_HEADER not in _all_content(artifact.messages)


# ---- Deterministic scope ordering --------------------------------------


@pytest.mark.asyncio
async def test_layers_emitted_in_fixed_scope_order() -> None:
    # Return hints in a scrambled order; assert render order is system→…→session.
    builder = _builder_with(
        [
            _hint(layer="session", summary="S-sess"),
            _hint(layer="system", summary="S-sys"),
            _hint(layer="user", summary="S-user"),
            _hint(layer="tenant", summary="S-tenant"),
            _hint(layer="role", summary="S-role"),
        ]
    )
    tenant_id = uuid4()
    state = make_state(messages=[msg("user", "q")], tenant_id=tenant_id)

    artifact = await builder.build(state=state, tenant_id=tenant_id)

    used = artifact.layer_metadata["memory_layers_used"]
    assert used == ["system", "tenant", "role", "user", "session"]
