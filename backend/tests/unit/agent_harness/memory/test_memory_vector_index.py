"""
File: backend/tests/unit/agent_harness/memory/test_memory_vector_index.py
Purpose: Unit tests for MemoryVectorIndex (Sprint 57.155 — CARRY-026 Slice 1, L4 user).
Category: Tests
Created: 2026-07-01
"""

from __future__ import annotations

import math
from typing import Any, cast
from uuid import uuid4

from adapters._testing.embedding import DeterministicEmbeddingClient
from agent_harness.memory.vector_index import (
    _EMBED_BATCH,
    MemoryRow,
    MemoryVectorIndex,
)
from infrastructure.vector.qdrant_client import VectorHit


def _cos(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


def _match(payload_filter: Any, payload: dict[str, Any]) -> bool:
    """Honor the two-key (tenant_id AND user_id) MemoryVectorIndex payload filter."""
    if payload_filter is None:
        return True
    for clause in payload_filter["must"]:
        if payload.get(clause["key"]) != clause["match"]["value"]:
            return False
    return True


class _FakeMemStore:
    """Collection-aware async stand-in for QdrantVectorStore honoring the per-user filter.

    A per-tenant collection (`tenant_<hex>_user_memory`) can hold MANY users' points;
    count + search honor the tenant_id+user_id payload filter the way real Qdrant does,
    so the per-user idempotency + isolation tests are faithful.
    """

    def __init__(self) -> None:
        self.collections: dict[str, list[tuple[int, list[float], dict[str, Any]]]] = {}

    async def count(self, name: str, payload_filter: Any = None) -> int:
        pts = self.collections.get(name, [])
        return sum(1 for p in pts if _match(payload_filter, p[2]))

    async def ensure_collection(self, name: str, dim: int) -> None:
        self.collections.setdefault(name, [])

    async def upsert(
        self, name: str, points: list[tuple[int, list[float], dict[str, Any]]]
    ) -> None:
        bucket = self.collections.setdefault(name, [])
        # Idempotent upsert by point id (mirror Qdrant: same id replaces).
        by_id = {p[0]: p for p in bucket}
        for pt in points:
            by_id[pt[0]] = pt
        self.collections[name] = list(by_id.values())

    async def search(
        self,
        name: str,
        query_vector: list[float],
        top_k: int,
        payload_filter: Any = None,
    ) -> list[VectorHit]:
        pts = [p for p in self.collections.get(name, []) if _match(payload_filter, p[2])]
        ranked = sorted(pts, key=lambda p: _cos(query_vector, p[1]), reverse=True)[:top_k]
        return [VectorHit(payload=pl, score=_cos(query_vector, vec)) for (_, vec, pl) in ranked]


class _CountingEmbedder:
    """Wraps DeterministicEmbeddingClient + records each batch size."""

    def __init__(self, dim: int = 16) -> None:
        self._inner = DeterministicEmbeddingClient(dim=dim)
        self.batch_sizes: list[int] = []

    async def embed(self, texts: list[str]) -> list[list[float]]:
        self.batch_sizes.append(len(texts))
        return await self._inner.embed(texts)

    def model_name(self) -> str:
        return "counting"


def _index(store: Any, dim: int = 48) -> MemoryVectorIndex:
    return MemoryVectorIndex(DeterministicEmbeddingClient(dim=dim), cast(Any, store))


def _rows(*contents: str) -> list[MemoryRow]:
    # dedup_key just needs to be stable + unique per distinct content for the tests.
    return [
        MemoryRow(dedup_key=f"k{i}", content=c, confidence=0.5 + 0.01 * i)
        for i, c in enumerate(contents)
    ]


# --- core semantic behavior ----------------------------------------------------


async def test_search_exact_row_ranks_first() -> None:
    tid, uid = uuid4(), uuid4()
    store = _FakeMemStore()
    rows = _rows("Chris leads the vector-search rewrite", "billing runs on Postgres")
    hits = await _index(store).search(
        tenant_id=tid,
        user_id=uid,
        rows=rows,
        query="Chris leads the vector-search rewrite",
        top_k=2,
    )
    assert hits
    assert hits[0].content == "Chris leads the vector-search rewrite"
    assert math.isclose(hits[0].score, 1.0, rel_tol=1e-6)  # identical embedding → cosine 1.0
    assert hits[0].dedup_key == "k0"


async def test_search_empty_rows_or_query_returns_empty() -> None:
    tid, uid = uuid4(), uuid4()
    store = _FakeMemStore()
    assert await _index(store).search(tenant_id=tid, user_id=uid, rows=[], query="x", top_k=3) == []
    assert (
        await _index(store).search(
            tenant_id=tid, user_id=uid, rows=_rows("a"), query="   ", top_k=3
        )
        == []
    )


async def test_hit_carries_cosine_score_and_confidence() -> None:
    tid, uid = uuid4(), uuid4()
    store = _FakeMemStore()
    rows = [MemoryRow(dedup_key="k0", content="deep sea diving is fun", confidence=0.9)]
    hits = await _index(store).search(
        tenant_id=tid, user_id=uid, rows=rows, query="deep sea diving is fun", top_k=1
    )
    assert hits[0].confidence == 0.9
    assert 0.0 <= hits[0].score <= 1.0


# --- lazy ingest idempotency (per-user count guard) ----------------------------


async def test_lazy_ingest_idempotent_per_user() -> None:
    tid, uid = uuid4(), uuid4()
    store = _FakeMemStore()
    embedder = _CountingEmbedder(dim=32)
    index = MemoryVectorIndex(cast(Any, embedder), cast(Any, store))
    rows = _rows("alpha fact one", "beta fact two")
    await index.search(tenant_id=tid, user_id=uid, rows=rows, query="alpha fact one", top_k=3)
    after_first = list(embedder.batch_sizes)
    await index.search(tenant_id=tid, user_id=uid, rows=rows, query="alpha fact one", top_k=3)
    # 2nd search: count(user)==len(rows) → skip corpus re-embed; only the query embed (size 1).
    assert embedder.batch_sizes == after_first + [1]


async def test_new_fact_triggers_reingest() -> None:
    tid, uid = uuid4(), uuid4()
    store = _FakeMemStore()
    index = _index(store)
    await index.search(tenant_id=tid, user_id=uid, rows=_rows("one"), query="one", top_k=3)
    coll = next(iter(store.collections))
    assert len(store.collections[coll]) == 1
    # a new fact → count(1) != expected(2) → re-ingest upserts the 2nd point
    await index.search(tenant_id=tid, user_id=uid, rows=_rows("one", "two"), query="two", top_k=3)
    assert len(store.collections[coll]) == 2


async def test_ingest_batches_embedding_calls() -> None:
    tid, uid = uuid4(), uuid4()
    store = _FakeMemStore()
    embedder = _CountingEmbedder()
    index = MemoryVectorIndex(cast(Any, embedder), cast(Any, store))
    n = _EMBED_BATCH + 4  # crosses the batch boundary
    rows = _rows(*[f"fact number {i} content" for i in range(n)])
    await index.search(
        tenant_id=tid, user_id=uid, rows=rows, query="fact number 0 content", top_k=2
    )
    # corpus embedded in [16, 4] batches, then the query embed (size 1)
    assert embedder.batch_sizes == [_EMBED_BATCH, 4, 1]


# --- point id stability + per-user uniqueness ----------------------------------


def test_point_id_stable_and_per_user_unique() -> None:
    u1, u2 = uuid4(), uuid4()
    # same (user, dedup_key) → same id (stable upsert)
    assert MemoryVectorIndex._point_id(u1, "kX") == MemoryVectorIndex._point_id(u1, "kX")
    # two users' identical fact (same dedup_key) → distinct ids
    assert MemoryVectorIndex._point_id(u1, "kX") != MemoryVectorIndex._point_id(u2, "kX")


async def test_ingest_stamps_tenant_and_user_payload() -> None:
    tid, uid = uuid4(), uuid4()
    store = _FakeMemStore()
    await _index(store).search(
        tenant_id=tid, user_id=uid, rows=_rows("stamped fact"), query="stamped fact", top_k=1
    )
    coll = next(iter(store.collections))
    payload = store.collections[coll][0][2]
    assert payload["tenant_id"] == str(tid)
    assert payload["user_id"] == str(uid)
    assert payload["dedup_key"] == "k0"
    assert payload["content"] == "stamped fact"


# --- per-user isolation inside a shared per-tenant collection -------------------


async def test_user_a_cannot_retrieve_user_b_fact() -> None:
    """THE isolation proof: two users, one tenant collection, isolated by the payload filter."""
    tid = uuid4()
    u_a, u_b = uuid4(), uuid4()
    store = _FakeMemStore()
    index = _index(store)
    secret_b = "user B secret only B knows this phrase"
    await index.search(
        tenant_id=tid, user_id=u_b, rows=[MemoryRow("kb", secret_b, 0.9)], query=secret_b, top_k=5
    )
    # user A (same tenant) searches for B's exact fact → 0 hits (own rows only, and A has none here)
    a_hits = await index.search(
        tenant_id=tid,
        user_id=u_a,
        rows=[MemoryRow("ka", "user A owns a totally different fact", 0.5)],
        query=secret_b,
        top_k=5,
    )
    assert all(h.content != secret_b for h in a_hits)
    # both users' points live in the ONE per-tenant collection (isolation by filter, not collection)
    coll = next(iter(store.collections))
    assert len(store.collections[coll]) == 2
