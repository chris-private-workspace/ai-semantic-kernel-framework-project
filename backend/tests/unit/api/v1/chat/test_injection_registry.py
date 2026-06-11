"""
File: backend/tests/unit/api/v1/chat/test_injection_registry.py
Purpose: Unit tests for the tenant-scoped InjectionRegistry + QueueMessageInbox (B1).
Category: tests
Scope: Phase 57 / Sprint 57.101 (B1 — between-turns message injection primitive)

Modification History (newest-first):
    - 2026-06-11: Initial creation (Sprint 57.101) — register/put/drain/unregister + isolation
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from agent_harness._contracts import Message
from api.v1.chat.injection_registry import InjectionRegistry, QueueMessageInbox


def _msg(text: str) -> Message:
    return Message(role="user", content=text)


@pytest.mark.asyncio
async def test_register_then_put_then_drain_returns_message() -> None:
    reg = InjectionRegistry()
    tid, sid = uuid4(), uuid4()
    await reg.register(tid, sid)
    assert (await reg.put(tid, sid, _msg("hi"))) is True
    drained = await reg.drain(tid, sid)
    assert [m.content for m in drained] == ["hi"]


@pytest.mark.asyncio
async def test_put_on_unregistered_session_returns_false() -> None:
    reg = InjectionRegistry()
    assert (await reg.put(uuid4(), uuid4(), _msg("x"))) is False


@pytest.mark.asyncio
async def test_drain_on_unregistered_session_returns_empty() -> None:
    reg = InjectionRegistry()
    assert (await reg.drain(uuid4(), uuid4())) == []


@pytest.mark.asyncio
async def test_drain_is_fifo_and_drains_all_then_empties() -> None:
    reg = InjectionRegistry()
    tid, sid = uuid4(), uuid4()
    await reg.register(tid, sid)
    await reg.put(tid, sid, _msg("a"))
    await reg.put(tid, sid, _msg("b"))
    assert [m.content for m in await reg.drain(tid, sid)] == ["a", "b"]
    # second drain is empty (the queue was emptied)
    assert (await reg.drain(tid, sid)) == []


@pytest.mark.asyncio
async def test_unregister_drops_queue_so_later_put_fails() -> None:
    reg = InjectionRegistry()
    tid, sid = uuid4(), uuid4()
    await reg.register(tid, sid)
    await reg.unregister(tid, sid)
    assert (await reg.put(tid, sid, _msg("late"))) is False
    assert (await reg.drain(tid, sid)) == []
    # idempotent on missing
    await reg.unregister(tid, sid)


@pytest.mark.asyncio
async def test_put_cannot_reach_another_tenants_session() -> None:
    """tenant_a registers; tenant_b put with the same session_id → no live queue → False."""
    reg = InjectionRegistry()
    tenant_a, tenant_b, sid = uuid4(), uuid4(), uuid4()
    await reg.register(tenant_a, sid)
    assert (await reg.put(tenant_b, sid, _msg("hijack"))) is False
    # tenant_a's queue is untouched (no leaked message)
    assert (await reg.drain(tenant_a, sid)) == []


@pytest.mark.asyncio
async def test_two_tenants_same_session_id_are_independent() -> None:
    reg = InjectionRegistry()
    tenant_a, tenant_b, sid = uuid4(), uuid4(), uuid4()  # SAME id under both tenants
    await reg.register(tenant_a, sid)
    await reg.register(tenant_b, sid)
    await reg.put(tenant_a, sid, _msg("for-a"))
    assert [m.content for m in await reg.drain(tenant_a, sid)] == ["for-a"]
    assert (await reg.drain(tenant_b, sid)) == []  # b's queue stays empty


@pytest.mark.asyncio
async def test_unregister_prunes_empty_tenant_bucket() -> None:
    reg = InjectionRegistry()
    tid, sid = uuid4(), uuid4()
    await reg.register(tid, sid)
    await reg.unregister(tid, sid)
    assert tid not in reg._tenants  # noqa: SLF001


@pytest.mark.asyncio
async def test_queue_message_inbox_drains_its_session() -> None:
    """QueueMessageInbox (the loop's MessageInbox view) delegates to registry.drain."""
    reg = InjectionRegistry()
    tid, sid = uuid4(), uuid4()
    await reg.register(tid, sid)
    inbox = QueueMessageInbox(reg, tid, sid)
    assert (await inbox.drain()) == []  # empty initially
    await reg.put(tid, sid, _msg("coach"))
    drained = await inbox.drain()
    assert [m.content for m in drained] == ["coach"]
    assert (await inbox.drain()) == []  # emptied
