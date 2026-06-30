"""
File: backend/tests/unit/agent_harness/memory/test_formation.py
Purpose: Unit tests for MemoryFormationWorker — the combined (1-call) extract +
    summarize worker (Sprint 57.152). Covers the combined path (one chat() →
    write_facts + store_summary), the separate fallback (combined=False → 2 delegate
    calls), section conditioning, no-op guards, prompt construction, and parse.
Category: Tests / 範疇 3
Scope: Phase 57 / Sprint 57.152

Created: 2026-06-30
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest

from adapters._testing.mock_clients import MockChatClient
from agent_harness._contracts import ChatResponse, Message
from agent_harness._contracts.chat import StopReason
from agent_harness.memory.formation import MemoryFormationWorker

_COMBINED_JSON = (
    '{"facts": [{"content": "User is Chris", "confidence": 0.9}], '
    '"summary": "Discussed the billing migration.", '
    '"key_decisions": ["dual-write"], '
    '"unresolved_issues": ["invoice schema"]}'
)


class _ExtractorStub:
    def __init__(self) -> None:
        self.write_facts_calls: list[dict[str, Any]] = []
        self.extract_calls: list[dict[str, Any]] = []

    async def write_facts(
        self,
        items: list[dict[str, Any]],
        *,
        tenant_id: Any,
        user_id: Any,
        trace_context: Any = None,
    ) -> list[Any]:
        self.write_facts_calls.append({"items": items, "tenant_id": tenant_id, "user_id": user_id})
        return []

    async def extract_session_to_user(self, **kwargs: Any) -> list[Any]:
        self.extract_calls.append(kwargs)
        return []


class _SummarizerStub:
    def __init__(self) -> None:
        self.store_calls: list[dict[str, Any]] = []
        self.summarize_calls: list[dict[str, Any]] = []

    async def store_summary(self, parsed: dict[str, Any], *, session_id: Any) -> None:
        self.store_calls.append({"parsed": parsed, "session_id": session_id})

    async def summarize_and_store(self, **kwargs: Any) -> None:
        self.summarize_calls.append(kwargs)


def _chat(content: str) -> MockChatClient:
    return MockChatClient(
        responses=[ChatResponse(model="mock", content=content, stop_reason=StopReason.END_TURN)]
    )


def _msgs() -> list[Message]:
    return [Message(role="user", content="I am Chris; let's discuss billing migration")]


@pytest.mark.asyncio
async def test_combined_one_call_writes_both() -> None:
    """The core win: ONE chat() call forms BOTH a user fact AND a session summary."""
    chat = _chat(_COMBINED_JSON)
    ext, summ = _ExtractorStub(), _SummarizerStub()
    worker = MemoryFormationWorker(chat, extractor=ext, summarizer=summ)  # type: ignore[arg-type]
    sid, tid, uid = uuid4(), uuid4(), uuid4()

    await worker.form(messages=_msgs(), session_id=sid, tenant_id=tid, user_id=uid)

    assert chat.chat_call_count == 1  # ONE combined call, not two
    assert len(ext.write_facts_calls) == 1
    assert ext.write_facts_calls[0]["items"] == [{"content": "User is Chris", "confidence": 0.9}]
    assert ext.write_facts_calls[0]["user_id"] == uid
    assert len(summ.store_calls) == 1
    assert summ.store_calls[0]["session_id"] == sid
    assert summ.store_calls[0]["parsed"]["summary"] == "Discussed the billing migration."
    assert summ.store_calls[0]["parsed"]["key_decisions"] == ["dual-write"]
    # the single-call delegates were NOT used (combined path)
    assert ext.extract_calls == [] and summ.summarize_calls == []


@pytest.mark.asyncio
async def test_combined_false_uses_separate_two_calls() -> None:
    """combined=False → delegate to each worker's full single-call method (fallback)."""
    chat = _chat(_COMBINED_JSON)
    ext, summ = _ExtractorStub(), _SummarizerStub()
    worker = MemoryFormationWorker(  # type: ignore[arg-type]
        chat, extractor=ext, summarizer=summ, combined=False
    )
    sid, tid, uid = uuid4(), uuid4(), uuid4()

    await worker.form(
        messages=_msgs(), session_id=sid, tenant_id=tid, user_id=uid, known_facts=["x"]
    )

    # the worker itself never calls chat in separate mode (the collaborators would)
    assert chat.chat_call_count == 0
    assert len(ext.extract_calls) == 1
    assert ext.extract_calls[0]["known_facts"] == ["x"]
    assert ext.extract_calls[0]["user_id"] == uid
    assert len(summ.summarize_calls) == 1
    assert summ.summarize_calls[0]["session_id"] == sid
    # combined dispatch halves NOT used
    assert ext.write_facts_calls == [] and summ.store_calls == []


@pytest.mark.asyncio
async def test_only_extractor_one_call_facts_only() -> None:
    """No summarizer → ONE call forms only facts."""
    chat = _chat('{"facts": [{"content": "User is Chris", "confidence": 0.8}]}')
    ext = _ExtractorStub()
    worker = MemoryFormationWorker(chat, extractor=ext, summarizer=None)  # type: ignore[arg-type]

    await worker.form(messages=_msgs(), session_id=uuid4(), tenant_id=uuid4(), user_id=uuid4())

    assert chat.chat_call_count == 1
    assert len(ext.write_facts_calls) == 1


@pytest.mark.asyncio
async def test_only_summarizer_one_call_summary_only() -> None:
    """No extractor → ONE call forms only the summary."""
    chat = _chat('{"summary": "Talked pricing.", "key_decisions": [], "unresolved_issues": []}')
    summ = _SummarizerStub()
    worker = MemoryFormationWorker(chat, extractor=None, summarizer=summ)  # type: ignore[arg-type]

    await worker.form(messages=_msgs(), session_id=uuid4(), tenant_id=uuid4(), user_id=uuid4())

    assert chat.chat_call_count == 1
    assert len(summ.store_calls) == 1
    assert summ.store_calls[0]["parsed"]["summary"] == "Talked pricing."


@pytest.mark.asyncio
async def test_no_user_skips_facts_still_forms_summary() -> None:
    """user_id=None → want_facts False (no write_facts) but the summary still forms."""
    chat = _chat(_COMBINED_JSON)
    ext, summ = _ExtractorStub(), _SummarizerStub()
    worker = MemoryFormationWorker(chat, extractor=ext, summarizer=summ)  # type: ignore[arg-type]

    await worker.form(messages=_msgs(), session_id=uuid4(), tenant_id=uuid4(), user_id=None)

    assert chat.chat_call_count == 1
    assert ext.write_facts_calls == []  # no user → facts skipped
    assert len(summ.store_calls) == 1  # summary still formed


@pytest.mark.asyncio
async def test_empty_ledger_no_op() -> None:
    """No messages → no chat call, no writes."""
    chat = MockChatClient()
    ext, summ = _ExtractorStub(), _SummarizerStub()
    worker = MemoryFormationWorker(chat, extractor=ext, summarizer=summ)  # type: ignore[arg-type]

    await worker.form(messages=[], session_id=uuid4(), tenant_id=uuid4(), user_id=uuid4())

    assert chat.chat_call_count == 0
    assert ext.write_facts_calls == [] and summ.store_calls == []


@pytest.mark.asyncio
async def test_no_collaborators_no_op() -> None:
    """Neither extractor nor summarizer wired → no chat call."""
    chat = MockChatClient()
    worker = MemoryFormationWorker(chat, extractor=None, summarizer=None)

    await worker.form(messages=_msgs(), session_id=uuid4(), tenant_id=uuid4(), user_id=uuid4())

    assert chat.chat_call_count == 0


@pytest.mark.asyncio
async def test_only_user_no_user_no_collaborator_summary_only_noop() -> None:
    """extractor-only worker + anon user → want_facts False, want_summary False → no call."""
    chat = MockChatClient()
    ext = _ExtractorStub()
    worker = MemoryFormationWorker(chat, extractor=ext, summarizer=None)  # type: ignore[arg-type]

    await worker.form(messages=_msgs(), session_id=uuid4(), tenant_id=uuid4(), user_id=None)

    assert chat.chat_call_count == 0
    assert ext.write_facts_calls == []


def test_build_prompt_sections_and_known_block() -> None:
    """The combined prompt includes only the enabled section field-specs + the
    known-facts dedup block (facts section only)."""
    worker = MemoryFormationWorker(  # type: ignore[arg-type]
        MockChatClient(), extractor=_ExtractorStub(), summarizer=_SummarizerStub()
    )

    both = worker._build_prompt(  # noqa: SLF001 — testing the private prompt builder
        messages=_msgs(), want_facts=True, want_summary=True, known_facts=["User is Chris."]
    )
    assert '"facts"' in both and '"summary"' in both and '"key_decisions"' in both
    assert "ALREADY REMEMBERED" in both and "User is Chris." in both

    summary_only = worker._build_prompt(  # noqa: SLF001
        messages=_msgs(), want_facts=False, want_summary=True, known_facts=["ignored"]
    )
    assert '"facts"' not in summary_only and '"summary"' in summary_only
    assert "ALREADY REMEMBERED" not in summary_only  # no facts section → no dedup block


def test_parse_combined_shapes() -> None:
    """The combined parser extracts dict-only facts + a non-blank summary, coerces
    decision lists, and tolerates prose around the JSON object."""
    worker = MemoryFormationWorker(MockChatClient())

    facts, summary = worker._parse_combined(  # noqa: SLF001
        'prefix {"facts": [{"content": "a"}, 42, "x"], "summary": "S", '
        '"key_decisions": ["k", 1, "  t  "], "unresolved_issues": "nope"} suffix',
        want_facts=True,
        want_summary=True,
    )
    assert facts == [{"content": "a"}]  # non-dict items dropped
    assert summary is not None
    assert summary["summary"] == "S"
    assert summary["key_decisions"] == ["k", "t"]  # coerced + trimmed
    assert summary["unresolved_issues"] == []  # non-list → []

    # blank summary → None; want_facts False → facts ignored
    facts2, summary2 = worker._parse_combined(  # noqa: SLF001
        '{"facts": [{"content": "a"}], "summary": "   "}', want_facts=False, want_summary=True
    )
    assert facts2 == [] and summary2 is None

    # no JSON object at all → ([], None)
    assert worker._parse_combined("not json", want_facts=True, want_summary=True) == (
        [],
        None,
    )  # noqa: SLF001
