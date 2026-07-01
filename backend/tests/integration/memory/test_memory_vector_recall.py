"""
File: backend/tests/integration/memory/test_memory_vector_recall.py
Purpose: Real-DB end-to-end test for UserLayer semantic recall (Sprint 57.155 — CARRY-026 Slice 1).
Category: Tests / Integration / 範疇 3
Scope: Phase 57 / Sprint 57.155

Description:
    Requires a live PostgreSQL (per conftest db_session). Exercises the FULL semantic
    recall chain with real components — real DB rows (written via UserLayer.write) + a
    real MemoryVectorIndex (real DeterministicEmbeddingClient embed logic) + a fake
    in-memory Qdrant store (no live Qdrant needed in CI). Proves: (1) a semantic-only
    read returns cosine-ranked hits from the vector path (not the 51.2 [] stub) when the
    index is injected, and (2) the per-user payload filter isolates one user's facts from
    another's inside the shared per-tenant collection. TRUE meaning-based recall (a
    keyword-disjoint query) is proven by the real-Azure drive-through; the deterministic
    embedder here makes an exact-content query rank cosine 1.0, proving the wiring.

Created: 2026-07-01 (Sprint 57.155)
"""

from __future__ import annotations

import math
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Callable, cast

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from adapters._testing.embedding import DeterministicEmbeddingClient
from agent_harness.memory.layers.user_layer import UserLayer
from agent_harness.memory.vector_index import MemoryVectorIndex
from infrastructure.vector.qdrant_client import VectorHit
from tests.conftest import seed_tenant, seed_user

pytestmark = pytest.mark.asyncio


def _cos(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


def _match(pf: Any, payload: dict[str, Any]) -> bool:
    if pf is None:
        return True
    return all(payload.get(c["key"]) == c["match"]["value"] for c in pf["must"])


class _FakeMemStore:
    """In-memory QdrantVectorStore honoring the tenant_id+user_id payload filter."""

    def __init__(self) -> None:
        self.collections: dict[str, list[tuple[int, list[float], dict[str, Any]]]] = {}

    async def count(self, name: str, payload_filter: Any = None) -> int:
        return sum(1 for p in self.collections.get(name, []) if _match(payload_filter, p[2]))

    async def ensure_collection(self, name: str, dim: int) -> None:
        self.collections.setdefault(name, [])

    async def upsert(
        self, name: str, points: list[tuple[int, list[float], dict[str, Any]]]
    ) -> None:
        by_id = {p[0]: p for p in self.collections.setdefault(name, [])}
        for pt in points:
            by_id[pt[0]] = pt
        self.collections[name] = list(by_id.values())

    async def search(
        self, name: str, query_vector: list[float], top_k: int, payload_filter: Any = None
    ) -> list[VectorHit]:
        pts = [p for p in self.collections.get(name, []) if _match(payload_filter, p[2])]
        ranked = sorted(pts, key=lambda p: _cos(query_vector, p[1]), reverse=True)[:top_k]
        return [VectorHit(payload=pl, score=_cos(query_vector, vec)) for (_, vec, pl) in ranked]


def _shared_factory(db_session: AsyncSession) -> Callable[[], object]:
    @asynccontextmanager
    async def _factory() -> AsyncIterator[AsyncSession]:
        orig_commit = db_session.commit
        db_session.commit = db_session.flush  # type: ignore[method-assign]
        try:
            yield db_session
        finally:
            db_session.commit = orig_commit  # type: ignore[method-assign]

    return _factory


def _layer(db_session: AsyncSession, store: _FakeMemStore) -> UserLayer:
    index = MemoryVectorIndex(DeterministicEmbeddingClient(dim=64), cast(Any, store))
    return UserLayer(cast(Any, _shared_factory(db_session)), vector_index=index)


async def test_semantic_read_returns_vector_hit_from_real_db_rows(
    db_session: AsyncSession,
) -> None:
    """Real DB rows → real MemoryVectorIndex → semantic-only read returns the row (was [])."""
    t = await seed_tenant(db_session, code="VEC_RECALL")
    u = await seed_user(db_session, t, email="recall@vec.test")
    await db_session.flush()

    store = _FakeMemStore()
    layer = _layer(db_session, store)
    await layer.write(content="Chris leads the vector-search rewrite", tenant_id=t.id, user_id=u.id)
    await layer.write(content="billing runs on PostgreSQL", tenant_id=t.id, user_id=u.id)

    hits = await layer.read(
        query="Chris leads the vector-search rewrite",
        tenant_id=t.id,
        user_id=u.id,
        time_scales=("semantic",),
    )
    assert hits  # NOT the 51.2 [] stub
    assert hits[0].summary == "Chris leads the vector-search rewrite"
    assert math.isclose(hits[0].relevance_score, 1.0, rel_tol=1e-6)  # exact content → cosine 1.0


async def test_semantic_recall_is_per_user_isolated(db_session: AsyncSession) -> None:
    """User A's semantic search never returns user B's fact (per-user payload filter)."""
    t = await seed_tenant(db_session, code="VEC_ISO")
    u_a = await seed_user(db_session, t, email="a@vec.test")
    u_b = await seed_user(db_session, t, email="b@vec.test")
    await db_session.flush()

    store = _FakeMemStore()  # shared store → ONE per-tenant collection holds both users
    secret_b = "user B private project codename Nightjar"
    await _layer(db_session, store).write(content=secret_b, tenant_id=t.id, user_id=u_b.id)
    await _layer(db_session, store).write(
        content="user A owns a different fact entirely", tenant_id=t.id, user_id=u_a.id
    )

    # user A searches for B's exact fact → must get 0 of B's rows (own rows only)
    a_hits = await _layer(db_session, store).read(
        query=secret_b, tenant_id=t.id, user_id=u_a.id, time_scales=("semantic",)
    )
    assert all(h.summary != secret_b for h in a_hits)
    # user B searching their own fact DOES retrieve it
    b_hits = await _layer(db_session, store).read(
        query=secret_b, tenant_id=t.id, user_id=u_b.id, time_scales=("semantic",)
    )
    assert any(h.summary == secret_b for h in b_hits)
