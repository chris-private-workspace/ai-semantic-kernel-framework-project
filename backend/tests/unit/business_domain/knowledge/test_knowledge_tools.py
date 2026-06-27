"""
File: backend/tests/unit/business_domain/knowledge/test_knowledge_tools.py
Purpose: Unit tests for knowledge_search ToolSpec + register_knowledge_tools (Sprint 57.145).
Category: Tests
Created: 2026-06-26
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from agent_harness._contracts import RiskLevel, ToolCall, ToolHITLPolicy
from agent_harness.tools import ToolHandler, ToolRegistryImpl
from business_domain.knowledge import (
    KNOWLEDGE_SEARCH_SPEC,
    make_knowledge_search_handler,
    register_knowledge_tools,
)
from business_domain.knowledge.connector import KnowledgeHit, LocalDocsConnector


def _write(root: Path, rel: str, content: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def test_spec_is_read_only_low_auto() -> None:
    s = KNOWLEDGE_SEARCH_SPEC
    assert s.name == "knowledge_search"
    assert s.annotations.read_only is True
    assert s.annotations.destructive is False
    assert s.annotations.open_world is True  # reads a real external data source
    assert s.risk_level == RiskLevel.LOW
    assert s.hitl_policy == ToolHITLPolicy.AUTO  # → auto-pass under default tenant policy


def test_spec_params_all_described() -> None:
    # 57.144 tool-description lint: every param must have a description.
    s = KNOWLEDGE_SEARCH_SPEC
    props = s.input_schema["properties"]
    assert s.input_schema["required"] == ["query"]
    assert all(props[k].get("description") for k in props)


@pytest.mark.asyncio
async def test_handler_returns_real_snippets(tmp_path: Path) -> None:
    _write(tmp_path, "guide.md", "# Guide\nthe magic keyword lives here")
    handler = make_knowledge_search_handler(LocalDocsConnector(tmp_path))
    out = await handler(
        ToolCall(id="t1", name="knowledge_search", arguments={"query": "magic keyword"})
    )
    payload = json.loads(out)
    assert payload["count"] == 1
    hit = payload["hits"][0]
    assert hit["source"] == "guide.md"
    assert "magic keyword" in hit["snippet"]
    assert hit["score"] > 0


@pytest.mark.asyncio
async def test_handler_empty_query(tmp_path: Path) -> None:
    _write(tmp_path, "a.md", "content")
    handler = make_knowledge_search_handler(LocalDocsConnector(tmp_path))
    out = await handler(ToolCall(id="t2", name="knowledge_search", arguments={"query": ""}))
    assert json.loads(out)["count"] == 0


@pytest.mark.asyncio
async def test_handler_invalid_top_k_falls_back(tmp_path: Path) -> None:
    _write(tmp_path, "a.md", "apple pie recipe")
    handler = make_knowledge_search_handler(LocalDocsConnector(tmp_path))
    out = await handler(
        ToolCall(id="t3", name="knowledge_search", arguments={"query": "apple", "top_k": "oops"})
    )
    assert json.loads(out)["count"] == 1  # bad top_k → default 5, still returns the hit


def test_register_mutates_registry_and_handlers(tmp_path: Path) -> None:
    _write(tmp_path, "a.md", "content")
    registry = ToolRegistryImpl()
    handlers: dict[str, ToolHandler] = {}
    register_knowledge_tools(registry, handlers, docs_root=tmp_path)
    assert "knowledge_search" in handlers
    assert any(t.name == "knowledge_search" for t in registry.list())


def test_register_missing_root_raises(tmp_path: Path) -> None:
    registry = ToolRegistryImpl()
    handlers: dict[str, ToolHandler] = {}
    with pytest.raises(ValueError):
        register_knowledge_tools(registry, handlers, docs_root=tmp_path / "nope")


class _FakeVectorIndex:
    """Stand-in for KnowledgeVectorIndex.search (Sprint 57.146)."""

    def __init__(self, hits: list[KnowledgeHit] | None = None, *, raises: bool = False) -> None:
        self._hits = hits or []
        self._raises = raises

    async def search(self, query: str, top_k: int = 5) -> list[KnowledgeHit]:
        if self._raises:
            raise RuntimeError("qdrant down")
        return self._hits


@pytest.mark.asyncio
async def test_handler_uses_vector_index_when_present(tmp_path: Path) -> None:
    _write(tmp_path, "kw.md", "keyword only term")  # keyword would match this
    fake = _FakeVectorIndex(
        [KnowledgeHit(source="vec.md", snippet="semantic section body", score=0.91)]
    )
    handler = make_knowledge_search_handler(LocalDocsConnector(tmp_path), cast(Any, fake))
    out = await handler(ToolCall(id="v1", name="knowledge_search", arguments={"query": "anything"}))
    payload = json.loads(out)
    assert payload["count"] == 1
    assert payload["hits"][0]["source"] == "vec.md"  # vector result, NOT keyword kw.md
    assert "semantic section body" in payload["hits"][0]["snippet"]


@pytest.mark.asyncio
async def test_handler_fails_soft_to_keyword_on_vector_error(tmp_path: Path) -> None:
    _write(tmp_path, "kw.md", "# Doc\nthe keyword fallback term here")
    fake = _FakeVectorIndex(raises=True)
    handler = make_knowledge_search_handler(LocalDocsConnector(tmp_path), cast(Any, fake))
    out = await handler(
        ToolCall(id="v2", name="knowledge_search", arguments={"query": "keyword fallback"})
    )
    payload = json.loads(out)
    assert payload["count"] == 1
    assert payload["hits"][0]["source"] == "kw.md"  # fell back to the keyword connector
