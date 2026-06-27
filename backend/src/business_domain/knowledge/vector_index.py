"""
File: backend/src/business_domain/knowledge/vector_index.py
Purpose: KnowledgeVectorIndex — embed doc sections into Qdrant + answer semantic queries.
Category: Business domain / knowledge (Cat 2 Tools — semantic retrieval)
Scope: Phase 57 / Sprint 57.146

Description:
    Slice-2 semantic retrieval over the same real .md/.txt corpus the 57.145
    keyword connector reads. Composes a provider-neutral EmbeddingClient (the
    ABC, NOT a concrete adapter — neutrality) + a QdrantVectorStore + the
    LocalDocsConnector. ingest() chunks each doc into ## sections, batch-embeds
    the section bodies, and upserts them; search() embeds the query and returns
    cosine-ranked KnowledgeHit(s). Single shared collection (per-tenant
    isolation is Slice 3).

Key Components:
    - KnowledgeVectorIndex: ingest() (idempotent) + search(query, top_k)

Created: 2026-06-27 (Sprint 57.146)
Last Modified: 2026-06-27

Modification History (newest-first):
    - 2026-06-27: Initial creation (Sprint 57.146) — embedding/Qdrant semantic index
      (AD-Knowledge-Connector-First-Real-Source Slice 2)

Related:
    - adapters/_base/embedding_client.py — EmbeddingClient ABC
    - infrastructure/vector/qdrant_client.py — QdrantVectorStore
    - chunking.py — section unit · connector.py — KnowledgeHit + file source
"""

from __future__ import annotations

import logging

from adapters._base.embedding_client import EmbeddingClient
from infrastructure.vector.qdrant_client import QdrantVectorStore

from .chunking import split_sections
from .connector import KnowledgeHit, LocalDocsConnector

logger = logging.getLogger(__name__)

_DEFAULT_COLLECTION = "knowledge_local_docs"
# Embed in small batches so a one-shot ingest of the whole corpus stays under the
# embedding deployment's tokens-per-minute quota. A single all-sections request
# returns HTTP 429 (Sprint 57.146 Day-3 drive-through finding); 16 sections
# (~6k tokens) per call fits comfortably and the SDK retries any residual 429.
_EMBED_BATCH = 16


class KnowledgeVectorIndex:
    """Embeds doc sections into Qdrant + answers semantic queries over them."""

    def __init__(
        self,
        embedder: EmbeddingClient,
        store: QdrantVectorStore,
        connector: LocalDocsConnector,
        *,
        collection: str = _DEFAULT_COLLECTION,
    ) -> None:
        self._embedder = embedder
        self._store = store
        self._connector = connector
        self._collection = collection

    def _sections(self) -> list[tuple[str, str]]:
        """Return (source_rel, section_body) pairs across every doc under the root."""
        pairs: list[tuple[str, str]] = []
        for path in self._connector.list_files():
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            rel = path.relative_to(self._connector.root).as_posix()
            for section in split_sections(text):
                pairs.append((rel, section.body))
        return pairs

    async def ingest(self) -> int:
        """Embed all sections + upsert into Qdrant. Idempotent. Returns section count.

        Skips re-embedding when the collection already holds the expected count.
        Otherwise recreates the collection (clean dim on a corpus / model change)
        and upserts. Sections are embedded in `_EMBED_BATCH`-sized batches to stay
        under the deployment's TPM quota. The dimension is derived from the first
        embedding.
        """
        pairs = self._sections()
        if not pairs:
            return 0
        expected = len(pairs)
        if await self._store.count(self._collection) == expected:
            return expected  # already ingested — idempotent no-op
        bodies = [body for _, body in pairs]
        vectors: list[list[float]] = []
        for start in range(0, len(bodies), _EMBED_BATCH):
            vectors.extend(await self._embedder.embed(bodies[start : start + _EMBED_BATCH]))
        if not vectors:
            return 0
        dim = len(vectors[0])
        await self._store.recreate_collection(self._collection, dim)
        points = [
            (idx, vectors[idx], {"source": src, "snippet": body})
            for idx, (src, body) in enumerate(pairs)
        ]
        await self._store.upsert(self._collection, points)
        logger.info("knowledge vector index ingested %d sections", expected)
        return expected

    async def search(self, query: str, top_k: int = 5) -> list[KnowledgeHit]:
        """Embed the query → Qdrant cosine top-k → KnowledgeHit per matched section."""
        if not query.strip():
            return []
        vectors = await self._embedder.embed([query])
        if not vectors:
            return []
        hits = await self._store.search(self._collection, vectors[0], top_k=top_k)
        return [
            KnowledgeHit(
                source=str(hit.payload.get("source", "")),
                snippet=str(hit.payload.get("snippet", "")),
                score=round(float(hit.score), 3),
            )
            for hit in hits
        ]


__all__ = ["KnowledgeVectorIndex"]
