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
        # Sprint 57.129: record each append() as its own batch so a test can assert
        # the tool round-trip arrives as ONE atomic call (dangling-free evidence).
        self.append_calls: list[list[Message]] = []

    async def load(self) -> list[Message]:
        return list(self._prior)

    async def append(self, messages: list[Message], *, turn_num: int) -> None:
        self.appended.extend(messages)
        self.append_calls.append(list(messages))


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


# Sprint 57.129 — a tool result that is NOT echoed in the final answer, so a
# rehydration test proves the `tool` message (not just the answer) is persisted.
_TOOL_RESULT = "factorial(8) = 40320"


def _build_tool_loop(
    *, chat_client: ChatClient, message_store: MessageStore | None
) -> AgentLoopImpl:
    """A loop with one registered tool (`calc_tool`) whose handler returns
    `_TOOL_RESULT`, so a TOOL_USE turn produces a real tool round-trip."""
    registry = ToolRegistryImpl()
    registry.register(
        ToolSpec(
            name="calc_tool",
            description="a calculator tool",
            input_schema={"type": "object", "properties": {}},
        )
    )

    async def _calc(call: ToolCall, context: ExecutionContext) -> Any:
        return _TOOL_RESULT

    return AgentLoopImpl(
        chat_client=chat_client,
        output_parser=OutputParserImpl(),
        tool_executor=ToolExecutorImpl(registry=registry, handlers={"calc_tool": _calc}),
        tool_registry=registry,
        tenant_id=_TENANT_ID,
        message_store=message_store,
    )


def _tool_then_final_chat() -> CapturingChatClient:
    """Turn 0 calls calc_tool (→ a tool round-trip + a 2nd turn); turn 1 ends."""
    return CapturingChatClient(
        responses=[
            (
                "let me compute",
                [ToolCall(id="tc-1", name="calc_tool", arguments={"n": 8})],
                StopReason.TOOL_USE,
            ),
            ("it is even", None, StopReason.END_TURN),
        ]
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


async def test_run_persists_tool_round_trip() -> None:
    """Sprint 57.129: a tool turn persists the COMPLETE intra-turn round-trip
    ([assistant tool_use, tool result]) to the ledger — not just the user prompt +
    final answer (57.127), so a follow-up send rehydrates the full tool context."""
    chat = _tool_then_final_chat()
    store = FakeMessageStore()
    loop = _build_tool_loop(chat_client=chat, message_store=store)

    await _run(loop, user_input="factorial of 8 even or odd?")

    roles = [m.role for m in store.appended]
    # user prompt + assistant(tool_use) + tool result + final answer.
    assert roles == ["user", "assistant", "tool", "assistant"]
    # the assistant tool_use carries its tool_calls...
    assistant_tool_use = store.appended[1]
    assert assistant_tool_use.tool_calls is not None
    assert assistant_tool_use.tool_calls[0].name == "calc_tool"
    # ...and the tool result is correlated by tool_call_id + carries the result text
    # (which is NEVER stated in the final answer "it is even").
    tool_result = store.appended[2]
    assert tool_result.tool_call_id == "tc-1"
    assert _TOOL_RESULT in str(tool_result.content)
    # final answer last; the answer never contains the tool result.
    assert store.appended[3].role == "assistant"
    assert str(store.appended[3].content) == "it is even"
    assert _TOOL_RESULT not in str(store.appended[3].content)


async def test_tool_round_trip_persisted_atomically() -> None:
    """The tool round-trip is persisted as ONE append() call ([assistant tool_use,
    tool result]) — never a separate/dangling persist of the bare tool_use. This is
    the dangling-free guarantee: a load() never sees a tool_use without its result."""
    chat = _tool_then_final_chat()
    store = FakeMessageStore()
    loop = _build_tool_loop(chat_client=chat, message_store=store)

    await _run(loop, user_input="factorial of 8 even or odd?")

    # Exactly one append() carries a tool_use; it carries the matching result too.
    batch_calls = [call for call in store.append_calls if any(m.tool_calls for m in call)]
    assert len(batch_calls) == 1
    batch = batch_calls[0]
    assert [m.role for m in batch] == ["assistant", "tool"]
    assert batch[0].tool_calls is not None
    assert batch[1].tool_call_id == "tc-1"


async def test_prior_tool_round_trip_rehydrated() -> None:
    """A prior ledger containing a tool round-trip is loaded + prepended → the tool
    assistant/result messages appear in the LLM request (the missing-capability the
    AD closes: a follow-up can reference the prior tool result)."""
    chat = _one_turn_chat()  # the follow-up just ends
    store = FakeMessageStore(
        prior=[
            Message(role="user", content="factorial of 8 even or odd?"),
            Message(
                role="assistant",
                content="let me compute",
                tool_calls=[ToolCall(id="tc-1", name="calc_tool", arguments={"n": 8})],
            ),
            Message(role="tool", content=_TOOL_RESULT, tool_call_id="tc-1"),
            Message(role="assistant", content="it is even"),
        ]
    )
    loop = _build_loop(chat_client=chat, message_store=store)

    await _run(loop, user_input="what was the exact number?")

    first_request = chat.requests[0]
    # the tool result text rehydrated (recoverable ONLY from the `tool` message)...
    assert any(m.role == "tool" and str(m.content) == _TOOL_RESULT for m in first_request)
    # ...alongside the assistant tool_use with its tool_calls preserved...
    assert any(m.role == "assistant" and m.tool_calls for m in first_request)
    # ...and the new user turn last.
    assert str(first_request[-1].content) == "what was the exact number?"
