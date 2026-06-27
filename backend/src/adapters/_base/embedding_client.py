"""
File: backend/src/adapters/_base/embedding_client.py
Purpose: EmbeddingClient ABC — the LLM-provider-neutral embedding interface (sibling of ChatClient).
Category: Adapters (LLM provider boundary; per 10-server-side-philosophy.md §原則 2)
Scope: Phase 57 / Sprint 57.146

Description:
    THE single embedding interface. Code that needs vector embeddings (the
    Cat 2 knowledge connector now; the Cat 3 memory semantic axis later)
    depends only on this ABC. Concrete adapters (azure_openai) live in sibling
    directories and confine the provider SDK there (check_llm_sdk_leak rule —
    business_domain / agent_harness must never import an LLM SDK directly).

    Minimal by design (KISS): one batch embed + a model_name for trace/cost.
    The vector dimension is derived by the consumer from len(vectors[0]) at
    ingest time — no hardcoded dim, no extra method.

Key Components:
    - EmbeddingClient: ABC with embed() + model_name()

Created: 2026-06-27 (Sprint 57.146)
Last Modified: 2026-06-27

Modification History (newest-first):
    - 2026-06-27: Initial creation (Sprint 57.146) — first embedding ABC
      (AD-Knowledge-Connector-First-Real-Source Slice 2)

Related:
    - chat_client.py — sibling ABC (the chat interface)
    - adapters/azure_openai/embeddings.py — Azure concrete impl
    - adapters/_testing/embedding.py — DeterministicEmbeddingClient test double
    - 10-server-side-philosophy.md §原則 2 (LLM Provider Neutrality)
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class EmbeddingClient(ABC):
    """LLM-neutral embedding client. THE only embedding interface for non-adapter code."""

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts → one vector per text, order-preserving.

        All returned vectors share the same dimension (the model's). An empty
        input returns an empty list. Implementations confine any provider SDK
        to their own adapters/<provider>/ module.
        """
        ...

    @abstractmethod
    def model_name(self) -> str:
        """Return the embedding model identifier (for trace / cost attribution)."""
        ...
