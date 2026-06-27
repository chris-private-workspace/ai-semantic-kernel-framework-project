"""
File: backend/tests/unit/adapters/azure_openai/test_embeddings.py
Purpose: Unit tests for AzureOpenAIEmbeddingClient (Sprint 57.146 — SDK mocked, no live Azure call).
Category: Tests
Created: 2026-06-27
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast

import pytest

from adapters.azure_openai.config import AzureOpenAIConfig
from adapters.azure_openai.embeddings import AzureOpenAIEmbeddingClient


def _cfg() -> AzureOpenAIConfig:
    return AzureOpenAIConfig(
        api_key="k",
        endpoint="https://x.openai.azure.com/",
        deployment_embedding="emb-deploy",
    )


class _FakeEmbeddings:
    def __init__(self, vectors: list[list[float]]) -> None:
        self._vectors = vectors
        self.calls: list[tuple[str, list[str]]] = []

    async def create(self, **kwargs: Any) -> Any:
        self.calls.append((kwargs["model"], list(kwargs["input"])))
        data = [SimpleNamespace(index=i, embedding=v) for i, v in enumerate(self._vectors)]
        # Return data REVERSED to prove the adapter re-sorts by .index.
        return SimpleNamespace(data=list(reversed(data)))


class _FakeClient:
    def __init__(self, vectors: list[list[float]]) -> None:
        self.embeddings = _FakeEmbeddings(vectors)

    async def close(self) -> None: ...


async def test_embed_batch_preserves_order() -> None:
    client = AzureOpenAIEmbeddingClient(_cfg())
    fake = _FakeClient([[1.0, 0.0], [0.0, 1.0], [0.5, 0.5]])
    client._client = cast(Any, fake)
    out = await client.embed(["a", "b", "c"])
    assert out == [[1.0, 0.0], [0.0, 1.0], [0.5, 0.5]]  # re-sorted by index despite reversed data
    assert fake.embeddings.calls[0] == ("emb-deploy", ["a", "b", "c"])


async def test_embed_empty_returns_empty_without_calling_sdk() -> None:
    client = AzureOpenAIEmbeddingClient(_cfg())
    fake = _FakeClient([])
    client._client = cast(Any, fake)
    assert await client.embed([]) == []
    assert fake.embeddings.calls == []  # short-circuits before the SDK


def test_is_embedding_configured() -> None:
    assert _cfg().is_embedding_configured() is True
    unconfigured = AzureOpenAIConfig(api_key="k", endpoint="e", deployment_embedding="")
    assert unconfigured.is_embedding_configured() is False


async def test_embed_unconfigured_raises() -> None:
    client = AzureOpenAIEmbeddingClient(
        AzureOpenAIConfig(api_key="", endpoint="", deployment_embedding="")
    )
    with pytest.raises(ValueError):
        await client.embed(["x"])


def test_model_name() -> None:
    assert AzureOpenAIEmbeddingClient(_cfg()).model_name() == "emb-deploy"
