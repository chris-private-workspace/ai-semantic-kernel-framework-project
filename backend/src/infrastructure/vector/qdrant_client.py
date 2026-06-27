"""
File: backend/src/infrastructure/vector/qdrant_client.py
Purpose: QdrantVectorStore — thin async wrapper over the Qdrant client (ensure/upsert/search).
Category: Infrastructure / Vector
Scope: Phase 57 / Sprint 57.146

Description:
    The Qdrant client integration deferred since Sprint 49.3 (CARRY-026). Wraps
    the synchronous qdrant-client SDK in asyncio.to_thread (mirrors the docker
    SDK pattern) so callers stay async. Consumed by the Cat 2 knowledge vector
    index now; the Cat 3 memory semantic axis can reuse it later (it already
    accepts a payload_filter in the QdrantNamespaceStrategy shape for per-tenant
    isolation — default None for the single shared knowledge collection here).

Key Components:
    - VectorHit: one search result (payload dict + cosine score)
    - QdrantVectorStore: ensure_collection / recreate_collection / count / upsert / search

Created: 2026-06-27 (Sprint 57.146)
Last Modified: 2026-06-27

Modification History (newest-first):
    - 2026-06-27: Initial creation (Sprint 57.146) — first real Qdrant client
      (AD-Knowledge-Connector-First-Real-Source Slice 2; closes CARRY-026 for KB)

Related:
    - qdrant_namespace.py — per-tenant collection naming + payload filter (Slice 3)
    - business_domain/knowledge/vector_index.py — primary consumer
    - infrastructure/vector/README.md — Phase 51.2 planned API
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from qdrant_client import QdrantClient, models


@dataclass(frozen=True)
class VectorHit:
    """One Qdrant search result: the stored payload + its cosine similarity score."""

    payload: dict[str, Any]
    score: float


class QdrantVectorStore:
    """Async wrapper over qdrant-client (sync SDK offloaded via asyncio.to_thread)."""

    def __init__(self, url: str) -> None:
        self._url = url
        self._client: QdrantClient | None = None

    def _get_client(self) -> QdrantClient:
        if self._client is None:
            self._client = QdrantClient(url=self._url)
        return self._client

    async def ensure_collection(self, name: str, dim: int) -> None:
        """Create the cosine collection if it does not already exist (idempotent)."""

        def _ensure() -> None:
            client = self._get_client()
            if not client.collection_exists(name):
                client.create_collection(
                    collection_name=name,
                    vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE),
                )

        await asyncio.to_thread(_ensure)

    async def recreate_collection(self, name: str, dim: int) -> None:
        """Drop (if present) + create the collection — clean re-ingest / dim change."""

        def _recreate() -> None:
            client = self._get_client()
            if client.collection_exists(name):
                client.delete_collection(name)
            client.create_collection(
                collection_name=name,
                vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE),
            )

        await asyncio.to_thread(_recreate)

    async def count(self, name: str) -> int:
        """Number of points in the collection (0 if it does not exist)."""

        def _count() -> int:
            client = self._get_client()
            if not client.collection_exists(name):
                return 0
            return client.count(collection_name=name).count

        return await asyncio.to_thread(_count)

    async def upsert(
        self, name: str, points: list[tuple[int, list[float], dict[str, Any]]]
    ) -> None:
        """Upsert (id, vector, payload) points into the collection."""

        def _upsert() -> None:
            client = self._get_client()
            structs = [
                models.PointStruct(id=pid, vector=vec, payload=payload)
                for pid, vec, payload in points
            ]
            client.upsert(collection_name=name, points=structs)

        await asyncio.to_thread(_upsert)

    async def search(
        self,
        name: str,
        query_vector: list[float],
        top_k: int,
        payload_filter: dict[str, Any] | None = None,
    ) -> list[VectorHit]:
        """Cosine top-k search. payload_filter (Slice 3 per-tenant) defaults None."""

        def _search() -> list[VectorHit]:
            client = self._get_client()
            if not client.collection_exists(name):
                return []
            qfilter = models.Filter.model_validate(payload_filter) if payload_filter else None
            response = client.query_points(
                collection_name=name,
                query=query_vector,
                limit=top_k,
                query_filter=qfilter,
                with_payload=True,
            )
            return [
                VectorHit(payload=dict(point.payload or {}), score=float(point.score))
                for point in response.points
            ]

        return await asyncio.to_thread(_search)


__all__ = ["QdrantVectorStore", "VectorHit"]
