"""
File: backend/src/api/v1/chat/knowledge_index.py
Purpose: Process-wide KnowledgeVectorIndex singleton builder (api composition layer).
Category: API / chat composition (wires adapters + infra + business_domain)
Scope: Phase 57 / Sprint 57.146

Description:
    The composition root for the Slice-2 knowledge vector path. Builds (once per
    process) the AzureOpenAIEmbeddingClient + QdrantVectorStore + LocalDocsConnector
    + KnowledgeVectorIndex when KNOWLEDGE_VECTOR_ENABLED is on AND the embedding
    deployment + Qdrant URL are configured. Returns None otherwise (flag off /
    unconfigured) so the chat handler degrades to the 57.145 keyword path with
    ZERO added cost — the heavy adapter / Qdrant imports load only when enabled.
    Kept in the api layer (not business_domain) so the domain stays
    adapter-agnostic — it sees only the EmbeddingClient ABC.

    Both build_real_llm_handler (passes the index into make_default_executor) and
    api/main.py (_lifespan startup ingest) consume get_knowledge_vector_index().

Key Components:
    - get_knowledge_vector_index() -> KnowledgeVectorIndex | None  (memoized)
    - reset_knowledge_vector_index()  (test hook)

Created: 2026-06-27 (Sprint 57.146)
Last Modified: 2026-06-27

Modification History (newest-first):
    - 2026-06-27: Initial creation (Sprint 57.146) — vector-index composition singleton
      (AD-Knowledge-Connector-First-Real-Source Slice 2)

Related:
    - business_domain/knowledge/vector_index.py — KnowledgeVectorIndex
    - business_domain/_register_all.py — make_default_executor(knowledge_vector_index=...)
    - api/main.py — _lifespan startup ingest
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from core.config import get_settings

if TYPE_CHECKING:
    from business_domain.knowledge.vector_index import KnowledgeVectorIndex

logger = logging.getLogger(__name__)

_built = False
_singleton: "KnowledgeVectorIndex | None" = None


def get_knowledge_vector_index() -> "KnowledgeVectorIndex | None":
    """Return the process-wide knowledge vector index (None when disabled/unconfigured).

    Memoized: built once on first call. Flag off → None, and the heavy imports
    (Azure adapter / Qdrant client) are never loaded (zero added cost when off).
    """
    global _built, _singleton
    if _built:
        return _singleton
    _built = True

    settings = get_settings()
    if not settings.knowledge_vector_enabled:
        return None

    # Lazy imports — load the adapter / Qdrant client only when actually enabled.
    from adapters.azure_openai.config import AzureOpenAIConfig
    from adapters.azure_openai.embeddings import AzureOpenAIEmbeddingClient
    from business_domain.knowledge.connector import LocalDocsConnector
    from business_domain.knowledge.vector_index import KnowledgeVectorIndex
    from infrastructure.vector.qdrant_client import QdrantVectorStore

    config = AzureOpenAIConfig()
    if not config.is_embedding_configured() or not settings.qdrant_url:
        logger.warning(
            "knowledge vector path enabled but not configured "
            "(AZURE_OPENAI_EMBEDDING_DEPLOYMENT / QDRANT_URL); using keyword fallback"
        )
        return None
    try:
        connector = LocalDocsConnector(settings.knowledge_docs_root)
    except ValueError:
        logger.warning("knowledge docs root missing; vector index disabled")
        return None

    _singleton = KnowledgeVectorIndex(
        AzureOpenAIEmbeddingClient(config),
        QdrantVectorStore(settings.qdrant_url),
        connector,
    )
    logger.info("knowledge vector index built (model=%s)", config.deployment_embedding)
    return _singleton


def reset_knowledge_vector_index() -> None:
    """Test hook: clear the memoized singleton so the next call rebuilds from settings."""
    global _built, _singleton
    _built = False
    _singleton = None
