"""
File: backend/src/adapters/_testing/embedding.py
Purpose: DeterministicEmbeddingClient — offline EmbeddingClient test double (no network).
Category: Adapters / Testing helpers
Scope: Phase 57 / Sprint 57.146

Description:
    Drop-in EmbeddingClient ABC implementation that does NOT call any provider.
    Each text maps to a fixed-dim unit vector derived from its sha256 digest,
    so identical texts embed identically and the knowledge vector index /
    search path can be exercised end-to-end without Azure (critical for AP-10:
    mock + real share the ABC, so mock-only tests catch interface drift).
    NOT used in production wiring.

Key Components:
    - DeterministicEmbeddingClient: hash → fixed-dim L2-normalized vector

Created: 2026-06-27 (Sprint 57.146)
Last Modified: 2026-06-27

Modification History (newest-first):
    - 2026-06-27: Initial creation (Sprint 57.146) — embedding test double
      (AD-Knowledge-Connector-First-Real-Source Slice 2)

Related:
    - adapters/_base/embedding_client.py — ABC owner
    - adapters/_testing/mock_clients.py — sibling MockChatClient
"""

from __future__ import annotations

import hashlib
import math

from adapters._base.embedding_client import EmbeddingClient


class DeterministicEmbeddingClient(EmbeddingClient):
    """Hash-based EmbeddingClient for unit tests. Deterministic, no network."""

    def __init__(self, dim: int = 64) -> None:
        if dim <= 0:
            raise ValueError("DeterministicEmbeddingClient: dim must be positive")
        self._dim = dim

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(t) for t in texts]

    def _vector(self, text: str) -> list[float]:
        # Expand the digest to >= dim bytes, map each to [-1, 1], then L2-normalize.
        raw = bytearray()
        counter = 0
        while len(raw) < self._dim:
            raw.extend(hashlib.sha256(f"{counter}:{text}".encode("utf-8")).digest())
            counter += 1
        vals = [(b / 127.5) - 1.0 for b in raw[: self._dim]]
        norm = math.sqrt(sum(v * v for v in vals)) or 1.0
        return [v / norm for v in vals]

    def model_name(self) -> str:
        return f"deterministic-{self._dim}d"
