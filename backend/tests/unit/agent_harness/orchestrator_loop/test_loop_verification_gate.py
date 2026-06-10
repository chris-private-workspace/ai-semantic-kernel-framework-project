"""
File: backend/tests/unit/agent_harness/orchestrator_loop/test_loop_verification_gate.py
Purpose: Unit tests for the in-loop Cat 10 verification gate (Sprint 57.98 A1).
Category: Tests / Unit / 範疇 1 + 範疇 10
Scope: Phase 57 / Sprint 57.98 (A1 — verification into the loop)

Description:
    Validates `AgentLoopImpl._cat10_verify_gate` wired into `_run_turns`:
    - PASS → VerificationPassed + deliver (LoopCompleted end_turn), no correction.
    - FAIL with budget left → VerificationFailed(correction_attempt=n) + the failed
      answer + a correction-feedback user Message appended → the NEXT turn re-answers
      in the SAME loop (turn_count++; not a new run), and the correction text reaches
      the next chat() request.
    - FAIL at the budget → LoopCompleted(stop_reason="verification_failed").
    - verifier_registry None → the gate is skipped (byte-identical to pre-57.98).

Created: 2026-06-10 (Sprint 57.98 A1)

Related:
    - backend/src/agent_harness/orchestrator_loop/loop.py (_cat10_verify_gate)
    - backend/src/agent_harness/verification/correction_loop.py (retired wrapper)
"""

from __future__ import annotations

from typing import AsyncIterator, Literal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from adapters._base.chat_client import ChatClient
from adapters._base.pricing import PricingInfo
from adapters._base.types import ModelInfo, StopReason, StreamEvent
from agent_harness._contracts import (
    CacheBreakpoint,
    ChatRequest,
    ChatResponse,
    LLMResponded,
    LoopCompleted,
    LoopEvent,
    Message,
    TokenUsage,
    ToolSpec,
    TraceContext,
    VerificationResult,
)
from agent_harness._contracts.events import VerificationFailed, VerificationPassed
from agent_harness._contracts.state import LoopState
from agent_harness.orchestrator_loop.loop import (
    VERIFICATION_FAILED_STOP_REASON,
    AgentLoopImpl,
)
from agent_harness.orchestrator_loop.termination import TerminationReason
from agent_harness.output_parser import OutputParserImpl
from agent_harness.tools import ToolExecutorImpl, ToolRegistryImpl
from agent_harness.verification import Verifier, VerifierRegistry

pytestmark = pytest.mark.asyncio


# === Fakes ==================================================================


class FakeChatClient(ChatClient):
    """Returns canned (text, stop_reason) per chat() call; records request messages."""

    def __init__(self, texts: list[str]) -> None:
        # Each response is a FINAL answer (no tool calls, END_TURN).
        self._texts = texts
        self._idx = 0
        self.request_messages: list[list[Message]] = []

    async def chat(
        self,
        request: ChatRequest,
        *,
        cache_breakpoints: list[CacheBreakpoint] | None = None,
        trace_context: TraceContext | None = None,
    ) -> ChatResponse:
        self.request_messages.append(list(request.messages))
        if self._idx >= len(self._texts):
            raise RuntimeError("Loop ran more turns than fake responses")
        text = self._texts[self._idx]
        self._idx += 1
        return ChatResponse(
            model="fake",
            content=text,
            tool_calls=None,
            stop_reason=StopReason.END_TURN,
            usage=TokenUsage(prompt_tokens=1, completion_tokens=1),
        )

    def stream(
        self,
        request: ChatRequest,
        *,
        cache_breakpoints: list[CacheBreakpoint] | None = None,
        trace_context: TraceContext | None = None,
    ) -> AsyncIterator[StreamEvent]:
        return self._dummy()

    async def _dummy(self) -> AsyncIterator[StreamEvent]:
        if False:
            yield  # type: ignore[unreachable]

    async def count_tokens(
        self, *, messages: list[Message], tools: list[ToolSpec] | None = None
    ) -> int:
        return 1

    def get_pricing(self) -> PricingInfo:
        return MagicMock(spec=PricingInfo)

    def supports_feature(
        self,
        feature: Literal[
            "thinking",
            "caching",
            "vision",
            "audio",
            "computer_use",
            "structured_output",
            "parallel_tool_calls",
        ],
    ) -> bool:
        return False

    def model_info(self) -> ModelInfo:
        return ModelInfo(
            model_name="fake",
            model_family="fake",
            provider="fake",
            context_window=8192,
            max_output_tokens=4096,
        )


class _PassingVerifier(Verifier):
    async def verify(
        self, *, output: str, state: LoopState, trace_context: TraceContext | None = None
    ) -> VerificationResult:
        return VerificationResult(
            passed=True, verifier_name="passing", verifier_type="rules_based", score=1.0
        )


class _AlwaysFailVerifier(Verifier):
    async def verify(
        self, *, output: str, state: LoopState, trace_context: TraceContext | None = None
    ) -> VerificationResult:
        return VerificationResult(
            passed=False,
            verifier_name="failing",
            verifier_type="rules_based",
            score=0.0,
            reason="always fails",
            suggested_correction="do better",
        )


class _BadWordVerifier(Verifier):
    """Fails iff the output contains the marker word; passes otherwise."""

    def __init__(self, marker: str = "bad") -> None:
        self._marker = marker

    async def verify(
        self, *, output: str, state: LoopState, trace_context: TraceContext | None = None
    ) -> VerificationResult:
        if self._marker in output:
            return VerificationResult(
                passed=False,
                verifier_name="badword",
                verifier_type="rules_based",
                score=0.0,
                reason=f"contains '{self._marker}'",
                suggested_correction="remove it",
            )
        return VerificationResult(
            passed=True, verifier_name="badword", verifier_type="rules_based", score=1.0
        )


# === Builders ===============================================================


def _registry(*verifiers: Verifier) -> VerifierRegistry:
    reg = VerifierRegistry()
    for v in verifiers:
        reg.register(v)
    return reg


def _build_loop(
    *, texts: list[str], verifier_registry: VerifierRegistry | None, max_attempts: int = 2
) -> tuple[FakeChatClient, AgentLoopImpl]:
    chat = FakeChatClient(texts)
    registry = ToolRegistryImpl()
    loop = AgentLoopImpl(
        chat_client=chat,
        output_parser=OutputParserImpl(),
        tool_executor=ToolExecutorImpl(registry=registry, handlers={}),
        tool_registry=registry,
        verifier_registry=verifier_registry,
        max_correction_attempts=max_attempts,
    )
    return chat, loop


async def _drive(loop: AgentLoopImpl) -> list[LoopEvent]:
    return [ev async for ev in loop.run(session_id=uuid4(), user_input="hello")]


# === Tests ==================================================================


async def test_gate_pass_delivers_no_correction() -> None:
    chat, loop = _build_loop(texts=["good answer"], verifier_registry=_registry(_PassingVerifier()))
    events = await _drive(loop)

    passed = [e for e in events if isinstance(e, VerificationPassed)]
    failed = [e for e in events if isinstance(e, VerificationFailed)]
    completed = [e for e in events if isinstance(e, LoopCompleted)]
    assert len(passed) == 1
    assert len(failed) == 0
    assert len(completed) == 1
    assert completed[-1].stop_reason == TerminationReason.END_TURN.value
    assert chat._idx == 1  # one LLM call, no re-run


async def test_gate_fail_then_pass_reinjects_as_new_turn() -> None:
    chat, loop = _build_loop(
        texts=["bad answer", "good answer"],
        verifier_registry=_registry(_BadWordVerifier(marker="bad")),
    )
    events = await _drive(loop)

    failed = [e for e in events if isinstance(e, VerificationFailed)]
    passed = [e for e in events if isinstance(e, VerificationPassed)]
    responded = [e for e in events if isinstance(e, LLMResponded)]
    completed = [e for e in events if isinstance(e, LoopCompleted)]

    # FAIL on "bad answer" (correction_attempt 0-indexed) → PASS on "good answer".
    assert len(failed) == 1
    assert failed[0].correction_attempt == 0
    assert len(passed) == 1
    assert len(responded) == 2  # the failed answer + the corrected answer
    assert completed[-1].stop_reason == TerminationReason.END_TURN.value
    assert chat._idx == 2  # re-ran ONCE (same loop, next turn)

    # The correction feedback reached the 2nd chat() request as a fresh user turn.
    second_request = chat.request_messages[1]
    user_texts = [m.content for m in second_request if m.role == "user"]
    assert any("failed verification" in (t or "") for t in user_texts)
    # The failed answer is in the context as an assistant message.
    assert any(m.role == "assistant" and m.content == "bad answer" for m in second_request)


async def test_gate_fail_at_max_emits_verification_failed() -> None:
    chat, loop = _build_loop(
        texts=["a", "b", "c"],  # attempt 0 fail, 1 fail, 2 fail == max
        verifier_registry=_registry(_AlwaysFailVerifier()),
        max_attempts=2,
    )
    events = await _drive(loop)

    failed = [e for e in events if isinstance(e, VerificationFailed)]
    passed = [e for e in events if isinstance(e, VerificationPassed)]
    completed = [e for e in events if isinstance(e, LoopCompleted)]

    assert len(failed) == 3  # attempts 0, 1, 2
    assert len(passed) == 0
    assert completed[-1].stop_reason == VERIFICATION_FAILED_STOP_REASON
    assert chat._idx == 3


async def test_gate_skipped_when_no_registry() -> None:
    chat, loop = _build_loop(texts=["any answer"], verifier_registry=None)
    events = await _drive(loop)

    assert [e for e in events if isinstance(e, (VerificationPassed, VerificationFailed))] == []
    completed = [e for e in events if isinstance(e, LoopCompleted)]
    assert completed[-1].stop_reason == TerminationReason.END_TURN.value
    assert chat._idx == 1


async def test_gate_skipped_when_empty_registry() -> None:
    # An empty (but non-None) registry → gate gated on len(registry) > 0 → skipped,
    # byte-identical to a non-verified run (the wrapper's empty-registry passthrough).
    chat, loop = _build_loop(texts=["any answer"], verifier_registry=_registry())
    events = await _drive(loop)

    assert [e for e in events if isinstance(e, (VerificationPassed, VerificationFailed))] == []
    completed = [e for e in events if isinstance(e, LoopCompleted)]
    assert completed[-1].stop_reason == TerminationReason.END_TURN.value
    assert chat._idx == 1
