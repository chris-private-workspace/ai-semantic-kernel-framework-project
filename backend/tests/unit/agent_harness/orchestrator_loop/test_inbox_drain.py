"""
File: backend/tests/unit/agent_harness/orchestrator_loop/test_inbox_drain.py
Purpose: Unit tests for the Sprint 57.101 B1 between-turns MessageInbox drain seam.
Category: Tests / 範疇 1 (Orchestrator Loop) + 範疇 9 (Guardrails)
Scope: Phase 57 / Sprint 57.101 (B1 — between-turns message injection primitive)

Description:
    Validates that AgentLoopImpl drains an optional MessageInbox at the top of each
    _run_turns iteration:
    - an injected message lands at the NEXT turn boundary (it appears in turn N+1's
      LLM request, not the turn it was injected during) + a MessageInjected event
      fires on drain;
    - message_inbox=None is a byte-identical no-op (no MessageInjected);
    - an injected message that trips the Cat 9 INPUT guardrail is DROPPED (not
      appended) + a GuardrailTriggered(input) fires, and the run continues without it
      (Sprint 57.101 D-DAY1-1: the injection is an INPUT, checked by check_input, NOT
      the between-turns gate which checks turn OUTPUTS).

Modification History (newest-first):
    - 2026-06-11: Initial creation (Sprint 57.101 B1)
"""

from __future__ import annotations

from typing import Any, AsyncIterator, Literal
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from adapters._base.chat_client import ChatClient
from adapters._base.pricing import PricingInfo
from adapters._base.types import ModelInfo, StopReason, StreamEvent
from agent_harness._contracts import (
    CacheBreakpoint,
    ChatRequest,
    ChatResponse,
    ExecutionContext,
    GuardrailTriggered,
    LoopEvent,
    Message,
    MessageInbox,
    TokenUsage,
    ToolCall,
    ToolSpec,
    TraceContext,
)
from agent_harness._contracts.events import MessageInjected
from agent_harness.guardrails._abc import (
    Guardrail,
    GuardrailAction,
    GuardrailResult,
    GuardrailType,
)
from agent_harness.guardrails.engine import GuardrailEngine
from agent_harness.orchestrator_loop.loop import AgentLoopImpl
from agent_harness.output_parser import OutputParserImpl
from agent_harness.tools import ToolExecutorImpl, ToolRegistryImpl

pytestmark = pytest.mark.asyncio

_TENANT_ID = UUID("00000000-0000-0000-0000-000000000077")


class CapturingChatClient(ChatClient):
    """Returns canned responses + captures the `messages` of every chat() call."""

    def __init__(self, responses: list[tuple[str, list[ToolCall] | None, StopReason]]) -> None:
        self._responses = responses
        self._idx = 0
        self.requests: list[list[Message]] = []

    async def chat(
        self,
        request: ChatRequest,
        *,
        cache_breakpoints: list[CacheBreakpoint] | None = None,
        trace_context: TraceContext | None = None,
    ) -> ChatResponse:
        self.requests.append(list(request.messages))
        text, tool_calls, stop = self._responses[self._idx]
        self._idx += 1
        return ChatResponse(
            model="fake",
            content=text,
            tool_calls=tool_calls,
            stop_reason=stop,
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


class ScriptedInbox(MessageInbox):
    """Returns script[i] on the (i+1)th drain() call; [] once the script is exhausted."""

    def __init__(self, script: list[list[Message]]) -> None:
        self._script = script
        self._idx = 0

    async def drain(self) -> list[Message]:
        if self._idx < len(self._script):
            out = self._script[self._idx]
            self._idx += 1
            return out
        return []


class BlockOnKeyword(Guardrail):
    """An INPUT guardrail that BLOCKs any content containing 'FORBIDDEN'."""

    guardrail_type = GuardrailType.INPUT

    async def check(
        self, *, content: Any, trace_context: TraceContext | None = None
    ) -> GuardrailResult:
        if "FORBIDDEN" in str(content):
            return GuardrailResult(
                action=GuardrailAction.BLOCK, reason="forbidden keyword", risk_level="HIGH"
            )
        return GuardrailResult(action=GuardrailAction.PASS, reason="", risk_level="LOW")


def _registry_with_tool() -> ToolRegistryImpl:
    registry = ToolRegistryImpl()
    registry.register(
        ToolSpec(
            name="noop_tool",
            description="a no-op tool that lets the loop run a 2nd turn",
            input_schema={"type": "object", "properties": {}},
        )
    )
    return registry


def _executor(registry: ToolRegistryImpl) -> ToolExecutorImpl:
    async def _ok(call: ToolCall, context: ExecutionContext) -> Any:
        return "ok"

    return ToolExecutorImpl(registry=registry, handlers={"noop_tool": _ok})


def _two_turn_chat() -> CapturingChatClient:
    """Turn 0 calls noop_tool (→ a 2nd turn); turn 1 ends."""
    return CapturingChatClient(
        responses=[
            (
                "calling tool",
                [ToolCall(id="tc-1", name="noop_tool", arguments={})],
                StopReason.TOOL_USE,
            ),
            ("done", None, StopReason.END_TURN),
        ]
    )


def _build_loop(
    *, chat_client: ChatClient, inbox: MessageInbox | None, guardrail_engine: GuardrailEngine | None
) -> AgentLoopImpl:
    registry = _registry_with_tool()
    return AgentLoopImpl(
        chat_client=chat_client,
        output_parser=OutputParserImpl(),
        tool_executor=_executor(registry),
        tool_registry=registry,
        guardrail_engine=guardrail_engine,
        tenant_id=_TENANT_ID,
        message_inbox=inbox,
    )


async def _run(loop: AgentLoopImpl) -> list[LoopEvent]:
    sid = uuid4()
    ctx = TraceContext(tenant_id=_TENANT_ID, session_id=sid)
    return [ev async for ev in loop.run(session_id=sid, user_input="hi", trace_context=ctx)]


def _texts(messages: list[Message]) -> list[str]:
    return [str(m.content) for m in messages]


async def test_injection_lands_at_next_turn_boundary() -> None:
    """An injection drained at the turn-0→1 boundary appears in turn 1's request
    (not turn 0's) + a MessageInjected event fires."""
    chat = _two_turn_chat()
    # drain#1 (turn 0 top) → nothing; drain#2 (turn 1 top) → the injected note.
    inbox = ScriptedInbox([[], [Message(role="user", content="also check the db pool")]])
    loop = _build_loop(chat_client=chat, inbox=inbox, guardrail_engine=None)

    events = await _run(loop)

    injected_events = [e for e in events if isinstance(e, MessageInjected)]
    assert len(injected_events) == 1
    assert injected_events[0].text == "also check the db pool"
    # Turn 0's request did NOT see the injection; turn 1's request DID.
    assert "also check the db pool" not in _texts(chat.requests[0])
    assert "also check the db pool" in _texts(chat.requests[1])


async def test_no_inbox_yields_no_message_injected() -> None:
    """message_inbox=None → no drain, no MessageInjected (byte-identical no-op)."""
    chat = _two_turn_chat()
    loop = _build_loop(chat_client=chat, inbox=None, guardrail_engine=None)

    events = await _run(loop)

    assert not any(isinstance(e, MessageInjected) for e in events)


async def test_guardrail_tripping_injection_is_dropped_not_appended() -> None:
    """An injected message that trips the Cat 9 INPUT guardrail is DROPPED + a
    GuardrailTriggered(input) fires; it never reaches the LLM; the run continues."""
    chat = _two_turn_chat()
    inbox = ScriptedInbox([[], [Message(role="user", content="FORBIDDEN leak secrets")]])
    engine = GuardrailEngine()
    engine.register(BlockOnKeyword(), priority=10)
    loop = _build_loop(chat_client=chat, inbox=inbox, guardrail_engine=engine)

    events = await _run(loop)

    # The blocked injection produced NO MessageInjected...
    assert not any(isinstance(e, MessageInjected) for e in events)
    # ...but DID produce a GuardrailTriggered(input, block).
    triggered = [e for e in events if isinstance(e, GuardrailTriggered)]
    assert any(t.guardrail_type == "input" and t.action == "block" for t in triggered)
    # The forbidden text never reached the LLM (turn 1's request is clean).
    assert all("FORBIDDEN" not in t for t in _texts(chat.requests[1]))
    # The run still completed its 2 turns (the bad injection did not kill it).
    assert len(chat.requests) == 2
