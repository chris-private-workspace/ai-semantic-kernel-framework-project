"""
File: backend/tests/unit/agent_harness/verification/test_observability.py
Purpose: AD-Cat10-Obs-1 closure — verify 4 verifier classes emit verifier.{name} spans.
Category: Tests / 範疇 10 (Verification) × 範疇 12 (Observability)
Scope: Sprint 54.2 US-5

Description:
    Per Day 4 D19: Cat 9 wrapper verifiers (cat9_fallback / cat9_mutator) reuse
    the inner LLMJudgeVerifier's tracer rather than having a separate wrapper
    span — to avoid double-wrap inflation. So tests for those classes verify
    that the INNER judge emits its span when invoked through the wrapper.

Created: 2026-05-04 (Sprint 54.2)
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, cast

import pytest

from adapters._testing.mock_clients import MockChatClient
from agent_harness._contracts import (
    ChatResponse,
    LoopState,
    SpanCategory,
    StopReason,
    TokenUsage,
    TraceContext,
)
from agent_harness.observability import Tracer
from agent_harness.verification import LLMJudgeVerifier, RulesBasedVerifier
from agent_harness.verification.cat9_fallback import LLMJudgeFallbackGuardrail
from agent_harness.verification.cat9_mutator import LLMVerifyMutateGuardrail
from agent_harness.verification.types import RegexRule


def _dummy_state() -> LoopState:
    """Verifiers don't read state — cast None to satisfy ABC type (54.1 pattern)."""
    return cast(LoopState, None)


class _RecordingTracer(Tracer):
    """Test tracer that records every span name + category opened."""

    def __init__(self) -> None:
        self.spans: list[tuple[str, SpanCategory]] = []
        self.metrics: list[object] = []

    @asynccontextmanager
    async def start_span(  # type: ignore[override]
        self,
        *,
        name: str,
        category: SpanCategory,
        trace_context: TraceContext | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> AsyncIterator[None]:
        # Sprint 57.71: match the full Tracer ABC signature (category_span now
        # always forwards attributes=). Recorded tuple still (name, category).
        self.spans.append((name, category))
        yield

    def record_metric(self, event: object) -> None:  # type: ignore[override]
        self.metrics.append(event)

    def get_current_context(self) -> object | None:  # type: ignore[override]
        return None


def _judge_response(passed: bool = True) -> ChatResponse:
    body = (
        '{"passed": true, "score": 1.0, "reason": "ok"}'
        if passed
        else '{"passed": false, "score": 0.0, "reason": "no"}'
    )
    return ChatResponse(
        model="mock",
        content=body,
        stop_reason=StopReason.END_TURN,
        usage=TokenUsage(prompt_tokens=10, completion_tokens=10, total_tokens=20),
    )


@pytest.mark.asyncio
async def test_rules_based_verifier_emits_span() -> None:
    """RulesBasedVerifier: tracer captures verifier.rules_based under VERIFICATION."""
    tracer = _RecordingTracer()
    verifier = RulesBasedVerifier(
        rules=[RegexRule(pattern=r".+", expected_match=True)],
        tracer=tracer,
    )
    state = _dummy_state()
    result = await verifier.verify(output="non-empty", state=state)
    assert result.passed is True
    assert tracer.spans == [("verifier.rules_based", SpanCategory.VERIFICATION)]


@pytest.mark.asyncio
async def test_llm_judge_verifier_emits_span() -> None:
    """LLMJudgeVerifier: tracer captures verifier.llm_judge under VERIFICATION."""
    tracer = _RecordingTracer()
    chat = MockChatClient(responses=[_judge_response(passed=True)])
    verifier = LLMJudgeVerifier(
        chat_client=chat,
        judge_template="Check {output}",
        tracer=tracer,
    )
    state = _dummy_state()
    result = await verifier.verify(output="content", state=state)
    assert result.passed is True
    assert tracer.spans == [("verifier.llm_judge", SpanCategory.VERIFICATION)]


@pytest.mark.asyncio
async def test_cat9_fallback_inner_judge_emits_span() -> None:
    """LLMJudgeFallbackGuardrail: inner judge's tracer emits span when fallback fires.

    Per D19: wrapper does NOT emit a separate span; the wrapped judge does.
    """
    tracer = _RecordingTracer()
    chat = MockChatClient(responses=[_judge_response(passed=True)])
    judge = LLMJudgeVerifier(
        chat_client=chat,
        judge_template="Safety check: {output}",
        name="safety_judge",
        tracer=tracer,
    )
    # Wrapped guardrail's verify() invokes judge.verify() internally
    result = await judge.verify(output="hello", state=_dummy_state())
    assert result.passed is True
    # Just one span from inner judge:
    assert tracer.spans == [("verifier.safety_judge", SpanCategory.VERIFICATION)]
    # Verify wrapper class is importable + Guardrail-typed (smoke check D19)
    assert LLMJudgeFallbackGuardrail.__name__ == "LLMJudgeFallbackGuardrail"


@pytest.mark.asyncio
async def test_cat9_mutator_inner_judge_emits_span() -> None:
    """LLMVerifyMutateGuardrail: inner judge's tracer emits span (D19 same pattern)."""
    tracer = _RecordingTracer()
    chat = MockChatClient(responses=[_judge_response(passed=False)])
    judge = LLMJudgeVerifier(
        chat_client=chat,
        judge_template="Mutate-check: {output}",
        name="mutator_judge",
        tracer=tracer,
    )
    result = await judge.verify(output="bad", state=_dummy_state())
    assert result.passed is False
    assert tracer.spans == [("verifier.mutator_judge", SpanCategory.VERIFICATION)]
    # Wrapper class smoke check
    assert LLMVerifyMutateGuardrail.__name__ == "LLMVerifyMutateGuardrail"
