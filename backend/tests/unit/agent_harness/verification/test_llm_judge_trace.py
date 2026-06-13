"""
File: backend/tests/unit/agent_harness/verification/test_llm_judge_trace.py
Purpose: A3 — LLMJudgeVerifier trace-awareness ({trace} substitution + back-compat) + temperature.
Category: Tests / Unit / 範疇 10
Scope: Sprint 57.111 (A3)
Created: 2026-06-13

Related:
    - backend/src/agent_harness/verification/llm_judge.py
    - backend/src/agent_harness/verification/_trace.py
"""

from __future__ import annotations

import json
from datetime import datetime
from uuid import uuid4

import pytest

from adapters._testing.mock_clients import MockChatClient
from agent_harness._contracts.chat import ChatResponse, Message, StopReason
from agent_harness._contracts.state import (
    DurableState,
    LoopState,
    StateVersion,
    TransientState,
)
from agent_harness.verification import LLMJudgeVerifier


def _resp(passed: bool = True) -> ChatResponse:
    return ChatResponse(
        model="m",
        content=json.dumps({"passed": passed, "score": 0.9, "reason": "ok"}),
        stop_reason=StopReason.END_TURN,
    )


def _state(messages: list[Message]) -> LoopState:
    sid = uuid4()
    return LoopState(
        transient=TransientState(messages=messages),
        durable=DurableState(session_id=sid, tenant_id=sid),
        version=StateVersion(
            version=0, parent_version=None, created_at=datetime.now(), created_by_category="test"
        ),
    )


@pytest.mark.asyncio
async def test_judge_prompt_includes_trace_when_state_present() -> None:
    """A trace-dependent failure: the trace shows a tool error the final string hides."""
    chat = MockChatClient(responses=[_resp()])
    verifier = LLMJudgeVerifier(
        chat_client=chat, judge_template="Trace:\n{trace}\n---\nOutput: {output}"
    )
    state = _state([Message(role="tool", content="ERROR: db timeout")])
    await verifier.verify(output="All good, data saved.", state=state)

    sent = chat.last_request.messages[0].content
    assert isinstance(sent, str)
    assert "ERROR: db timeout" in sent  # the trace was substituted into the judge prompt
    assert "[tool]" in sent


@pytest.mark.asyncio
async def test_judge_prompt_empty_trace_when_state_none() -> None:
    """state=None (the Cat 9 fallback paths / back-compat) → {trace} resolves empty."""
    chat = MockChatClient(responses=[_resp()])
    verifier = LLMJudgeVerifier(chat_client=chat, judge_template="Trace:[{trace}] Output: {output}")
    await verifier.verify(output="x", state=None)

    sent = chat.last_request.messages[0].content
    assert sent == "Trace:[] Output: x"  # {trace} → empty string, no crash


@pytest.mark.asyncio
async def test_judge_backcompat_template_without_trace_placeholder() -> None:
    """A pre-A3 template with no {trace} placeholder works unchanged even WITH state."""
    chat = MockChatClient(responses=[_resp()])
    verifier = LLMJudgeVerifier(chat_client=chat, judge_template="Judge: {output}")
    state = _state([Message(role="user", content="hello")])
    result = await verifier.verify(output="x", state=state)

    assert result.passed is True
    assert chat.last_request.messages[0].content == "Judge: x"  # {trace} no-op


@pytest.mark.asyncio
async def test_judge_temperature_passed_to_request() -> None:
    """The benchmark constructs judges at temperature 0.0 for a stable accuracy number."""
    chat = MockChatClient(responses=[_resp()])
    verifier = LLMJudgeVerifier(chat_client=chat, judge_template="Judge: {output}", temperature=0.0)
    await verifier.verify(output="x", state=None)

    assert chat.last_request.temperature == 0.0


@pytest.mark.asyncio
async def test_judge_default_temperature_is_one() -> None:
    """Production verification keeps the pre-A3 default temperature (1.0)."""
    chat = MockChatClient(responses=[_resp()])
    verifier = LLMJudgeVerifier(chat_client=chat, judge_template="Judge: {output}")
    await verifier.verify(output="x", state=None)

    assert chat.last_request.temperature == 1.0
