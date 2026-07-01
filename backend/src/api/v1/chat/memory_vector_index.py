"""
File: backend/src/api/v1/chat/memory_vector_index.py
Purpose: Process-wide MemoryVectorIndex singleton builder (api composition layer).
Category: API / chat composition (wires adapters + infra into the Cat 3 memory semantic axis)
Scope: Phase 57 / Sprint 57.155

Description:
    The composition root for the CARRY-026 Slice 1 memory semantic axis. Builds (once
    per process) the AzureOpenAIEmbeddingClient + QdrantVectorStore + MemoryVectorIndex
    when MEMORY_VECTOR_ENABLED is on AND the embedding deployment + Qdrant URL are
    configured. Returns None otherwise (flag off / unconfigured) so make_chat_memory_deps
    builds the UserLayer WITHOUT an index → the 57.150 keyword/ILIKE path with ZERO
    added cost (the heavy adapter / Qdrant imports load only when enabled). Kept in the
    api layer (not agent_harness) so the memory domain sees only the EmbeddingClient ABC
    (神經性中立 / 約束 3) — mirrors knowledge_index.py.

Key Components:
    - get_memory_vector_index() -> MemoryVectorIndex | None  (memoized)
    - reset_memory_vector_index()  (test hook)

Created: 2026-07-01 (Sprint 57.155)
Last Modified: 2026-07-01

Modification History (newest-first):
    - 2026-07-01: Initial creation (Sprint 57.155) — memory vector-index composition
      singleton (CARRY-026 Slice 1, L4 user semantic axis)

Related:
    - agent_harness/memory/vector_index.py — MemoryVectorIndex
    - api/v1/chat/knowledge_index.py — the mirrored knowledge singleton
    - api/v1/chat/_category_factories.py — make_chat_memory_deps consumes it
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from core.config import get_settings

if TYPE_CHECKING:
    from agent_harness.memory.vector_index import MemoryVectorIndex

logger = logging.getLogger(__name__)

_built = False
_singleton: "MemoryVectorIndex | None" = None


def get_memory_vector_index() -> "MemoryVectorIndex | None":
    """Return the process-wide memory vector index (None when disabled/unconfigured).

    Memoized: built once on first call. Flag off → None, and the heavy imports
    (Azure adapter / Qdrant client) are never loaded (zero added cost when off).
    """
    global _built, _singleton
    if _built:
        return _singleton
    _built = True

    settings = get_settings()
    if not settings.memory_vector_enabled:
        return None

    # Lazy imports — load the adapter / Qdrant client only when actually enabled.
    from adapters.azure_openai.config import AzureOpenAIConfig
    from adapters.azure_openai.embeddings import AzureOpenAIEmbeddingClient
    from agent_harness.memory.vector_index import MemoryVectorIndex
    from infrastructure.vector.qdrant_client import QdrantVectorStore

    config = AzureOpenAIConfig()
    if not config.is_embedding_configured() or not settings.qdrant_url:
        logger.warning(
            "memory vector path enabled but not configured "
            "(AZURE_OPENAI_DEPLOYMENT_EMBEDDING / QDRANT_URL); using keyword fallback"
        )
        return None

    _singleton = MemoryVectorIndex(
        AzureOpenAIEmbeddingClient(config),
        QdrantVectorStore(settings.qdrant_url),
    )
    logger.info("memory vector index built (model=%s)", config.deployment_embedding)
    return _singleton


def reset_memory_vector_index() -> None:
    """Test hook: clear the memoized singleton so the next call rebuilds from settings."""
    global _built, _singleton
    _built = False
    _singleton = None
