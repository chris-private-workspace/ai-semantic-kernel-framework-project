"""
File: backend/tests/unit/agent_harness/verification/test_inloop_gate_persist.py
Purpose: In-loop Cat 10 gate — best-effort verification_log persistence hook.
Category: Tests / Unit / 範疇 1 + 範疇 10 / persistence
Scope: Sprint 57.98 A1 (converted from the retired run_with_verification wrapper suite)

Description:
    Converted (Sprint 57.98 A1, Never-Delete via git mv from
    test_correction_loop_persist.py) from the retired run_with_verification wrapper
    to the in-loop gate. The verification_log write hook (Sprint 57.11 US-2) now
    fires from `AgentLoopImpl._cat10_verify_gate`, which calls the SHARED
    `agent_harness.verification.persistence.persist_verification_event`:
    - Passed verifier → persist called with passed=True + correction_attempt=0
    - Failed verifier (max_attempts=0 → 1 verify, no re-run) → passed=False + reason
    - DB raise (get_session_factory) → loop continues, event stream unbroken

    Mocks the package re-export `agent_harness.verification.persist_verification_event`
    (where the gate's lazy `from agent_harness.verification import …` resolves the name)
    to isolate the verifier→hook contract from DB concerns; the DB layer is covered
    by integration tests in tests/integration/api/test_verification.py.

Created: 2026-05-10 (Sprint 57.11 Day 1 / US-2, as test_correction_loop_persist.py)
Last Modified: 2026-06-10 (Sprint 57.98 A1 — converted to the in-loop gate)

Related:
    - backend/src/agent_harness/orchestrator_loop/loop.py (_cat10_verify_gate)
    - backend/src/agent_harness/verification/persistence.py (persist_verification_event)
    - infrastructure/db/repositories/verification_log.py
"""

from __future__ import annotations

from typing import AsyncIterator, Literal
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from adapters._base.chat_client import ChatClient
from adapters._base.pricing import PricingInfo
from adapters._base.types import ModelInfo, StopReason, StreamEvent
from agent_harness._contracts import (
    CacheBreakpoint,
    ChatRequest,
    ChatResponse,
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
from agent_harness.orchestrator_loop.loop import AgentLoopImpl
from agent_harness.output_parser import OutputParserImpl
from agent_harness.tools import ToolExecutorImpl, ToolRegistryImpl
from agent_harness.verification import Verifier, VerifierRegistry

pytestmark = pytest.mark.asyncio


# === Fakes ==================================================================


class _FinalChatClient(ChatClient):
    """Single-shot stub: one FINAL (END_TURN) answer, then refuses further turns."""

    def __init__(self, content: str = "stub-output") -> None:
        self._content = content
        self._done = False

    async def chat(
        self,
        request: ChatRequest,
        *,
        cache_breakpoints: list[CacheBreakpoint] | None = None,
        trace_context: TraceContext | None = None,
    ) -> ChatResponse:
        if self._done:
            raise RuntimeError("Loop ran more turns than expected")
        self._done = True
        return ChatResponse(
            model="fake",
            content=self._content,
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
    def __init__(self, name: str = "v_pass") -> None:
        self.name = name

    async def verify(
        self, *, output: str, state: LoopState, trace_context: TraceContext | None = None
    ) -> VerificationResult:
        return VerificationResult(
            passed=True, verifier_name=self.name, verifier_type="rules_based", score=0.95
        )


class _FailingVerifier(Verifier):
    def __init__(self, name: str = "v_fail") -> None:
        self.name = name

    async def verify(
        self, *, output: str, state: LoopState, trace_context: TraceContext | None = None
    ) -> VerificationResult:
        return VerificationResult(
            passed=False,
            verifier_name=self.name,
            verifier_type="llm_judge",
            reason="contains forbidden token",
            suggested_correction="redact and retry",
        )


def _registry(*verifiers: Verifier) -> VerifierRegistry:
    reg = VerifierRegistry()
    for v in verifiers:
        reg.register(v)
    return reg


def _build_loop(*, verifier_registry: VerifierRegistry, max_attempts: int = 2) -> AgentLoopImpl:
    registry = ToolRegistryImpl()
    return AgentLoopImpl(
        chat_client=_FinalChatClient(),
        output_parser=OutputParserImpl(),
        tool_executor=ToolExecutorImpl(registry=registry, handlers={}),
        tool_registry=registry,
        verifier_registry=verifier_registry,
        max_correction_attempts=max_attempts,
    )


def _trace_with_tenant(tenant_id: UUID) -> TraceContext:
    base = TraceContext.create_root()
    return TraceContext(
        trace_id=base.trace_id,
        span_id=base.span_id,
        parent_span_id=base.parent_span_id,
        tenant_id=tenant_id,
        user_id=base.user_id,
        session_id=base.session_id,
        baggage=base.baggage,
    )


async def _drive(loop: AgentLoopImpl, *, session_id: UUID, trace: TraceContext) -> list[LoopEvent]:
    return [
        ev async for ev in loop.run(session_id=session_id, user_input="hello", trace_context=trace)
    ]


# === Tests ==================================================================


async def test_persist_passed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Passing verifier → persist_verification_event called with passed=True."""
    persist_mock = AsyncMock()
    monkeypatch.setattr(
        "agent_harness.verification.persist_verification_event", persist_mock
    )

    tenant_id, session_id = uuid4(), uuid4()
    loop = _build_loop(verifier_registry=_registry(_PassingVerifier("v1")))
    events = await _drive(loop, session_id=session_id, trace=_trace_with_tenant(tenant_id))

    assert persist_mock.await_count == 1
    call_kwargs = persist_mock.await_args.kwargs
    assert call_kwargs["tenant_id"] == tenant_id
    assert call_kwargs["session_id"] == session_id
    assert call_kwargs["passed"] is True
    assert call_kwargs["verifier_name"] == "v1"
    assert call_kwargs["verifier_type"] == "rules_based"
    assert call_kwargs["score"] == 0.95
    assert call_kwargs["correction_attempt"] == 0

    assert any(isinstance(e, VerificationPassed) for e in events)
    assert any(isinstance(e, LoopCompleted) for e in events)


async def test_persist_failed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Failing verifier (max_attempts=0 → no re-run) → persist passed=False + reason."""
    persist_mock = AsyncMock()
    monkeypatch.setattr(
        "agent_harness.verification.persist_verification_event", persist_mock
    )

    tenant_id, session_id = uuid4(), uuid4()
    loop = _build_loop(verifier_registry=_registry(_FailingVerifier("vF")), max_attempts=0)
    events = await _drive(loop, session_id=session_id, trace=_trace_with_tenant(tenant_id))

    assert persist_mock.await_count == 1
    call_kwargs = persist_mock.await_args.kwargs
    assert call_kwargs["passed"] is False
    assert call_kwargs["reason"] == "contains forbidden token"
    assert call_kwargs["suggested_correction"] == "redact and retry"
    assert call_kwargs["verifier_type"] == "llm_judge"
    assert call_kwargs["correction_attempt"] == 0

    assert any(isinstance(e, VerificationFailed) for e in events)


async def test_persist_failure_silent(monkeypatch: pytest.MonkeyPatch) -> None:
    """Persist DB error → loop continues, event stream unbroken.

    Exercises the REAL persist_verification_event with get_session_factory made to
    raise so the helper's try/except path triggers; the gate must NOT see the error.
    """

    def _raise_factory() -> object:
        raise RuntimeError("simulated DB outage")

    monkeypatch.setattr(
        "agent_harness.verification.persistence.get_session_factory", _raise_factory
    )

    tenant_id, session_id = uuid4(), uuid4()
    loop = _build_loop(verifier_registry=_registry(_PassingVerifier("v_silent")))
    events = await _drive(loop, session_id=session_id, trace=_trace_with_tenant(tenant_id))

    # Despite the simulated DB outage, the loop completes successfully.
    assert any(isinstance(e, VerificationPassed) for e in events)
    assert any(isinstance(e, LoopCompleted) for e in events)
