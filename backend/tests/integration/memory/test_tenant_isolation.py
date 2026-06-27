"""
File: backend/tests/integration/memory/test_tenant_isolation.py
Purpose: Cross-tenant red-team tests for Cat 3 Memory layers + memory tools.
Category: Tests / Cat 3 / multi-tenant red-team
Scope: Phase 51 / Sprint 51.2 Day 5.1

Description:
    Verifies multi-tenant isolation at every memory access path:
    - SessionLayer composite key (tenant_id, session_id) blocks tenant_a
      from reading tenant_b's session entries.
    - UserLayer / TenantLayer stub-backed; query filter enforces tenant_id.
    - memory_search tool routes through MemoryRetrieval which passes
      tenant_id down.
    - MemoryExtractor writes carry only the originating session's tenant_id.

    Per sprint-51-2-plan.md acceptance, 5 fixtures cover the core paths.
    Full OWASP LLM Top 10 prompt-injection sweep deferred to CARRY-028.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4

import pytest

from adapters._testing.mock_clients import MockChatClient
from agent_harness._contracts import (
    ChatResponse,
    ExecutionContext,
    MemoryHint,
    Message,
    ToolCall,
    TraceContext,
)
from agent_harness._contracts.chat import StopReason
from agent_harness.memory._abc import MemoryLayer, MemoryScope
from agent_harness.memory.extraction import MemoryExtractor
from agent_harness.memory.layers.session_layer import SessionLayer
from agent_harness.memory.retrieval import MemoryRetrieval
from agent_harness.tools.memory_tools import (
    make_memory_search_handler,
    make_memory_write_handler,
)


class _TenantStubLayer(MemoryLayer):
    """Test-only layer that enforces tenant_id filter at read/write."""

    def __init__(self, scope: MemoryScope) -> None:
        self.scope = scope
        self._store: list[MemoryHint] = []
        self.write_calls: list[dict[str, object]] = []

    async def read(
        self,
        *,
        query: str,
        tenant_id: UUID | None = None,
        user_id: UUID | None = None,
        time_scales: tuple[Literal["short_term", "long_term", "semantic"], ...] = ("long_term",),
        max_hints: int = 10,
        trace_context: TraceContext | None = None,
    ) -> list[MemoryHint]:
        if tenant_id is None:
            return []
        return [
            h
            for h in self._store
            if h.tenant_id == tenant_id and query.lower() in h.summary.lower()
        ][:max_hints]

    async def write(
        self,
        *,
        content: str,
        tenant_id: UUID | None = None,
        user_id: UUID | None = None,
        time_scale: Literal["short_term", "long_term", "semantic"] = "long_term",
        confidence: float = 0.5,
        trace_context: TraceContext | None = None,
    ) -> UUID:
        if tenant_id is None:
            raise ValueError("tenant_id required")
        new_id = uuid4()
        self.write_calls.append(
            {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "content": content,
                "time_scale": time_scale,
            }
        )
        self._store.append(
            MemoryHint(
                hint_id=new_id,
                layer="user",
                time_scale=time_scale,
                summary=content,
                confidence=confidence,
                relevance_score=1.0,
                full_content_pointer="t",
                timestamp=datetime.now(timezone.utc),
                tenant_id=tenant_id,
            )
        )
        return new_id

    async def evict(self, **kwargs: object) -> None:
        return None

    async def resolve(self, hint: MemoryHint, **kwargs: object) -> str:
        return ""


@pytest.mark.asyncio
@pytest.mark.multi_tenant
async def test_tenant_a_search_zero_leak_from_tenant_b() -> None:
    """memory_search by tenant_a returns 0 hints belonging to tenant_b."""
    layer = _TenantStubLayer(MemoryScope.USER)
    tenant_a = uuid4()
    tenant_b = uuid4()
    user_a = uuid4()
    user_b = uuid4()

    await layer.write(content="tenant B secret topic", tenant_id=tenant_b, user_id=user_b)

    retrieval = MemoryRetrieval({"user": layer})
    handler = make_memory_search_handler(retrieval)
    exec_ctx = ExecutionContext(tenant_id=tenant_a, user_id=user_a)
    call = ToolCall(
        id="t1",
        name="memory_search",
        arguments={
            "query": "secret",
            "scopes": ["user"],
        },
    )
    resp = json.loads(await handler(call, exec_ctx))
    assert resp["ok"] is True
    assert resp["hints"] == []


@pytest.mark.asyncio
@pytest.mark.multi_tenant
async def test_tenant_a_write_isolated_storage() -> None:
    layer = _TenantStubLayer(MemoryScope.USER)
    tenant_a = uuid4()
    tenant_b = uuid4()
    user_a = uuid4()
    user_b = uuid4()

    handler = make_memory_write_handler({"user": layer})
    exec_ctx = ExecutionContext(tenant_id=tenant_a, user_id=user_a)
    write_call = ToolCall(
        id="t2",
        name="memory_write",
        arguments={
            "scope": "user",
            "key": "k",
            "content": "tenant A data",
        },
    )
    resp = json.loads(await handler(write_call, exec_ctx))
    assert resp["ok"] is True

    assert layer.write_calls[0]["tenant_id"] == tenant_a

    hints_b = await layer.read(query="tenant", tenant_id=tenant_b, user_id=user_b)
    assert hints_b == []


@pytest.mark.asyncio
@pytest.mark.multi_tenant
async def test_session_layer_tenant_isolation_via_composite_key() -> None:
    layer = SessionLayer()
    tenant_a = uuid4()
    tenant_b = uuid4()
    session_a = uuid4()
    session_b = uuid4()

    await layer.write(content="shared topic", tenant_id=tenant_a, user_id=session_a)
    await layer.write(content="shared topic", tenant_id=tenant_b, user_id=session_b)

    a_hints = await layer.read(query="shared", tenant_id=tenant_a, user_id=session_a)
    assert len(a_hints) == 1
    assert a_hints[0].tenant_id == tenant_a

    cross = await layer.read(query="shared", tenant_id=tenant_a, user_id=session_b)
    assert cross == []


@pytest.mark.asyncio
@pytest.mark.multi_tenant
async def test_user_layer_query_filtered_by_tenant_id_at_search() -> None:
    layer = _TenantStubLayer(MemoryScope.USER)
    tenant_a = uuid4()
    tenant_b = uuid4()
    user_a = uuid4()
    user_b = uuid4()

    await layer.write(content="banana", tenant_id=tenant_a, user_id=user_a)
    await layer.write(content="banana", tenant_id=tenant_b, user_id=user_b)

    retrieval = MemoryRetrieval({"user": layer})
    a_hints = await retrieval.search(
        query="banana", tenant_id=tenant_a, user_id=user_a, scopes=("user",)
    )
    b_hints = await retrieval.search(
        query="banana", tenant_id=tenant_b, user_id=user_b, scopes=("user",)
    )
    assert len(a_hints) == 1
    assert a_hints[0].tenant_id == tenant_a
    assert len(b_hints) == 1
    assert b_hints[0].tenant_id == tenant_b


@pytest.mark.asyncio
@pytest.mark.multi_tenant
async def test_extraction_worker_no_cross_tenant_pollution() -> None:
    chat_client = MockChatClient(
        responses=[
            ChatResponse(
                model="mock",
                content='[{"content": "user prefers JSON output", "confidence": 0.8}]',
                stop_reason=StopReason.END_TURN,
            )
        ]
    )
    user_layer = _TenantStubLayer(MemoryScope.USER)
    extractor = MemoryExtractor(chat_client=chat_client, user_layer=user_layer)  # type: ignore[arg-type]  # noqa: E501

    tenant_a = uuid4()
    user_a = uuid4()
    session_a = uuid4()
    new_ids = await extractor.extract_session_to_user(
        session_id=session_a,
        tenant_id=tenant_a,
        user_id=user_a,
        messages=[Message(role="user", content="give me JSON")],
    )

    assert len(new_ids) == 1
    assert user_layer.write_calls[0]["tenant_id"] == tenant_a
    assert user_layer.write_calls[0]["user_id"] == user_a


@pytest.mark.asyncio
@pytest.mark.multi_tenant
async def test_profile_pull_isolated_by_tenant() -> None:
    """Sprint 57.148: profile() (always-on, empty query) still enforces the tenant filter.

    The wildcard empty query must NOT bypass isolation — tenant B's profile pull
    returns 0 rows belonging to tenant A despite the query matching everything.
    """
    layer = _TenantStubLayer(MemoryScope.USER)
    tenant_a = uuid4()
    tenant_b = uuid4()
    user_a = uuid4()
    user_b = uuid4()

    await layer.write(content="name is Chris", tenant_id=tenant_a, user_id=user_a)

    retrieval = MemoryRetrieval({"user": layer})
    a_hints = await retrieval.profile(tenant_id=tenant_a, user_id=user_a)
    b_hints = await retrieval.profile(tenant_id=tenant_b, user_id=user_b)

    assert [h.summary for h in a_hints] == ["name is Chris"]  # owner sees it
    assert b_hints == []  # other tenant → 0 leak despite the wildcard query
