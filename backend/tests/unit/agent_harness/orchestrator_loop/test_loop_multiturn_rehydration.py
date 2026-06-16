"""
File: backend/tests/unit/agent_harness/orchestrator_loop/test_loop_multiturn_rehydration.py
Purpose: Unit tests — Sprint 57.127 loop multi-turn rehydration (MessageStore load + persist).
Category: Tests / 範疇 1 (Orchestrator Loop) + 範疇 7 (State Mgmt)
Scope: Phase 57 / Sprint 57.127 (AD-ChatV2-Live-MultiTurn-Context)

Description:
    Validates AgentLoopImpl's injected MessageStore behavior:
    - run() persists the user prompt (at send start) + the final answer (at
      end_turn) to the ledger — so a follow-up send rehydrates them;
    - run() SELF-LOADS the prior ledger and prepends it to the LLM request (the
      fix: turn 2 now sees turn 1's conversation);
    - message_store=None is the single-turn baseline (no load / no persist).

Modification History (newest-first):
    - 2026-06-16: Initial creation (Sprint 57.127)
"""

from __future__ import annotations

from typing import AsyncIterator, Literal
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
    LoopEvent,
    Message,
    TokenUsage,
    ToolCall,
    ToolSpec,
    TraceContext,
)
from agent_harness.orchestrator_loop.loop import AgentLoopImpl
from agent_harness.output_parser import OutputParserImpl
from agent_harness.state_mgmt import MessageStore
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


class FakeMessageStore(MessageStore):
    """In-memory MessageStore: returns a seeded prior on load(), records append()s."""

    def __init__(self, prior: list[Message] | None = None) -> None:
        self._prior = prior or []
        self.appended: list[Message] = []

    async def load(self) -> list[Message]:
        return list(self._prior)

    async def append(self, messages: list[Message], *, turn_num: int) -> None:
        self.appended.extend(messages)


def _one_turn_chat() -> CapturingChatClient:
    """A single FINAL turn — no tools."""
    return CapturingChatClient(responses=[("Paris", None, StopReason.END_TURN)])


def _build_loop(*, chat_client: ChatClient, message_store: MessageStore | None) -> AgentLoopImpl:
    registry = ToolRegistryImpl()
    return AgentLoopImpl(
        chat_client=chat_client,
        output_parser=OutputParserImpl(),
        tool_executor=ToolExecutorImpl(registry=registry, handlers={}),
        tool_registry=registry,
        tenant_id=_TENANT_ID,
        message_store=message_store,
    )


async def _run(loop: AgentLoopImpl, *, user_input: str) -> list[LoopEvent]:
    sid = uuid4()
    ctx = TraceContext(tenant_id=_TENANT_ID, session_id=sid)
    return [ev async for ev in loop.run(session_id=sid, user_input=user_input, trace_context=ctx)]


def _texts(messages: list[Message]) -> list[str]:
    return [str(m.content) for m in messages]


async def test_run_persists_user_prompt_and_final_answer() -> None:
    """run() appends the user prompt (send start) + the final answer (end_turn)."""
    chat = _one_turn_chat()
    store = FakeMessageStore()
    loop = _build_loop(chat_client=chat, message_store=store)

    await _run(loop, user_input="capital of France?")

    persisted = [(m.role, str(m.content)) for m in store.appended]
    assert ("user", "capital of France?") in persisted
    assert ("assistant", "Paris") in persisted
    # system is NEVER persisted to the ledger.
    assert not any(role == "system" for role, _ in persisted)


async def test_run_rehydrates_prior_into_llm_request() -> None:
    """The injected prior is loaded + prepended → it appears in the LLM request
    (the fix: a follow-up resolves references to the prior turn)."""
    chat = _one_turn_chat()
    store = FakeMessageStore(
        prior=[
            Message(role="user", content="capital of France?"),
            Message(role="assistant", content="Paris"),
        ]
    )
    loop = _build_loop(chat_client=chat, message_store=store)

    await _run(loop, user_input="its population?")

    first_request = _texts(chat.requests[0])
    assert "capital of France?" in first_request  # prior rehydrated...
    assert "Paris" in first_request
    assert "its population?" in first_request  # ...alongside the new user turn
    # Order: prior (oldest-first) then the new user prompt last.
    assert first_request[-1] == "its population?"


async def test_no_store_is_single_turn_baseline() -> None:
    """message_store=None → no load / no persist (today's behavior, no crash)."""
    chat = _one_turn_chat()
    loop = _build_loop(chat_client=chat, message_store=None)

    await _run(loop, user_input="hello")

    # No prior rehydrated — the request is just the new user message.
    assert _texts(chat.requests[0]) == ["hello"]
