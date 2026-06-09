"""
File: backend/tests/unit/agent_harness/subagent/test_fork.py
Purpose: Unit tests for ForkExecutor (real child loop) + dispatcher.spawn(FORK) round-trip.
Category: Tests / 範疇 11 (Subagent Orchestration)
Scope: Sprint 54.2 US-2 → Sprint 57.94 (real child loop)

Description:
    Sprint 57.94: FORK now drives a REAL child AgentLoop via an injected
    ChildLoopFactory (no single-shot fallback). These tests inject a mock-LLM
    child loop (make_child_loop_factory) and assert the same outward behavior —
    summary / truncation / fail-closed / timeout — now produced by a real loop.

Created: 2026-05-04 (Sprint 54.2)
Last Modified: 2026-06-09

Modification History:
    - 2026-06-09: Convert to real child loop via ChildLoopFactory (Sprint 57.94)
    - 2026-05-04: Initial creation (Sprint 54.2 US-2)
"""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest

from adapters._testing.mock_clients import MockChatClient
from agent_harness._contracts import (
    ChatResponse,
    StopReason,
    SubagentBudget,
    SubagentMode,
    TokenUsage,
)
from agent_harness.subagent import (
    DefaultSubagentDispatcher,
    ForkExecutor,
)

from ._child_loop_helpers import make_child_loop_factory


def _mock_response(text: str, prompt: int = 50, completion: int = 30) -> ChatResponse:
    return ChatResponse(
        model="mock-gpt",
        content=text,
        stop_reason=StopReason.END_TURN,
        usage=TokenUsage(
            prompt_tokens=prompt,
            completion_tokens=completion,
            total_tokens=prompt + completion,
        ),
    )


@pytest.mark.asyncio
async def test_fork_returns_subagent_result_with_summary() -> None:
    """ForkExecutor: child loop returns a final answer → success=True + summary + tokens."""
    chat = MockChatClient(responses=[_mock_response("Subagent did X and Y.")])
    fork = ForkExecutor(child_loop_factory=make_child_loop_factory(chat))
    sid = uuid4()
    result = await fork.execute(
        subagent_id=sid,
        task="Compute X and Y.",
        budget=SubagentBudget(),
    )
    assert result.success is True
    assert result.subagent_id == sid
    assert result.mode == SubagentMode.FORK
    assert "Subagent did X and Y." in result.summary
    assert result.tokens_used == 80  # 50 + 30 (child loop LoopCompleted.total_tokens)
    assert result.error is None


@pytest.mark.asyncio
async def test_fork_summary_truncated_to_cap() -> None:
    """ForkExecutor: child final answer > cap_words=500 → truncated marker appended."""
    long_text = " ".join(["word"] * 1000)  # 1000 words
    chat = MockChatClient(responses=[_mock_response(long_text)])
    fork = ForkExecutor(child_loop_factory=make_child_loop_factory(chat))
    result = await fork.execute(
        subagent_id=uuid4(),
        task="Generate long output",
        budget=SubagentBudget(),
    )
    assert result.success is True
    assert result.summary.endswith("[...truncated]")
    # Truncated to 500 words + truncation marker (1 word) = 501 tokens total
    assert len(result.summary.split()) == 501


@pytest.mark.asyncio
async def test_fork_child_exception_returns_fail_closed() -> None:
    """ForkExecutor: child loop raises (chat error) → SubagentResult(success=False, error=...)."""

    class BrokenChatClient(MockChatClient):
        async def chat(self, request, **kwargs):  # type: ignore[override]
            raise RuntimeError("provider down")

    fork = ForkExecutor(child_loop_factory=make_child_loop_factory(BrokenChatClient()))
    result = await fork.execute(
        subagent_id=uuid4(),
        task="Will fail",
        budget=SubagentBudget(),
    )
    assert result.success is False
    assert result.summary == ""
    assert result.error is not None
    assert "RuntimeError" in result.error
    assert "provider down" in result.error


@pytest.mark.asyncio
async def test_fork_timeout_returns_timeout_error() -> None:
    """ForkExecutor: child loop exceeds budget.max_duration_s → error='timeout: ...'."""

    class SlowChatClient(MockChatClient):
        async def chat(self, request, **kwargs):  # type: ignore[override]
            await asyncio.sleep(0.5)  # Longer than budget below
            return _mock_response("never returned")

    fork = ForkExecutor(child_loop_factory=make_child_loop_factory(SlowChatClient()))
    result = await fork.execute(
        subagent_id=uuid4(),
        task="Slow task",
        budget=SubagentBudget(max_duration_s=0),  # Force immediate timeout
    )
    assert result.success is False
    assert result.error is not None
    assert "timeout" in result.error


@pytest.mark.asyncio
async def test_fork_no_factory_fails_closed() -> None:
    """ForkExecutor without a child_loop_factory fails closed (US-5: no single-shot fallback)."""
    fork = ForkExecutor(child_loop_factory=None)
    result = await fork.execute(
        subagent_id=uuid4(),
        task="cannot run",
        budget=SubagentBudget(),
    )
    assert result.success is False
    assert result.error == "child_loop_factory_unavailable"


@pytest.mark.asyncio
async def test_dispatcher_spawn_fork_then_wait_for_round_trip() -> None:
    """End-to-end: dispatcher.spawn(FORK) → wait_for(uuid) → SubagentResult from a child loop."""
    chat = MockChatClient(responses=[_mock_response("Round-trip OK")])
    dispatcher = DefaultSubagentDispatcher(
        chat_client=chat,
        child_loop_factory=make_child_loop_factory(chat),
    )
    subagent_id = await dispatcher.spawn(
        mode=SubagentMode.FORK,
        task="Test round trip",
        parent_session_id=uuid4(),
    )
    result = await dispatcher.wait_for(subagent_id)
    assert result.subagent_id == subagent_id
    assert result.success is True
    assert "Round-trip OK" in result.summary
