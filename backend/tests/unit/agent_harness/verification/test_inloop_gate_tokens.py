"""
File: backend/tests/unit/agent_harness/verification/test_inloop_gate_tokens.py
Purpose: In-loop Cat 10 gate — judge-token accumulation/stamping + non-final skip.
Category: Tests / Unit / 範疇 1 + 範疇 10
Scope: Sprint 57.98 A1 (converted from the retired run_with_verification wrapper suite)

Description:
    Converted (Sprint 57.98 A1, Never-Delete via git mv from test_correction_loop.py)
    from the retired run_with_verification wrapper to the in-loop gate
    (AgentLoopImpl._cat10_verify_gate wired into _run_turns). Covers the judge-token
    accounting the wrapper used to do — now stamped on the terminal LoopCompleted by
    the loop itself (Sprint 57.82) — plus the non-final skip invariant:
    - all-pass        → terminal LoopCompleted carries the judge tokens + model
    - 1 correction    → tokens summed across BOTH judge runs
    - all fail (==max)→ verification_failed terminal carries summed tokens
    - non-final (tool-loop hits max_turns) → gate never runs → tokens 0 / model None
    - no registry     → gate dormant → tokens 0 (byte-identical)

    The core PASS / FAIL-then-PASS / FAIL-at-max behaviors live in the sibling
    orchestrator_loop/test_loop_verification_gate.py.

Created: 2026-05-04 (Sprint 54.1 Day 3, as test_correction_loop.py)
Last Modified: 2026-06-10 (Sprint 57.98 A1 — converted to the in-loop gate)

Related:
    - backend/src/agent_harness/orchestrator_loop/loop.py (_cat10_verify_gate / _run_turns)
    - backend/tests/unit/agent_harness/orchestrator_loop/test_loop_verification_gate.py
"""

from __future__ import annotations

from typing import Any, AsyncIterator, Literal
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
    ExecutionContext,
    LoopCompleted,
    LoopEvent,
    Message,
    TokenUsage,
    ToolCall,
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
    """Returns canned ChatResponses per chat() call.

    `clamp=True` returns the LAST response once exhausted (for a tool-loop that
    must keep producing tool_use until the loop hits max_turns); `clamp=False`
    raises on over-run so the strict token tests catch an unexpected extra turn.
    """

    def __init__(self, responses: list[ChatResponse], *, clamp: bool = False) -> None:
        self._responses = responses
        self._idx = 0
        self.clamp = clamp
        self.calls = 0

    async def chat(
        self,
        request: ChatRequest,
        *,
        cache_breakpoints: list[CacheBreakpoint] | None = None,
        trace_context: TraceContext | None = None,
    ) -> ChatResponse:
        self.calls += 1
        if self._idx >= len(self._responses):
            if self.clamp:
                return self._responses[-1]
            raise RuntimeError("Loop ran more turns than fake responses")
        r = self._responses[self._idx]
        self._idx += 1
        return r

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


def _final(content: str) -> ChatResponse:
    return ChatResponse(
        model="fake",
        content=content,
        tool_calls=None,
        stop_reason=StopReason.END_TURN,
        usage=TokenUsage(prompt_tokens=1, completion_tokens=1),
    )


def _tool_use() -> ChatResponse:
    return ChatResponse(
        model="fake",
        content="",
        tool_calls=[ToolCall(id="tc-1", name="noop_tool", arguments={})],
        stop_reason=StopReason.TOOL_USE,
        usage=TokenUsage(prompt_tokens=1, completion_tokens=1),
    )


class _TokenVerifier(Verifier):
    """Reports fixed judge token usage per call; verdict per call from a list.

    verdicts[i] drives the i-th verify() (clamped to the last entry once
    exhausted), so a single False verdict means "always fail" across attempts.
    """

    def __init__(
        self,
        *,
        verdicts: list[bool],
        in_tok: int = 100,
        out_tok: int = 10,
        model: str = "judge-m",
        name: str = "tok",
    ) -> None:
        self.name = name
        self._verdicts = list(verdicts)
        self._in = in_tok
        self._out = out_tok
        self._model = model
        self.calls = 0

    async def verify(
        self, *, output: str, state: LoopState, trace_context: TraceContext | None = None
    ) -> VerificationResult:
        idx = min(self.calls, len(self._verdicts) - 1)
        passed = self._verdicts[idx]
        self.calls += 1
        return VerificationResult(
            passed=passed,
            verifier_name=self.name,
            verifier_type="llm_judge",
            score=1.0 if passed else 0.0,
            reason=None if passed else "bad",
            suggested_correction=None if passed else "fix it",
            input_tokens=self._in,
            output_tokens=self._out,
            model=self._model,
        )


# === Builders ===============================================================


def _registry(*verifiers: Verifier) -> VerifierRegistry:
    reg = VerifierRegistry()
    for v in verifiers:
        reg.register(v)
    return reg


def _build_loop(
    *,
    responses: list[ChatResponse],
    verifier_registry: VerifierRegistry | None,
    max_attempts: int = 2,
    max_turns: int = 8,
    clamp: bool = False,
    with_noop_tool: bool = False,
) -> tuple[FakeChatClient, AgentLoopImpl]:
    chat = FakeChatClient(responses, clamp=clamp)
    registry = ToolRegistryImpl()
    handlers: dict[str, Any] = {}
    if with_noop_tool:
        registry.register(
            ToolSpec(name="noop_tool", description="no-op", input_schema={"type": "object"})
        )

        async def _ok(call: ToolCall, context: ExecutionContext) -> Any:
            return "ok"

        handlers["noop_tool"] = _ok
    loop = AgentLoopImpl(
        chat_client=chat,
        output_parser=OutputParserImpl(),
        tool_executor=ToolExecutorImpl(registry=registry, handlers=handlers),
        tool_registry=registry,
        verifier_registry=verifier_registry,
        max_correction_attempts=max_attempts,
        max_turns=max_turns,
    )
    return chat, loop


async def _drive(loop: AgentLoopImpl) -> list[LoopEvent]:
    return [ev async for ev in loop.run(session_id=uuid4(), user_input="q")]


# === Tests ==================================================================


async def test_judge_tokens_stamped_on_passing_completion() -> None:
    """(a) all-pass → terminal LoopCompleted carries the judge tokens + model."""
    _, loop = _build_loop(
        responses=[_final("ok")],
        verifier_registry=_registry(
            _TokenVerifier(verdicts=[True], in_tok=120, out_tok=8, model="gpt-5.2-judge")
        ),
    )
    events = await _drive(loop)
    completion = [e for e in events if isinstance(e, LoopCompleted)][-1]
    assert completion.stop_reason == TerminationReason.END_TURN.value
    assert completion.verification_input_tokens == 120
    assert completion.verification_output_tokens == 8
    assert completion.verification_model == "gpt-5.2-judge"


async def test_judge_tokens_summed_across_correction_attempts() -> None:
    """(b) 1 correction then pass → tokens summed across BOTH judge runs."""
    _, loop = _build_loop(
        responses=[_final("bad"), _final("good")],
        verifier_registry=_registry(_TokenVerifier(verdicts=[False, True], in_tok=100, out_tok=10)),
    )
    events = await _drive(loop)
    completion = [e for e in events if isinstance(e, LoopCompleted)][-1]
    assert completion.stop_reason == TerminationReason.END_TURN.value
    assert completion.verification_input_tokens == 200  # 2 judge runs
    assert completion.verification_output_tokens == 20


async def test_judge_tokens_summed_on_exhausted_completion() -> None:
    """(c) all attempts fail → verification_failed terminal carries summed tokens."""
    _, loop = _build_loop(
        responses=[_final("b1"), _final("b2"), _final("b3")],
        verifier_registry=_registry(_TokenVerifier(verdicts=[False], in_tok=100, out_tok=10)),
        max_attempts=2,
    )
    events = await _drive(loop)
    completion = [e for e in events if isinstance(e, LoopCompleted)][-1]
    assert completion.stop_reason == VERIFICATION_FAILED_STOP_REASON
    assert completion.verification_input_tokens == 300  # attempts 0,1,2
    assert completion.verification_output_tokens == 30


async def test_judge_tokens_zero_on_non_final() -> None:
    """(d) non-final (tool-loop hits max_turns) → gate never runs → tokens 0."""
    verifier = _TokenVerifier(verdicts=[True], in_tok=100, out_tok=10)
    _, loop = _build_loop(
        responses=[_tool_use()],
        verifier_registry=_registry(verifier),
        max_turns=2,
        clamp=True,  # keep returning tool_use until max_turns terminates the loop
        with_noop_tool=True,
    )
    events = await _drive(loop)
    completion = [e for e in events if isinstance(e, LoopCompleted)][-1]
    # The loop never produced a FINAL answer → the gate never fired.
    assert completion.stop_reason != TerminationReason.END_TURN.value
    assert verifier.calls == 0
    assert not any(isinstance(e, (VerificationPassed, VerificationFailed)) for e in events)
    assert completion.verification_input_tokens == 0
    assert completion.verification_output_tokens == 0
    assert completion.verification_model is None


async def test_judge_tokens_zero_on_no_registry() -> None:
    """(e) no registry → gate dormant → terminal LoopCompleted carries 0 tokens."""
    _, loop = _build_loop(responses=[_final("any")], verifier_registry=None)
    events = await _drive(loop)
    completion = [e for e in events if isinstance(e, LoopCompleted)][-1]
    assert completion.verification_input_tokens == 0
    assert completion.verification_output_tokens == 0
    assert completion.verification_model is None
    assert not any(isinstance(e, (VerificationPassed, VerificationFailed)) for e in events)
