"""
File: backend/tests/unit/api/v1/chat/test_memory_auto_extract.py
Purpose: Unit tests for the Sprint 57.149 post-completion Option-B auto-extract
    hook (_maybe_auto_extract) — gate + dedup-facts threading + best-effort swallow.
Category: Tests / 範疇 3 + chat wiring
Scope: Sprint 57.149 (AD-Memory-Formation-Auto-Extract)

Created: 2026-06-28
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest

from agent_harness._contracts import Message, TraceContext
from api.v1.chat.handler import ChatMemoryExtractContext
from api.v1.chat.router import _maybe_auto_extract


class _StubExtractor:
    def __init__(self, *, raises: bool = False) -> None:
        self.calls: list[dict[str, Any]] = []
        self._raises = raises

    async def extract_session_to_user(self, **kwargs: Any) -> list[Any]:
        self.calls.append(kwargs)
        if self._raises:
            raise RuntimeError("extractor boom")
        return []


class _StubRetrieval:
    def __init__(self, summaries: tuple[str, ...] = ()) -> None:
        self._hints = [SimpleNamespace(summary=s) for s in summaries]
        self.profile_calls: list[tuple[Any, Any]] = []

    async def profile(self, *, tenant_id: Any, user_id: Any, top_k: int = 5) -> list[Any]:
        self.profile_calls.append((tenant_id, user_id))
        return self._hints


class _StubMessageStore:
    def __init__(self, messages: tuple[Message, ...] = ()) -> None:
        self._messages = list(messages)

    async def load(self) -> list[Message]:
        return list(self._messages)


def _ctx(extractor: Any, retrieval: Any, store: Any) -> ChatMemoryExtractContext:
    return ChatMemoryExtractContext(
        extractor=extractor,
        retrieval=retrieval,
        message_store=store,
    )


def _trace(user_id: Any) -> TraceContext:
    return TraceContext(tenant_id=uuid4(), session_id=uuid4(), user_id=user_id)


@pytest.mark.asyncio
async def test_no_op_when_ctx_none() -> None:
    """No extract context wired (echo / flag-off / missing env) → nothing happens."""
    await _maybe_auto_extract(
        memory_extract_ctx=None,
        tenant_id=uuid4(),
        session_id=uuid4(),
        trace_context=_trace(uuid4()),
    )


@pytest.mark.asyncio
async def test_no_op_when_no_user() -> None:
    """Anonymous / legacy caller (user_id None) → extractor never called."""
    extractor = _StubExtractor()
    store = _StubMessageStore((Message(role="user", content="x"),))
    await _maybe_auto_extract(
        memory_extract_ctx=_ctx(extractor, _StubRetrieval(), store),
        tenant_id=uuid4(),
        session_id=uuid4(),
        trace_context=_trace(None),
    )
    assert extractor.calls == []


@pytest.mark.asyncio
async def test_no_op_when_empty_ledger() -> None:
    """No messages in the session ledger → extractor never called."""
    extractor = _StubExtractor()
    await _maybe_auto_extract(
        memory_extract_ctx=_ctx(extractor, _StubRetrieval(), _StubMessageStore(())),
        tenant_id=uuid4(),
        session_id=uuid4(),
        trace_context=_trace(uuid4()),
    )
    assert extractor.calls == []


@pytest.mark.asyncio
async def test_runs_extract_with_ledger_and_known_facts() -> None:
    """Happy path: loads the ledger, reads profile() facts for dedup, runs extract."""
    user, tenant, session = uuid4(), uuid4(), uuid4()
    msgs = (Message(role="user", content="I am Chris"),)
    extractor = _StubExtractor()
    retrieval = _StubRetrieval(summaries=("User name is Chris.",))
    await _maybe_auto_extract(
        memory_extract_ctx=_ctx(extractor, retrieval, _StubMessageStore(msgs)),
        tenant_id=tenant,
        session_id=session,
        trace_context=TraceContext(tenant_id=tenant, session_id=session, user_id=user),
    )
    assert len(extractor.calls) == 1
    call = extractor.calls[0]
    assert call["tenant_id"] == tenant
    assert call["user_id"] == user
    assert call["messages"] == list(msgs)
    assert call["known_facts"] == ["User name is Chris."]
    assert retrieval.profile_calls == [(tenant, user)]


@pytest.mark.asyncio
async def test_swallows_extractor_failure() -> None:
    """An extractor exception is logged + swallowed — it must NEVER propagate
    (memory formation is best-effort; it cannot break the SSE stream)."""
    extractor = _StubExtractor(raises=True)
    store = _StubMessageStore((Message(role="user", content="x"),))
    await _maybe_auto_extract(
        memory_extract_ctx=_ctx(extractor, _StubRetrieval(), store),
        tenant_id=uuid4(),
        session_id=uuid4(),
        trace_context=_trace(uuid4()),
    )
    assert len(extractor.calls) == 1  # attempted, then swallowed (no raise)
