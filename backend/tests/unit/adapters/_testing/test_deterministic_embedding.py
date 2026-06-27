"""
File: backend/tests/unit/adapters/_testing/test_deterministic_embedding.py
Purpose: Unit tests for DeterministicEmbeddingClient (Sprint 57.146).
Category: Tests
Created: 2026-06-27
"""

from __future__ import annotations

import math

import pytest

from adapters._testing.embedding import DeterministicEmbeddingClient


async def test_deterministic_same_text_same_vector() -> None:
    c = DeterministicEmbeddingClient(dim=32)
    a = await c.embed(["hello world"])
    b = await c.embed(["hello world"])
    assert a == b
    assert a[0] != (await c.embed(["different"]))[0]


async def test_dimension_and_unit_norm() -> None:
    c = DeterministicEmbeddingClient(dim=48)
    [v] = await c.embed(["some text"])
    assert len(v) == 48
    assert math.isclose(math.sqrt(sum(x * x for x in v)), 1.0, rel_tol=1e-9)


async def test_empty_input_returns_empty() -> None:
    assert await DeterministicEmbeddingClient().embed([]) == []


async def test_batch_order_preserved() -> None:
    c = DeterministicEmbeddingClient(dim=16)
    out = await c.embed(["a", "b", "c"])
    assert len(out) == 3
    assert out[0] == (await c.embed(["a"]))[0]
    assert out[2] == (await c.embed(["c"]))[0]


def test_invalid_dim_raises() -> None:
    with pytest.raises(ValueError):
        DeterministicEmbeddingClient(dim=0)


def test_model_name() -> None:
    assert DeterministicEmbeddingClient(dim=64).model_name() == "deterministic-64d"
