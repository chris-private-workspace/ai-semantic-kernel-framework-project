"""
File: backend/tests/unit/agent_harness/subagent/test_teammate_inbox.py
Purpose: Unit tests — the teammate child loop drains its MessageInbox at a turn boundary
    (B1 seam) + the lifecycle-scoped inbox (make_teammate_inbox_scope, Sprint 57.103 B2b)
    registers the child's queue on enter + unregisters on exit.
Category: Tests / 範疇 11 (Subagent Orchestration)
Scope: Sprint 57.102 (B2a) → Sprint 57.103 (B2b)

Description:
    B2a wired the teammate child loop with a MessageInbox (reusing B1's QueueMessageInbox
    over the InjectionRegistry keyed by subagent_id). B2b makes the inbox lifecycle-scoped:
    the TeammateExecutor brackets the child drive in a TeammateInboxScope (an async CM)
    that registers the child's queue on enter (so a concurrent chat-user inject POST
    reaches a LIVE teammate) and unregisters it on exit (so a put onto a finished teammate
    returns False → 409). These tests prove (a) the executor opens the scope keyed by the
    child's subagent_id, (b) the child drains a message present in its inbox (B1 seam), and
    (c) make_teammate_inbox_scope registers on enter + unregisters on exit / exception.

Created: 2026-06-11 (Sprint 57.102 B2a)

Modification History:
    - 2026-06-11: Sprint 57.103 (B2b) — inbox_factory → inbox_scope; + scope lifecycle tests
    - 2026-06-11: Initial creation (Sprint 57.102 B2a)
"""

from __future__ import annotations

import contextlib
from collections.abc import AsyncIterator
from uuid import UUID, uuid4

import pytest

from adapters._testing.mock_clients import MockChatClient
from agent_harness._contracts import (
    ChatResponse,
    LoopEvent,
    Message,
    MessageInbox,
    MessageInjected,
    StopReason,
    SubagentBudget,
    SubagentChildEvent,
    TokenUsage,
)
from agent_harness.subagent import MailboxStore, TeammateExecutor
from api.v1.chat.injection_registry import InjectionRegistry, make_teammate_inbox_scope

from ._child_loop_helpers import make_teammate_child_loop_factory


def _mock_response(text: str) -> ChatResponse:
    return ChatResponse(
        model="mock-gpt",
        content=text,
        stop_reason=StopReason.END_TURN,
        usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
    )


class _ScriptedInbox(MessageInbox):
    """A MessageInbox pre-filled with messages; records how many times it was drained."""

    def __init__(self, messages: list[Message]) -> None:
        self.remaining = list(messages)
        self.drain_calls = 0

    async def drain(self) -> list[Message]:
        self.drain_calls += 1
        out, self.remaining = self.remaining, []
        return out


@pytest.mark.asyncio
async def test_executor_opens_inbox_scope_with_subagent_id() -> None:
    """The TeammateExecutor opens the inbox scope keyed by the child's subagent_id."""
    captured: list[UUID] = []

    @contextlib.asynccontextmanager
    async def scope(sid: UUID) -> AsyncIterator[MessageInbox | None]:
        captured.append(sid)  # the scope was ENTERED with the child's subagent_id
        yield _ScriptedInbox([])

    teammate = TeammateExecutor(
        teammate_child_loop_factory=make_teammate_child_loop_factory(
            MockChatClient(responses=[_mock_response("done")])
        ),
        mailbox=MailboxStore(),
        inbox_scope=scope,
    )
    sid = uuid4()
    result = await teammate.execute(
        subagent_id=sid,
        parent_session_id=uuid4(),
        role="teammate",
        task="go",
        budget=SubagentBudget(),
    )
    assert result.success is True
    assert captured == [sid]


@pytest.mark.asyncio
async def test_teammate_child_loop_drains_inbox_message() -> None:
    """A message present in the child's inbox is drained by the child loop (B1 seam)."""
    inbox = _ScriptedInbox([Message(role="user", content="also check the db pool")])

    @contextlib.asynccontextmanager
    async def scope(sid: UUID) -> AsyncIterator[MessageInbox | None]:
        yield inbox

    teammate = TeammateExecutor(
        teammate_child_loop_factory=make_teammate_child_loop_factory(
            MockChatClient(responses=[_mock_response("done")])
        ),
        mailbox=MailboxStore(),
        inbox_scope=scope,
    )
    result = await teammate.execute(
        subagent_id=uuid4(),
        parent_session_id=uuid4(),
        role="teammate",
        task="investigate",
        budget=SubagentBudget(),
    )
    assert result.success is True
    # The child loop drained the inbox at its turn boundary (the B1 seam consumed it).
    assert inbox.drain_calls >= 1
    assert inbox.remaining == []


@pytest.mark.asyncio
async def test_teammate_no_inbox_scope_runs_without_inbox() -> None:
    """Without an inbox_scope the teammate child runs fine (inbox=None → no drain)."""
    teammate = TeammateExecutor(
        teammate_child_loop_factory=make_teammate_child_loop_factory(
            MockChatClient(responses=[_mock_response("done")])
        ),
        mailbox=MailboxStore(),
    )
    result = await teammate.execute(
        subagent_id=uuid4(),
        parent_session_id=uuid4(),
        role="teammate",
        task="go",
        budget=SubagentBudget(),
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_inbox_scope_registers_on_enter_unregisters_on_exit() -> None:
    """make_teammate_inbox_scope registers the child's queue while open; a concurrent
    inject put reaches the inbox; the queue is unregistered on exit."""
    registry = InjectionRegistry()
    tenant = uuid4()
    sid = uuid4()
    scope = make_teammate_inbox_scope(registry, tenant)
    msg = Message(role="user", content="hi")

    # Before: no queue → a concurrent inject put 409s (returns False).
    assert await registry.put(tenant, sid, msg) is False

    async with scope(sid) as inbox:
        # During: the queue is registered → a concurrent inject put succeeds AND the
        # child's inbox (over the same queue) drains it.
        assert await registry.put(tenant, sid, msg) is True
        assert inbox is not None
        assert [m.content for m in await inbox.drain()] == ["hi"]

    # After: unregistered → a put 409s again (no Potemkin dead inbox).
    assert await registry.put(tenant, sid, msg) is False


@pytest.mark.asyncio
async def test_inbox_scope_unregisters_on_exception() -> None:
    """The scope unregisters the queue even when the bracketed body raises (finally)."""
    registry = InjectionRegistry()
    tenant = uuid4()
    sid = uuid4()
    scope = make_teammate_inbox_scope(registry, tenant)

    with pytest.raises(RuntimeError):
        async with scope(sid):
            assert await registry.put(tenant, sid, Message(role="user", content="x")) is True
            raise RuntimeError("boom")

    # The finally ran → the queue is gone → a put 409s.
    assert await registry.put(tenant, sid, Message(role="user", content="y")) is False


@pytest.mark.asyncio
async def test_child_message_injected_is_relayed_as_subagent_child_event() -> None:
    """A MessageInjected the child fires (draining its inbox) is relayed to the parent as a
    SubagentChildEvent so the Inspector Tree shows the injected turn (Sprint 57.103 US-3)."""
    inbox = _ScriptedInbox([Message(role="user", content="check the db pool")])
    relayed: list[LoopEvent] = []

    async def emitter(ev: LoopEvent) -> None:
        relayed.append(ev)

    @contextlib.asynccontextmanager
    async def scope(sid: UUID) -> AsyncIterator[MessageInbox | None]:
        yield inbox

    teammate = TeammateExecutor(
        teammate_child_loop_factory=make_teammate_child_loop_factory(
            MockChatClient(responses=[_mock_response("done")])
        ),
        mailbox=MailboxStore(),
        event_emitter=emitter,
        inbox_scope=scope,
    )
    result = await teammate.execute(
        subagent_id=uuid4(),
        parent_session_id=uuid4(),
        role="teammate",
        task="investigate",
        budget=SubagentBudget(),
    )
    assert result.success is True
    injected = [
        e
        for e in relayed
        if isinstance(e, SubagentChildEvent) and isinstance(e.inner, MessageInjected)
    ]
    assert len(injected) >= 1
    inner = injected[0].inner
    assert isinstance(inner, MessageInjected)
    assert inner.text == "check the db pool"
