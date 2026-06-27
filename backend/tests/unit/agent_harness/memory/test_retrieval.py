"""
File: backend/tests/unit/agent_harness/memory/test_retrieval.py
Purpose: Unit tests for MemoryRetrieval coordinator.
Category: Tests / Cat 3
Scope: Phase 51 / Sprint 51.2 Day 3.4

Created: 2026-04-30
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4

import pytest

from agent_harness._contracts import MemoryHint, TraceContext
from agent_harness.memory._abc import MemoryLayer, MemoryScope


class _StubLayer(MemoryLayer):
    """Stub MemoryLayer that returns canned hints; records last call args."""

    def __init__(self, scope: MemoryScope, hints: list[MemoryHint]) -> None:
        self.scope = scope
        self._hints = hints
        self.last_user_id: UUID | None = None
        self.last_tenant_id: UUID | None = None
        self.last_time_scales: tuple[str, ...] | None = None
        self.last_query: str | None = None
        self.last_max_hints: int | None = None
        self.read_count = 0

    async def read(
        self,
        *,
        query: str,
        tenant_id: UUID | None = None,
        user_id: UUID | None = None,
        time_scales: tuple[Literal["short_term", "long_term", "semantic"], ...] = ("long_term",),
        max_hints: int = 10,
        trace_context: TraceContext | None = None,
    ) -> list[MemoryHint]:
        self.read_count += 1
        self.last_user_id = user_id
        self.last_tenant_id = tenant_id
        self.last_time_scales = tuple(time_scales)
        self.last_query = query
        self.last_max_hints = max_hints
        return list(self._hints)

    async def write(self, **kwargs: object) -> UUID:
        raise NotImplementedError

    async def evict(self, **kwargs: object) -> None:
        raise NotImplementedError

    async def resolve(self, hint: MemoryHint, **kwargs: object) -> str:
        return ""


def _hint(
    *,
    layer: Literal["system", "tenant", "role", "user", "session"] = "user",
    confidence: float = 0.5,
    relevance: float = 0.5,
    summary: str = "x",
) -> MemoryHint:
    return MemoryHint(
        hint_id=uuid4(),
        layer=layer,
        time_scale="long_term",
        summary=summary,
        confidence=confidence,
        relevance_score=relevance,
        full_content_pointer="p",
        timestamp=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_search_returns_empty_without_tenant() -> None:
    from agent_harness.memory.retrieval import MemoryRetrieval

    r = MemoryRetrieval({})
    assert await r.search(query="x", tenant_id=None) == []


@pytest.mark.asyncio
async def test_search_dispatches_to_configured_layers_only() -> None:
    from agent_harness.memory.retrieval import MemoryRetrieval

    user_layer = _StubLayer(MemoryScope.USER, [_hint(layer="user")])
    r = MemoryRetrieval({"user": user_layer})

    result = await r.search(
        query="hello",
        tenant_id=uuid4(),
        user_id=uuid4(),
        scopes=("user", "tenant", "session"),
    )
    assert user_layer.read_count == 1
    assert len(result) == 1


@pytest.mark.asyncio
async def test_search_routes_session_id_for_session_layer() -> None:
    """SessionLayer overloads user_id slot for session_id; coordinator routes."""
    from agent_harness.memory.retrieval import MemoryRetrieval

    session_layer = _StubLayer(MemoryScope.SESSION, [_hint(layer="session")])
    user_layer = _StubLayer(MemoryScope.USER, [_hint(layer="user")])
    r = MemoryRetrieval({"session": session_layer, "user": user_layer})

    tenant = uuid4()
    user = uuid4()
    session = uuid4()

    await r.search(
        query="x",
        tenant_id=tenant,
        user_id=user,
        session_id=session,
        scopes=("session", "user"),
    )
    assert session_layer.last_user_id == session
    assert user_layer.last_user_id == user


@pytest.mark.asyncio
async def test_search_top_k_limits_result() -> None:
    from agent_harness.memory.retrieval import MemoryRetrieval

    user_layer = _StubLayer(
        MemoryScope.USER,
        [_hint(layer="user", confidence=0.9, relevance=0.9) for _ in range(10)],
    )
    r = MemoryRetrieval({"user": user_layer})

    out = await r.search(
        query="x",
        tenant_id=uuid4(),
        user_id=uuid4(),
        scopes=("user",),
        top_k=3,
    )
    assert len(out) == 3


@pytest.mark.asyncio
async def test_search_sort_by_relevance_times_confidence() -> None:
    from agent_harness.memory.retrieval import MemoryRetrieval

    low = _hint(layer="user", relevance=0.4, confidence=0.4, summary="low")
    mid = _hint(layer="user", relevance=0.7, confidence=0.5, summary="mid")
    high = _hint(layer="user", relevance=0.9, confidence=0.9, summary="high")
    user_layer = _StubLayer(MemoryScope.USER, [low, mid, high])
    r = MemoryRetrieval({"user": user_layer})

    out = await r.search(
        query="x",
        tenant_id=uuid4(),
        user_id=uuid4(),
        scopes=("user",),
        top_k=3,
    )
    assert [h.summary for h in out] == ["high", "mid", "low"]


@pytest.mark.asyncio
async def test_search_handles_layer_exceptions() -> None:
    """One layer failing should not abort the entire search."""
    from agent_harness.memory.retrieval import MemoryRetrieval

    class _BoomLayer(_StubLayer):
        async def read(self, **kwargs: object) -> list[MemoryHint]:
            self.read_count += 1
            raise RuntimeError("boom")

    boom = _BoomLayer(MemoryScope.TENANT, [])
    user_layer = _StubLayer(MemoryScope.USER, [_hint(layer="user")])
    r = MemoryRetrieval({"tenant": boom, "user": user_layer})

    out = await r.search(
        query="x",
        tenant_id=uuid4(),
        user_id=uuid4(),
        scopes=("tenant", "user"),
    )
    assert len(out) == 1


@pytest.mark.asyncio
async def test_search_passes_time_scales_to_layers() -> None:
    from agent_harness.memory.retrieval import MemoryRetrieval

    user_layer = _StubLayer(MemoryScope.USER, [])
    r = MemoryRetrieval({"user": user_layer})

    await r.search(
        query="x",
        tenant_id=uuid4(),
        user_id=uuid4(),
        scopes=("user",),
        time_scales=("long_term", "semantic"),
    )
    assert user_layer.last_time_scales == ("long_term", "semantic")


@pytest.mark.asyncio
async def test_search_returns_empty_for_unmapped_scopes() -> None:
    from agent_harness.memory.retrieval import MemoryRetrieval

    r = MemoryRetrieval({})
    out = await r.search(
        query="x",
        tenant_id=uuid4(),
        user_id=uuid4(),
        scopes=("user", "tenant"),
    )
    assert out == []


# --- Sprint 57.148: profile() always-on user-scope pull (memory-formation S1) ---


@pytest.mark.asyncio
async def test_profile_returns_empty_without_tenant_or_user() -> None:
    """Zero-trust: profile() never dispatches without both tenant_id and user_id."""
    from agent_harness.memory.retrieval import MemoryRetrieval

    user_layer = _StubLayer(MemoryScope.USER, [_hint(layer="user")])
    r = MemoryRetrieval({"user": user_layer})

    assert await r.profile(tenant_id=None, user_id=uuid4()) == []
    assert await r.profile(tenant_id=uuid4(), user_id=None) == []
    assert user_layer.read_count == 0  # never dispatched


@pytest.mark.asyncio
async def test_profile_returns_empty_without_user_layer() -> None:
    from agent_harness.memory.retrieval import MemoryRetrieval

    r = MemoryRetrieval({"tenant": _StubLayer(MemoryScope.TENANT, [_hint(layer="tenant")])})
    assert await r.profile(tenant_id=uuid4(), user_id=uuid4()) == []


@pytest.mark.asyncio
async def test_profile_pulls_user_layer_long_term_with_wildcard_query() -> None:
    """profile() is NOT query-gated: wildcard ('') + long_term-only to the user layer."""
    from agent_harness.memory.retrieval import MemoryRetrieval

    user_layer = _StubLayer(MemoryScope.USER, [_hint(layer="user", summary="name is Chris")])
    r = MemoryRetrieval({"user": user_layer})

    out = await r.profile(tenant_id=uuid4(), user_id=uuid4(), top_k=7)

    assert [h.summary for h in out] == ["name is Chris"]
    assert user_layer.last_query == ""  # wildcard — surfaces regardless of the message
    assert user_layer.last_time_scales == ("long_term",)
    assert user_layer.last_max_hints == 7  # top_k passed through
    assert user_layer.last_user_id is not None  # user-scoped (not session)


@pytest.mark.asyncio
async def test_profile_only_dispatches_user_layer() -> None:
    """profile() is user-scope only — it never touches tenant / session layers."""
    from agent_harness.memory.retrieval import MemoryRetrieval

    user_layer = _StubLayer(MemoryScope.USER, [_hint(layer="user")])
    tenant_layer = _StubLayer(MemoryScope.TENANT, [_hint(layer="tenant")])
    r = MemoryRetrieval({"user": user_layer, "tenant": tenant_layer})

    await r.profile(tenant_id=uuid4(), user_id=uuid4())

    assert user_layer.read_count == 1
    assert tenant_layer.read_count == 0
