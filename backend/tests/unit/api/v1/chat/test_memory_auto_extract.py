"""
File: backend/tests/unit/api/v1/chat/test_memory_auto_extract.py
Purpose: Unit tests for the post-completion memory-formation hook
    (_maybe_auto_extract) — gate + profile() dedup-facts threading + best-effort
    swallow. Sprint 57.152 reshaped the ctx to carry a MemoryFormationWorker
    (`former`) that the hook calls ONCE; the profile() known-facts read is gated
    on former.wants_user_facts.
Category: Tests / 範疇 3 + chat wiring
Scope: Sprint 57.149 (created) / Sprint 57.152 (former shape)

Created: 2026-06-28
Last Modified: 2026-06-30
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest

from agent_harness._contracts import Message, TraceContext
from api.v1.chat.handler import ChatMemoryExtractContext
from api.v1.chat.router import _maybe_auto_extract


class _StubFormer:
    """Records form() calls; mimics MemoryFormationWorker's wants_user_facts gate."""

    def __init__(self, *, wants_user_facts: bool = True, raises: bool = False) -> None:
        self.calls: list[dict[str, Any]] = []
        self._wants = wants_user_facts
        self._raises = raises

    @property
    def wants_user_facts(self) -> bool:
        return self._wants

    async def form(self, **kwargs: Any) -> None:
        self.calls.append(kwargs)
        if self._raises:
            raise RuntimeError("former boom")


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


def _ctx(former: Any, retrieval: Any, store: Any) -> ChatMemoryExtractContext:
    return ChatMemoryExtractContext(
        former=former,
        retrieval=retrieval,
        message_store=store,
    )


def _trace(user_id: Any) -> TraceContext:
    return TraceContext(tenant_id=uuid4(), session_id=uuid4(), user_id=user_id)


@pytest.mark.asyncio
async def test_no_op_when_ctx_none() -> None:
    """No formation context wired (echo / flag-off / missing env) → nothing happens."""
    await _maybe_auto_extract(
        memory_extract_ctx=None,
        tenant_id=uuid4(),
        session_id=uuid4(),
        trace_context=_trace(uuid4()),
    )


@pytest.mark.asyncio
async def test_no_op_when_empty_ledger() -> None:
    """No messages in the session ledger → former.form never called."""
    former = _StubFormer()
    await _maybe_auto_extract(
        memory_extract_ctx=_ctx(former, _StubRetrieval(), _StubMessageStore(())),
        tenant_id=uuid4(),
        session_id=uuid4(),
        trace_context=_trace(uuid4()),
    )
    assert former.calls == []


@pytest.mark.asyncio
async def test_anon_user_skips_profile_but_still_forms() -> None:
    """Anonymous trace (user_id None) → profile() NOT read, but former.form IS
    called (with user_id=None) so the summary section can still form."""
    former = _StubFormer()
    retrieval = _StubRetrieval(summaries=("User name is Chris.",))
    store = _StubMessageStore((Message(role="user", content="x"),))
    await _maybe_auto_extract(
        memory_extract_ctx=_ctx(former, retrieval, store),
        tenant_id=uuid4(),
        session_id=uuid4(),
        trace_context=_trace(None),
    )
    assert retrieval.profile_calls == []
    assert len(former.calls) == 1
    assert former.calls[0]["user_id"] is None
    assert former.calls[0]["known_facts"] is None


@pytest.mark.asyncio
async def test_no_profile_read_when_former_wants_no_facts() -> None:
    """Summary-only worker (wants_user_facts False) → profile() NOT read even with
    a known user; former.form is still called (summary section)."""
    former = _StubFormer(wants_user_facts=False)
    retrieval = _StubRetrieval(summaries=("User name is Chris.",))
    store = _StubMessageStore((Message(role="user", content="x"),))
    await _maybe_auto_extract(
        memory_extract_ctx=_ctx(former, retrieval, store),
        tenant_id=uuid4(),
        session_id=uuid4(),
        trace_context=_trace(uuid4()),
    )
    assert retrieval.profile_calls == []
    assert len(former.calls) == 1
    assert former.calls[0]["known_facts"] is None


@pytest.mark.asyncio
async def test_runs_form_with_ledger_and_known_facts() -> None:
    """Happy path: loads the ledger, reads profile() facts for dedup (wants_user_
    facts + known user), runs ONE former.form() with the ledger + known_facts."""
    user, tenant, session = uuid4(), uuid4(), uuid4()
    msgs = (Message(role="user", content="I am Chris"),)
    former = _StubFormer()
    retrieval = _StubRetrieval(summaries=("User name is Chris.",))
    await _maybe_auto_extract(
        memory_extract_ctx=_ctx(former, retrieval, _StubMessageStore(msgs)),
        tenant_id=tenant,
        session_id=session,
        trace_context=TraceContext(tenant_id=tenant, session_id=session, user_id=user),
    )
    assert len(former.calls) == 1
    call = former.calls[0]
    assert call["tenant_id"] == tenant
    assert call["session_id"] == session
    assert call["user_id"] == user
    assert call["messages"] == list(msgs)
    assert call["known_facts"] == ["User name is Chris."]
    assert retrieval.profile_calls == [(tenant, user)]


@pytest.mark.asyncio
async def test_swallows_former_failure() -> None:
    """A former exception is logged + swallowed — it must NEVER propagate
    (memory formation is best-effort; it cannot break the SSE stream)."""
    former = _StubFormer(raises=True)
    store = _StubMessageStore((Message(role="user", content="x"),))
    await _maybe_auto_extract(
        memory_extract_ctx=_ctx(former, _StubRetrieval(), store),
        tenant_id=uuid4(),
        session_id=uuid4(),
        trace_context=_trace(uuid4()),
    )
    assert len(former.calls) == 1  # attempted, then swallowed (no raise)
