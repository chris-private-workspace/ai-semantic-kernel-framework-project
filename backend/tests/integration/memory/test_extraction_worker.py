"""
File: backend/tests/integration/memory/test_extraction_worker.py
Purpose: Integration tests for MemoryExtractor (manual-trigger; via MockChatClient).
Category: Tests / Cat 3 / extraction integration
Scope: Phase 51 / Sprint 51.2 Day 5.3

Created: 2026-04-30
"""

from __future__ import annotations

from typing import Literal
from uuid import UUID, uuid4

import pytest

from adapters._testing.mock_clients import MockChatClient
from agent_harness._contracts import ChatResponse, Message, TraceContext
from agent_harness._contracts.chat import StopReason
from agent_harness.memory._abc import MemoryLayer, MemoryScope
from agent_harness.memory.extraction import MemoryExtractor


class _RecordingLayer(MemoryLayer):
    """User layer stub that records write() calls."""

    scope = MemoryScope.USER

    def __init__(self) -> None:
        self.writes: list[dict[str, object]] = []

    async def read(self, **kwargs: object) -> list:
        return []

    async def write(
        self,
        *,
        content: str,
        tenant_id: UUID | None = None,
        user_id: UUID | None = None,
        time_scale: Literal["short_term", "long_term", "semantic"] = "long_term",
        confidence: float = 0.5,
        source: str | None = None,
        trace_context: TraceContext | None = None,
    ) -> UUID:
        self.writes.append(
            {
                "content": content,
                "tenant_id": tenant_id,
                "user_id": user_id,
                "time_scale": time_scale,
                "confidence": confidence,
                "source": source,
            }
        )
        return uuid4()

    async def evict(self, **kwargs: object) -> None:
        return None

    async def resolve(self, **kwargs: object) -> str:
        return ""


@pytest.mark.asyncio
async def test_extract_5_message_session_creates_user_hints() -> None:
    """5-message session feeds into extractor; 2 facts written to user layer."""
    chat_client = MockChatClient(
        responses=[
            ChatResponse(
                model="mock",
                content=(
                    '[{"content": "user prefers tables over prose", "confidence": 0.9}, '
                    '{"content": "user is in finance", "confidence": 0.7}]'
                ),
                stop_reason=StopReason.END_TURN,
            )
        ]
    )
    layer = _RecordingLayer()
    extractor = MemoryExtractor(chat_client=chat_client, user_layer=layer)  # type: ignore[arg-type]

    tenant = uuid4()
    user = uuid4()
    session = uuid4()
    messages = [
        Message(role="user", content="give me a table of expenses"),
        Message(role="assistant", content="Here is the table..."),
        Message(role="user", content="that works for finance"),
        Message(role="assistant", content="Got it"),
        Message(role="user", content="thanks"),
    ]
    new_ids = await extractor.extract_session_to_user(
        session_id=session,
        tenant_id=tenant,
        user_id=user,
        messages=messages,
    )

    assert len(new_ids) == 2
    assert layer.writes[0]["content"] == "user prefers tables over prose"
    assert layer.writes[0]["confidence"] == 0.9
    assert layer.writes[1]["content"] == "user is in finance"
    assert layer.writes[1]["confidence"] == 0.7
    # All writes go to the same tenant + user
    for w in layer.writes:
        assert w["tenant_id"] == tenant
        assert w["user_id"] == user
        assert w["time_scale"] == "long_term"
        assert w["source"] == "auto_extract"  # Sprint 57.149 provenance tag


@pytest.mark.asyncio
async def test_extraction_uses_chat_client_abc_no_sdk_leak() -> None:
    """Smoke check: MockChatClient (ABC-conformant) is used; chat_call_count
    increments. Combined with grep gate at lint time, this verifies the LLM
    Provider Neutrality rule (no openai/anthropic import in agent_harness/memory)."""
    chat_client = MockChatClient(
        responses=[ChatResponse(model="mock", content="[]", stop_reason=StopReason.END_TURN)]
    )
    layer = _RecordingLayer()
    extractor = MemoryExtractor(chat_client=chat_client, user_layer=layer)  # type: ignore[arg-type]

    await extractor.extract_session_to_user(
        session_id=uuid4(),
        tenant_id=uuid4(),
        user_id=uuid4(),
        messages=[Message(role="user", content="hi")],
    )
    assert chat_client.chat_call_count == 1


@pytest.mark.asyncio
async def test_extraction_writes_under_correct_tenant_user() -> None:
    """Even when LLM returns shared/generic facts, the writes inherit the
    originating session's tenant + user identifiers."""
    chat_client = MockChatClient(
        responses=[
            ChatResponse(
                model="mock",
                content='[{"content": "shared fact", "confidence": 0.5}]',
                stop_reason=StopReason.END_TURN,
            )
        ]
    )
    layer = _RecordingLayer()
    extractor = MemoryExtractor(chat_client=chat_client, user_layer=layer)  # type: ignore[arg-type]

    tenant = uuid4()
    user = uuid4()
    session = uuid4()
    await extractor.extract_session_to_user(
        session_id=session,
        tenant_id=tenant,
        user_id=user,
        messages=[Message(role="user", content="x")],
    )

    assert layer.writes[0]["tenant_id"] == tenant
    assert layer.writes[0]["user_id"] == user


@pytest.mark.asyncio
async def test_known_facts_threaded_into_extraction_prompt() -> None:
    """Sprint 57.149: known_facts (from profile()) reach the extractor's LLM
    prompt as a do-not-repeat dedup block (best-effort prompt-level dedup)."""
    chat_client = MockChatClient(
        responses=[ChatResponse(model="mock", content="[]", stop_reason=StopReason.END_TURN)]
    )
    layer = _RecordingLayer()
    extractor = MemoryExtractor(chat_client=chat_client, user_layer=layer)  # type: ignore[arg-type]

    await extractor.extract_session_to_user(
        session_id=uuid4(),
        tenant_id=uuid4(),
        user_id=uuid4(),
        messages=[Message(role="user", content="hello again")],
        known_facts=["User name is Chris."],
    )
    assert chat_client.last_request is not None
    prompt = chat_client.last_request.messages[0].content
    assert isinstance(prompt, str)
    assert "User name is Chris." in prompt
    assert "ALREADY REMEMBERED" in prompt
