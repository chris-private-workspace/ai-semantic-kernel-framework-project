"""
File: backend/src/agent_harness/memory/vector_index.py
Purpose: MemoryVectorIndex — per-tenant+user Qdrant embedding + semantic recall over memory rows.
Category: 範疇 3 (Memory) — semantic axis (CARRY-026 Slice 1, L4 user)
Scope: Phase 57 / Sprint 57.155

Description:
    The Cat 3 memory semantic axis (CARRY-026, logged Sprint 51.2, infra unblocked
    by 57.146/57.147). Mirrors business_domain/knowledge/vector_index.py but ingests
    caller-supplied rows (memory_user facts) rather than disk docs. Composes a
    provider-neutral EmbeddingClient (the ABC, NOT a concrete adapter — 約束 3
    neutrality) + a QdrantVectorStore + QdrantNamespaceStrategy's "user_memory"
    layer. search() lazily ensures the user's rows are embedded + upserted
    (idempotent via a PER-USER count guard) then returns cosine-ranked hits.

    Isolation (two independent mechanisms, mirroring 57.147): the collection is
    per-tenant (`tenant_<hex>_user_memory`) AND every search + count carries a
    tenant_id+user_id payload filter, so one user cannot retrieve another's facts
    even though a tenant collection holds all its users' points. Point ids derive
    from (user_id, dedup_key) so two users' identical facts are distinct points and
    re-ingest is a stable upsert (no duplicate points across re-ingests).

    Design (vs embed-on-write): lazy ingest-on-search does NOT touch the 57.150
    write-path upsert and backfills pre-flag rows for free; the per-user count guard
    keeps steady-state embedding cost near-zero (facts are add-mostly — there is no
    user-memory delete path today, so count(Qdrant, user) == len(rows) in steady
    state; an incremental embed-on-write + orphan cleanup is a noted follow-on).

Key Components:
    - MemoryRow: one user fact to embed (dedup_key + content + confidence)
    - MemoryVectorHit: one semantic recall result (dedup_key + content + confidence + cosine)
    - MemoryVectorIndex: search(tenant_id, user_id, rows, query, top_k) — lazy ingest + cosine query

Created: 2026-07-01 (Sprint 57.155)
Last Modified: 2026-07-01

Modification History (newest-first):
    - 2026-07-01: Initial creation (Sprint 57.155) — CARRY-026 Slice 1 (L4 user semantic axis)

Related:
    - adapters/_base/embedding_client.py — EmbeddingClient ABC (reused unchanged)
    - infrastructure/vector/qdrant_client.py — QdrantVectorStore (reused; count += payload_filter)
    - infrastructure/vector/qdrant_namespace.py — "user_memory" layer naming + payload filter
    - business_domain/knowledge/vector_index.py — the mirrored shape (57.146/57.147)
    - memory/layers/user_layer.py — the consumer (read() semantic branch)
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from adapters._base.embedding_client import EmbeddingClient
from infrastructure.vector.qdrant_client import QdrantVectorStore
from infrastructure.vector.qdrant_namespace import MemoryLayer, QdrantNamespaceStrategy

logger = logging.getLogger(__name__)

# Embed in small batches so a one-shot ingest stays under the embedding deployment's
# tokens-per-minute quota (a single all-rows request returns HTTP 429 — the 57.146
# Day-3 drive-through finding; 16 rows fit comfortably + the SDK retries residual 429s).
_EMBED_BATCH = 16
# The QdrantNamespaceStrategy layer this slice writes to (49.3 reserved it for exactly this).
_LAYER: MemoryLayer = "user_memory"


@dataclass(frozen=True)
class MemoryRow:
    """One user-memory fact to embed: its stable dedup key (57.150) + content + confidence."""

    dedup_key: str
    content: str
    confidence: float


@dataclass(frozen=True)
class MemoryVectorHit:
    """One semantic recall result: dedup_key (for hint mapping) + content + confidence + cosine."""

    dedup_key: str
    content: str
    confidence: float
    score: float


class MemoryVectorIndex:
    """Embeds a user's memory rows into a per-tenant Qdrant collection + answers semantic queries.

    Mirrors KnowledgeVectorIndex; the only structural difference is the corpus —
    caller-supplied `rows` (memory_user facts) rather than disk docs. Reuses the
    EmbeddingClient ABC, QdrantVectorStore, and the "user_memory" namespace unchanged.
    """

    def __init__(self, embedder: EmbeddingClient, store: QdrantVectorStore) -> None:
        self._embedder = embedder
        self._store = store

    @staticmethod
    def _point_id(user_id: UUID, dedup_key: str) -> int:
        """Stable, per-user-unique 64-bit point id from (user_id, dedup_key).

        Incorporating user_id keeps two users' identical facts as distinct points in
        the shared per-tenant collection; deriving from the 57.150 dedup_key makes
        re-ingest a stable upsert (same fact → same point). md5 is a non-cryptographic
        id hash here (usedforsecurity=False), not a security primitive.
        """
        digest = hashlib.md5(f"{user_id}:{dedup_key}".encode(), usedforsecurity=False).hexdigest()
        return int(digest[:16], 16)

    @staticmethod
    def _user_filter(tenant_id: UUID, user_id: UUID) -> dict[str, Any]:
        """Two-key payload filter (tenant_id AND user_id) for per-user isolation."""
        return {
            "must": [
                {"key": "tenant_id", "match": {"value": str(tenant_id)}},
                {"key": "user_id", "match": {"value": str(user_id)}},
            ]
        }

    async def _ingest(
        self, collection: str, tenant_id: UUID, user_id: UUID, rows: list[MemoryRow]
    ) -> None:
        """Ensure the user's rows are embedded + upserted. Idempotent via a per-user count guard.

        Skips re-embedding when the collection already holds this user's expected count
        (the count is scoped by the tenant_id+user_id payload filter — a plain
        collection count would see every user's points). Otherwise embeds in
        `_EMBED_BATCH`-sized batches + upserts. Each point stamps tenant_id+user_id so
        the search-time payload filter rejects any cross-user row (defense-in-depth on
        top of the per-tenant collection name).
        """
        expected = len(rows)
        user_filter = self._user_filter(tenant_id, user_id)
        if await self._store.count(collection, payload_filter=user_filter) == expected:
            return  # already ingested for this user — idempotent no-op (no embed)
        bodies = [row.content for row in rows]
        vectors: list[list[float]] = []
        for start in range(0, len(bodies), _EMBED_BATCH):
            vectors.extend(await self._embedder.embed(bodies[start : start + _EMBED_BATCH]))
        if not vectors:
            return
        dim = len(vectors[0])
        await self._store.ensure_collection(collection, dim)
        points = [
            (
                self._point_id(user_id, row.dedup_key),
                vectors[idx],
                {
                    "tenant_id": str(tenant_id),
                    "user_id": str(user_id),
                    "content": row.content,
                    "confidence": float(row.confidence),
                    "dedup_key": row.dedup_key,
                },
            )
            for idx, row in enumerate(rows)
        ]
        await self._store.upsert(collection, points)
        logger.info(
            "memory vector index ingested %d rows (tenant=%s user=%s)",
            expected,
            tenant_id,
            user_id,
        )

    async def search(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        rows: list[MemoryRow],
        query: str,
        top_k: int = 5,
    ) -> list[MemoryVectorHit]:
        """Embed the query → the user's per-tenant Qdrant collection cosine top-k → hits.

        Lazily ensures the user's rows are ingested first (idempotent). The search is
        scoped to the tenant collection AND carries the tenant_id+user_id payload
        filter — two independent isolation mechanisms.
        """
        if not rows or not query.strip():
            return []
        collection = QdrantNamespaceStrategy.collection_name(tenant_id, _LAYER)
        await self._ingest(collection, tenant_id, user_id, rows)
        qvecs = await self._embedder.embed([query])
        if not qvecs:
            return []
        hits = await self._store.search(
            collection,
            qvecs[0],
            top_k=top_k,
            payload_filter=self._user_filter(tenant_id, user_id),
        )
        return [
            MemoryVectorHit(
                dedup_key=str(hit.payload.get("dedup_key", "")),
                content=str(hit.payload.get("content", "")),
                confidence=float(hit.payload.get("confidence", 0.0)),
                score=round(float(hit.score), 3),
            )
            for hit in hits
        ]


__all__ = ["MemoryRow", "MemoryVectorHit", "MemoryVectorIndex"]
