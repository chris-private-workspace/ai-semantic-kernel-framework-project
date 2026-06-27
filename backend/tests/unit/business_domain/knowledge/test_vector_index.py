"""
File: backend/tests/unit/business_domain/knowledge/test_vector_index.py
Purpose: Unit tests for KnowledgeVectorIndex (Sprint 57.146 — deterministic embed + fake store).
Category: Tests
Created: 2026-06-27
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, cast

from adapters._testing.embedding import DeterministicEmbeddingClient
from business_domain.knowledge.connector import LocalDocsConnector
from business_domain.knowledge.vector_index import KnowledgeVectorIndex
from infrastructure.vector.qdrant_client import VectorHit


def _write(root: Path, rel: str, content: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def _cos(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


class _FakeStore:
    """In-memory async stand-in for QdrantVectorStore."""

    def __init__(self) -> None:
        self.points: list[tuple[int, list[float], dict[str, Any]]] = []
        self.dim: int | None = None

    async def count(self, name: str) -> int:
        return len(self.points)

    async def ensure_collection(self, name: str, dim: int) -> None:
        self.dim = dim

    async def recreate_collection(self, name: str, dim: int) -> None:
        self.points = []
        self.dim = dim

    async def upsert(
        self, name: str, points: list[tuple[int, list[float], dict[str, Any]]]
    ) -> None:
        self.points.extend(points)

    async def search(
        self,
        name: str,
        query_vector: list[float],
        top_k: int,
        payload_filter: Any = None,
    ) -> list[VectorHit]:
        ranked = sorted(self.points, key=lambda p: _cos(query_vector, p[1]), reverse=True)[:top_k]
        return [
            VectorHit(payload=payload, score=_cos(query_vector, vec))
            for (_, vec, payload) in ranked
        ]


def _index(tmp_path: Path, store: _FakeStore, dim: int = 48) -> KnowledgeVectorIndex:
    return KnowledgeVectorIndex(
        DeterministicEmbeddingClient(dim=dim),
        cast(Any, store),
        LocalDocsConnector(tmp_path),
    )


async def test_ingest_counts_sections() -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "doc.md", "## A\nbody a\n## B\nbody b\n")
        store = _FakeStore()
        assert await _index(root, store).ingest() == 2  # 2 sections (A, B)
        assert len(store.points) == 2


async def test_ingest_idempotent_skips_reembed() -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "doc.md", "## A\nbody a\n## B\nbody b\n")
        store = _FakeStore()
        index = _index(root, store)
        assert await index.ingest() == 2
        before = len(store.points)
        assert await index.ingest() == 2  # count matches → idempotent no-op
        assert len(store.points) == before  # not re-upserted


async def test_ingest_empty_corpus_returns_zero() -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        assert await _index(Path(d), _FakeStore()).ingest() == 0


async def test_search_exact_section_ranks_first() -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "doc.md", "# T\n## Alpha\nalpha body content\n## Beta\nbeta body content\n")
        store = _FakeStore()
        index = _index(root, store)
        await index.ingest()
        # Query with the EXACT Alpha section body → identical embedding → cosine 1.0 → first.
        hits = await index.search("## Alpha\nalpha body content", top_k=2)
        assert hits
        assert hits[0].source == "doc.md"
        assert "Alpha" in hits[0].snippet
        assert math.isclose(hits[0].score, 1.0, rel_tol=1e-6)


async def test_search_empty_query_returns_empty() -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "doc.md", "## A\nbody\n")
        assert await _index(root, _FakeStore()).search("   ") == []


class _CountingEmbedder:
    """Wraps the deterministic embedder + records each batch size (Sprint 57.146)."""

    def __init__(self, dim: int = 16) -> None:
        self._inner = DeterministicEmbeddingClient(dim=dim)
        self.batch_sizes: list[int] = []

    async def embed(self, texts: list[str]) -> list[list[float]]:
        self.batch_sizes.append(len(texts))
        return await self._inner.embed(texts)

    def model_name(self) -> str:
        return "counting"


async def test_ingest_batches_embedding_calls() -> None:
    """Sprint 57.146 Day-3 fix: ingest embeds in _EMBED_BATCH chunks (one giant
    all-sections call returned HTTP 429 on the real embedding deployment)."""
    import tempfile

    from business_domain.knowledge.vector_index import _EMBED_BATCH

    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        n = _EMBED_BATCH + 4  # crosses the batch boundary → expect 2 calls
        _write(root, "big.md", "".join(f"## S{i}\nbody {i} content\n" for i in range(n)))
        store = _FakeStore()
        embedder = _CountingEmbedder()
        index = KnowledgeVectorIndex(
            cast(Any, embedder), cast(Any, store), LocalDocsConnector(root)
        )
        assert await index.ingest() == n
        assert len(store.points) == n  # all sections upserted across batches
        assert embedder.batch_sizes == [_EMBED_BATCH, 4]  # batched, not one call
