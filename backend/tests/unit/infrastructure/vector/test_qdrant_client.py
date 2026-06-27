"""
File: backend/tests/unit/infrastructure/vector/test_qdrant_client.py
Purpose: Unit tests for QdrantVectorStore (Sprint 57.146 — QdrantClient mocked, no live Qdrant).
Category: Tests
Created: 2026-06-27
"""

from __future__ import annotations

import math
from types import SimpleNamespace
from typing import Any, cast

from infrastructure.vector.qdrant_client import QdrantVectorStore


def _cos(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


class _FakeQdrant:
    """In-memory stand-in for qdrant_client.QdrantClient (sync surface)."""

    def __init__(self) -> None:
        self.collections: dict[str, list[tuple[int, list[float], dict[str, Any]]]] = {}
        self.created: list[tuple[str, int]] = []

    def collection_exists(self, name: str) -> bool:
        return name in self.collections

    def create_collection(self, collection_name: str, vectors_config: Any) -> None:
        self.collections.setdefault(collection_name, [])
        self.created.append((collection_name, vectors_config.size))

    def delete_collection(self, name: str) -> None:
        self.collections.pop(name, None)

    def count(self, collection_name: str) -> Any:
        return SimpleNamespace(count=len(self.collections.get(collection_name, [])))

    def upsert(self, collection_name: str, points: list[Any]) -> None:
        store = self.collections.setdefault(collection_name, [])
        for p in points:
            store.append((p.id, list(p.vector), dict(p.payload)))

    def query_points(
        self,
        collection_name: str,
        query: list[float],
        limit: int,
        query_filter: Any = None,
        with_payload: bool = True,
    ) -> Any:
        items = self.collections.get(collection_name, [])
        ranked = sorted(items, key=lambda it: _cos(query, it[1]), reverse=True)[:limit]
        pts = [
            SimpleNamespace(id=pid, score=_cos(query, vec), payload=payload)
            for (pid, vec, payload) in ranked
        ]
        return SimpleNamespace(points=pts)


def _store_with_fake() -> tuple[QdrantVectorStore, _FakeQdrant]:
    store = QdrantVectorStore(url="http://fake:6333")
    fake = _FakeQdrant()
    store._client = cast(Any, fake)
    return store, fake


async def test_ensure_collection_idempotent() -> None:
    store, fake = _store_with_fake()
    await store.ensure_collection("c", 4)
    await store.ensure_collection("c", 4)
    assert fake.created == [("c", 4)]  # created exactly once


async def test_upsert_and_count() -> None:
    store, _ = _store_with_fake()
    await store.ensure_collection("c", 2)
    await store.upsert("c", [(0, [1.0, 0.0], {"source": "a"}), (1, [0.0, 1.0], {"source": "b"})])
    assert await store.count("c") == 2
    assert await store.count("missing") == 0


async def test_search_ranks_by_cosine_and_maps_payload() -> None:
    store, _ = _store_with_fake()
    await store.ensure_collection("c", 2)
    await store.upsert("c", [(0, [1.0, 0.0], {"source": "x"}), (1, [0.0, 1.0], {"source": "y"})])
    hits = await store.search("c", [0.9, 0.1], top_k=2)
    assert len(hits) == 2
    assert hits[0].payload["source"] == "x"  # closest to [0.9, 0.1]
    assert hits[0].score >= hits[1].score


async def test_search_missing_collection_returns_empty() -> None:
    store, _ = _store_with_fake()
    assert await store.search("nope", [1.0, 0.0], top_k=5) == []


async def test_recreate_drops_then_creates() -> None:
    store, fake = _store_with_fake()
    await store.ensure_collection("c", 2)
    await store.upsert("c", [(0, [1.0, 0.0], {"source": "x"})])
    await store.recreate_collection("c", 3)
    assert await store.count("c") == 0  # dropped + recreated empty
    assert ("c", 3) in fake.created
