"""
File: backend/tests/unit/agent_harness/memory/test_user_layer.py
Purpose: Unit tests for UserLayer (Layer 4; PG-backed durable per-user memory).
Category: Tests / 範疇 3
Scope: Phase 51 / Sprint 51.2 Day 2.7

Description:
    Mix of static-helper tests (_row_to_hint mapping logic) and AsyncMock-
    based DB interaction tests. Real DB integration tests live in
    tests/integration/memory/ (Day 4-5).

Created: 2026-04-30
Modified: 2026-06-04 (Sprint 57.76 — update write/evict assertions for memory_ops emit)
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from agent_harness.memory.layers.user_layer import UserLayer, _dedup_key
from agent_harness.memory.vector_index import MemoryVectorHit
from infrastructure.db.models.memory import MemoryOp, MemoryUser


class _FakeVectorIndex:
    """Stand-in MemoryVectorIndex: returns preset hits + records the search call."""

    def __init__(self, hits: list[MemoryVectorHit]) -> None:
        self._hits = hits
        self.calls: list[tuple[Any, Any, list[str], str, int]] = []

    async def search(
        self, *, tenant_id: Any, user_id: Any, rows: Any, query: str, top_k: int
    ) -> list[MemoryVectorHit]:
        self.calls.append((tenant_id, user_id, [r.dedup_key for r in rows], query, top_k))
        return self._hits


def _build_factory(
    rows: list[MemoryUser],
    scalar_value: str | None = None,
    scalar_one_value: object | None = None,
) -> AsyncMock:
    """async_sessionmaker shape: factory() returns async ctx mgr -> session.

    `scalar_one_value` configures the upserted-id returned by write()'s
    `(await session.execute(pg_insert…returning)).scalar_one()` (Sprint 57.150).
    """
    session = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = rows
    result.scalar_one_or_none.return_value = scalar_value
    result.scalar_one.return_value = scalar_one_value
    session.execute = AsyncMock(return_value=result)
    session.commit = AsyncMock()
    session.add = MagicMock()
    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=session)
    cm.__aexit__ = AsyncMock(return_value=False)
    factory = MagicMock(return_value=cm)
    factory._mock_session = session  # for test introspection
    return factory


def _make_row(
    *,
    tenant_id: object | None = None,
    user_id: object | None = None,
    content: str = "user prefers detailed reports",
    confidence: Decimal | None = Decimal("0.85"),
    metadata: dict[str, object] | None = None,
    expires_at: datetime | None = None,
) -> MemoryUser:
    row = MemoryUser(
        id=uuid4(),
        tenant_id=tenant_id or uuid4(),
        user_id=user_id or uuid4(),
        category="preference",
        content=content,
        confidence=confidence,
        expires_at=expires_at,
        metadata_=metadata or {"time_scale": "long_term"},
    )
    row.created_at = datetime.now(timezone.utc)
    return row


@pytest.mark.asyncio
async def test_read_returns_empty_without_tenant_or_user() -> None:
    layer = UserLayer(_build_factory([]))
    assert await layer.read(query="x", tenant_id=None, user_id=uuid4()) == []
    assert await layer.read(query="x", tenant_id=uuid4(), user_id=None) == []


@pytest.mark.asyncio
async def test_read_returns_hints() -> None:
    tenant = uuid4()
    user = uuid4()
    row = _make_row(tenant_id=tenant, user_id=user)
    layer = UserLayer(_build_factory([row]))

    hints = await layer.read(query="detailed", tenant_id=tenant, user_id=user)
    assert len(hints) == 1
    h = hints[0]
    assert h.layer == "user"
    assert h.time_scale == "long_term"
    assert h.confidence == 0.85
    assert h.tenant_id == tenant
    # relevance_score boosted because query matches content
    assert h.relevance_score == 0.8


@pytest.mark.asyncio
async def test_read_semantic_only_returns_empty() -> None:
    """Semantic axis is the 51.2 [] stub when NO vector index is injected (byte-identical)."""
    layer = UserLayer(_build_factory([_make_row()]))
    hints = await layer.read(
        query="x", tenant_id=uuid4(), user_id=uuid4(), time_scales=("semantic",)
    )
    assert hints == []


@pytest.mark.asyncio
async def test_read_semantic_returns_vector_hits_when_index_injected() -> None:
    """Sprint 57.155 (CARRY-026 Slice 1): with a MemoryVectorIndex injected, semantic
    recall returns cosine-ranked hits (was the 51.2 [] stub); the hit's cosine score
    becomes the MemoryHint.relevance_score (not the keyword 0.4/0.8 substring boost)."""
    tenant, user = uuid4(), uuid4()
    row = _make_row(tenant_id=tenant, user_id=user, content="I love scuba diving")
    row.dedup_key = "k1"
    fake = _FakeVectorIndex(
        [
            MemoryVectorHit(
                dedup_key="k1", content="I love scuba diving", confidence=0.85, score=0.93
            )
        ]
    )
    layer = UserLayer(_build_factory([row]), vector_index=cast(Any, fake))
    hints = await layer.read(
        query="ocean hobbies", tenant_id=tenant, user_id=user, time_scales=("semantic",)
    )
    assert len(hints) == 1
    assert hints[0].summary == "I love scuba diving"
    assert hints[0].relevance_score == 0.93  # cosine score, not the substring boost
    # the index was queried with the user's rows + the query
    assert fake.calls and fake.calls[0][3] == "ocean hobbies"


@pytest.mark.asyncio
async def test_read_semantic_fail_soft_on_index_error() -> None:
    """Any embed/Qdrant error → semantic degrades to [] (recall never breaks)."""

    class _BoomIndex:
        async def search(self, **kwargs: Any) -> list[MemoryVectorHit]:
            raise RuntimeError("qdrant unreachable")

    tenant, user = uuid4(), uuid4()
    row = _make_row(tenant_id=tenant, user_id=user)
    row.dedup_key = "k1"
    layer = UserLayer(_build_factory([row]), vector_index=cast(Any, _BoomIndex()))
    hints = await layer.read(query="x", tenant_id=tenant, user_id=user, time_scales=("semantic",))
    assert hints == []  # fail-soft to the stub


@pytest.mark.asyncio
async def test_write_returns_upserted_id_and_records_op() -> None:
    """Sprint 57.150: write() upserts via execute(pg_insert…returning).scalar_one()
    and still records a WRITE MemoryOp in the same txn (Risk C). The returned id is
    the upserted row id (new on insert, existing on conflict)."""
    upserted = uuid4()
    layer = UserLayer(_build_factory([], scalar_one_value=upserted))
    eid = await layer.write(
        content="prefers brevity",
        tenant_id=uuid4(),
        user_id=uuid4(),
        time_scale="long_term",
        confidence=0.7,
    )
    assert eid == upserted

    session = layer._session_factory._mock_session  # type: ignore[attr-defined]
    # The upsert ran via session.execute (NOT session.add(MemoryUser)).
    session.execute.assert_awaited_once()
    op_targets = [c.args[0] for c in session.add.call_args_list if isinstance(c.args[0], MemoryOp)]
    assert len(op_targets) == 1
    assert op_targets[0].operation == "WRITE"
    assert op_targets[0].time_scale == "long_term"
    assert op_targets[0].value_snapshot == "prefers brevity"
    # No MemoryUser is session.add'd anymore (the upsert is an execute()).
    assert not [c.args[0] for c in session.add.call_args_list if isinstance(c.args[0], MemoryUser)]
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_write_short_term_op_records_time_scale() -> None:
    """Sprint 57.150: short_term still flows through the upsert; the MemoryOp
    carries the time_scale. The 24h-expiry value now lives in the real-DB
    integration test (test_user_layer_dedup.py), where the inserted row is observable."""
    layer = UserLayer(_build_factory([], scalar_one_value=uuid4()))
    await layer.write(
        content="working note",
        tenant_id=uuid4(),
        user_id=uuid4(),
        time_scale="short_term",
    )
    session = layer._session_factory._mock_session  # type: ignore[attr-defined]
    op_targets = [c.args[0] for c in session.add.call_args_list if isinstance(c.args[0], MemoryOp)]
    assert len(op_targets) == 1
    assert op_targets[0].time_scale == "short_term"


@pytest.mark.asyncio
async def test_write_requires_tenant_and_user() -> None:
    layer = UserLayer(_build_factory([]))
    with pytest.raises(ValueError, match="tenant_id and user_id"):
        await layer.write(content="x", tenant_id=None, user_id=uuid4())
    with pytest.raises(ValueError):
        await layer.write(content="x", tenant_id=uuid4(), user_id=None)


@pytest.mark.asyncio
async def test_evict_no_op_without_tenant_id() -> None:
    layer = UserLayer(_build_factory([]))
    # Should not raise; just no-op
    await layer.evict(entry_id=uuid4(), tenant_id=None)
    session = layer._session_factory._mock_session  # type: ignore[attr-defined]
    session.execute.assert_not_called()


@pytest.mark.asyncio
async def test_evict_executes_delete_when_tenant_present() -> None:
    # Sprint 57.76: evict now SELECTs-before-DELETE to snapshot the old value,
    # then emits a MemoryOp(EVICT). Configure the SELECT result + assert both.
    factory = _build_factory([])
    old_user = uuid4()
    factory._mock_session.execute.return_value.first.return_value = ("old fact", old_user)
    layer = UserLayer(factory)
    await layer.evict(entry_id=uuid4(), tenant_id=uuid4())
    session = factory._mock_session  # type: ignore[attr-defined]
    # SELECT + DELETE = 2 execute() calls now.
    assert session.execute.await_count == 2
    session.commit.assert_awaited_once()
    # An EVICT op row was recorded with the old value.
    op_targets = [c.args[0] for c in session.add.call_args_list if isinstance(c.args[0], MemoryOp)]
    assert len(op_targets) == 1
    assert op_targets[0].operation == "EVICT"
    assert op_targets[0].value_snapshot == "old fact"


@pytest.mark.asyncio
async def test_resolve_returns_full_content() -> None:
    full = "user prefers extremely detailed financial breakdowns including line items"
    factory = _build_factory(rows=[], scalar_value=full)
    layer = UserLayer(factory)

    from agent_harness._contracts import MemoryHint

    hint = MemoryHint(
        hint_id=uuid4(),
        layer="user",
        time_scale="long_term",
        summary=full[:50],
        confidence=0.9,
        relevance_score=0.8,
        full_content_pointer="memory_user:abc",
        timestamp=datetime.now(timezone.utc),
        tenant_id=uuid4(),
    )
    content = await layer.resolve(hint)
    assert content == full


def test_row_to_hint_handles_missing_metadata() -> None:
    """Static helper: missing metadata → defaults applied (no exception)."""
    row = _make_row(metadata={})
    hint = UserLayer._row_to_hint(row, query="anything")
    assert hint.time_scale == "long_term"  # default
    assert hint.verify_before_use is False
    assert hint.last_verified_at is None
    assert hint.source_tool_call_id is None


def test_row_to_hint_parses_iso_last_verified() -> None:
    iso = "2026-04-15T10:30:00+00:00"
    row = _make_row(metadata={"time_scale": "long_term", "last_verified_at": iso})
    hint = UserLayer._row_to_hint(row, query="x")
    assert hint.last_verified_at is not None
    assert hint.last_verified_at.year == 2026


# ---------------------------------------------------------------------------
# _dedup_key normalization (Sprint 57.150 — write-side upsert key)
# ---------------------------------------------------------------------------


def test_dedup_key_is_32_hex() -> None:
    key = _dedup_key("hello world")
    assert len(key) == 32
    assert all(c in "0123456789abcdef" for c in key)


def test_dedup_key_normalizes_whitespace_and_case() -> None:
    """Collapse whitespace runs + trim edges + lowercase before hashing — must
    match the migration 0032 backfill so a backfilled row and a live repeat collide."""
    assert _dedup_key("User  Likes\tDark   Mode") == _dedup_key("user likes dark mode")
    assert _dedup_key("  hello  ") == _dedup_key("hello")
    assert _dedup_key("Hello\nWorld") == _dedup_key("hello world")


def test_dedup_key_distinguishes_different_content() -> None:
    assert _dedup_key("Chris works on Aurora") != _dedup_key("Chris works on Borealis")
