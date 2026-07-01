"""
File: backend/tests/unit/api/v1/chat/test_memory_vector_index_singleton.py
Purpose: Unit tests for get_memory_vector_index() composition singleton (Sprint 57.155).
Category: Tests
Created: 2026-07-01
"""

from __future__ import annotations

import pytest

from api.v1.chat.memory_vector_index import (
    get_memory_vector_index,
    reset_memory_vector_index,
)
from core.config import get_settings

_IS_CONFIGURED = "adapters.azure_openai.config.AzureOpenAIConfig.is_embedding_configured"


@pytest.fixture(autouse=True)
def _reset_singleton() -> object:
    get_settings.cache_clear()
    reset_memory_vector_index()
    yield
    get_settings.cache_clear()
    reset_memory_vector_index()


def test_flag_off_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MEMORY_VECTOR_ENABLED", "false")
    get_settings.cache_clear()
    reset_memory_vector_index()
    assert get_memory_vector_index() is None


def test_flag_on_unconfigured_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MEMORY_VECTOR_ENABLED", "true")
    monkeypatch.setattr(_IS_CONFIGURED, lambda self: False)
    get_settings.cache_clear()
    reset_memory_vector_index()
    assert (
        get_memory_vector_index() is None
    )  # flag on but no embedding deployment → keyword fallback


def test_flag_on_configured_builds_and_memoizes(monkeypatch: pytest.MonkeyPatch) -> None:
    from agent_harness.memory.vector_index import MemoryVectorIndex

    monkeypatch.setenv("MEMORY_VECTOR_ENABLED", "true")
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")
    monkeypatch.setattr(_IS_CONFIGURED, lambda self: True)
    get_settings.cache_clear()
    reset_memory_vector_index()
    idx = get_memory_vector_index()  # ctors are lazy → no real Azure/Qdrant connection
    assert isinstance(idx, MemoryVectorIndex)
    assert get_memory_vector_index() is idx  # memoized (built once)
