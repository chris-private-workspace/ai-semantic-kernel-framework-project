"""
File: backend/tests/integration/api/test_chat_tier2_wiring.py
Purpose: Integration tests proving Sprint 57.65 A-1 Tier2 — the production chat
    path now RENDERS a per-turn, capped (≤2000-token) memory summary into the
    assembled system prompt + injects verify-before-use rules, fed by the SAME
    MemoryRetrieval the executor's memory tools use.
Category: Tests / integration / api
Scope: Phase 57 / Sprint 57.65

Description:
    Mirrors test_chat_keystone_wiring.py: fake AZURE_OPENAI_* env so
    build_real_llm_handler constructs the adapter config (no network), then swap
    loop._chat_client for a MockChatClient before run(). The MockChatClient
    records last_request, so we read the FINAL turn's assembled prompt messages
    and assert the rendered memory block is present.

    - render: a session memory written earlier in the run is rendered into a
      later turn's assembled system prompt; PromptBuilt.memory_layers_used is
      non-empty.
    - verify_before_use: a flagged hint surfaces the lead-then-verify rule.
    - cross-tenant: a tenant-B build shows none of tenant-A's session memory.
    - negative: the empty-MemoryRetrieval standalone path renders no memory block
      and the run still completes.

Created: 2026-06-01 (Sprint 57.65)
Last Modified: 2026-06-01

Modification History (newest-first):
    - 2026-06-01: Sprint 57.65 A-2 Tier2 — add prompt-cache observability section
        (LoopCompleted.cached_input_tokens + cache_hit_rate from MockChatClient usage)
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from adapters._testing.mock_clients import MockChatClient
from agent_harness._contracts import (
    ChatResponse,
    PromptBuilt,
    StopReason,
    TokenUsage,
    ToolCall,
)
from agent_harness.prompt_builder.templates import VERIFY_BEFORE_USE_HEADER
from api.v1.chat.handler import build_real_llm_handler

_FAKE_AZURE_ENV = {
    "AZURE_OPENAI_ENDPOINT": "https://fake.openai.azure.com/",
    "AZURE_OPENAI_API_KEY": "fake-key-not-used",
    "AZURE_OPENAI_DEPLOYMENT_NAME": "fake-deploy",
}


def _set_fake_azure(monkeypatch: pytest.MonkeyPatch) -> None:
    for k, v in _FAKE_AZURE_ENV.items():
        monkeypatch.setenv(k, v)
    # Sprint 57.98 A1: the Cat 10 verifier registry is now injected INTO the loop
    # ctor (pre-57.98 these tests received it in a tuple and discarded it). With
    # verification enabled (the default), the in-loop gate would fire the
    # LLMJudgeVerifier — whose OWN ChatClient is the fake-Azure adapter, NOT the
    # swapped mock — on every FINAL answer, making a real (fake-endpoint) network
    # call + perturbing the mock-response sequence. These tests exercise
    # memory/prompt wiring, NOT verification, so disable it to drive the loop the
    # way they did pre-57.98 (registry discarded → no in-loop verification).
    monkeypatch.setenv("CHAT_VERIFICATION_MODE", "disabled")
    # Clear AFTER setenv so build_real_llm_handler's get_settings() reads the new
    # value (a conftest autouse fixture may re-cache the default after the pre-clear).
    from core.config import get_settings

    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _reset_settings_cache():
    """Clear get_settings lru_cache before+after each test (mirrors the 57.64
    keystone wiring tests; build_real_llm_handler reads Settings)."""
    from core.config import get_settings

    get_settings.cache_clear()  # type: ignore[attr-defined]
    yield
    get_settings.cache_clear()  # type: ignore[attr-defined]


def _final_response(text: str = "done") -> ChatResponse:
    return ChatResponse(
        model="mock",
        content=text,
        stop_reason=StopReason.END_TURN,
        tool_calls=None,
        usage=TokenUsage(prompt_tokens=10, completion_tokens=2, total_tokens=12),
    )


def _tool_call_response(name: str, arguments: dict, call_id: str) -> ChatResponse:
    return ChatResponse(
        model="mock",
        content="",
        stop_reason=StopReason.TOOL_USE,
        tool_calls=[ToolCall(id=call_id, name=name, arguments=arguments)],
        usage=TokenUsage(prompt_tokens=10, completion_tokens=2, total_tokens=12),
    )


def _assembled_prompt_text(mock: MockChatClient) -> str:
    """Flatten the FINAL turn's assembled prompt messages to plain text."""
    assert mock.last_request is not None
    return "\n".join(str(m.content) for m in mock.last_request.messages)


# ============================================================
# Render — a written session memory renders into a later turn's prompt
# ============================================================


@pytest.mark.asyncio
async def test_tier2_memory_renders_into_assembled_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A session memory written on turn 1 is rendered into turn-2's system prompt.

    SessionLayer matches on substring (query in content); we craft the content so
    the auto-inject query (the user message) is a substring of the stored content.
    """
    _set_fake_azure(monkeypatch)
    tenant_id = uuid4()
    user_id = uuid4()
    session_id = uuid4()
    loop = build_real_llm_handler(session_id=session_id, tenant_id=tenant_id, user_id=user_id)

    token = "alpha-secret-token"
    stored = f"the user prefers {token} per their last note"
    mock = MockChatClient(
        responses=[
            _tool_call_response(
                "memory_write",
                {"scope": "session", "key": "k1", "content": stored, "time_scale": "short_term"},
                "call_w",
            ),
            _final_response("done"),
        ]
    )
    loop._chat_client = mock  # type: ignore[attr-defined]

    from agent_harness._contracts import TraceContext

    trace_ctx = TraceContext(tenant_id=tenant_id, user_id=user_id, session_id=session_id)
    # The user input IS the auto-inject query; make it a substring of the stored content.
    events = [
        ev
        async for ev in loop.run(session_id=session_id, user_input=token, trace_context=trace_ctx)
    ]

    # The FINAL turn's assembled prompt carries the rendered memory block.
    prompt_text = _assembled_prompt_text(mock)
    assert stored in prompt_text
    assert "Session Memory" in prompt_text
    assert "confidence" in prompt_text

    # PromptBuilt.memory_layers_used is non-empty on the turn that saw memory.
    prompt_built = [ev for ev in events if isinstance(ev, PromptBuilt)]
    assert any("session" in pb.memory_layers_used for pb in prompt_built)


# ============================================================
# verify_before_use — lead-then-verify rule present when flagged
# ============================================================


@pytest.mark.asyncio
async def test_tier2_verify_before_use_rule_present(monkeypatch: pytest.MonkeyPatch) -> None:
    """A flagged hint (verify_before_use=True) surfaces the lead-then-verify rule.

    We inject a flagged hint directly via the shared MemoryRetrieval so the build
    path renders it (SessionLayer cannot set the flag; the flag is the retrieval's
    contract surface)."""
    from unittest.mock import AsyncMock

    from agent_harness._contracts import MemoryHint, TraceContext

    _set_fake_azure(monkeypatch)
    tenant_id = uuid4()
    session_id = uuid4()
    loop = build_real_llm_handler(session_id=session_id, tenant_id=tenant_id)

    flagged = MemoryHint(
        hint_id=uuid4(),
        layer="user",
        time_scale="long_term",
        summary="LAST-QUARTER-PRICE-99",
        confidence=0.6,
        relevance_score=0.7,
        full_content_pointer="db://memory/x",
        timestamp=datetime.now(timezone.utc),
        verify_before_use=True,
    )
    # The handler shares ONE MemoryRetrieval between tools + prompt builder; patch
    # its search so the prompt build sees the flagged hint.
    builder = loop._prompt_builder  # type: ignore[attr-defined]
    search_mock = AsyncMock(return_value=[flagged])
    builder._memory_retrieval.search = search_mock  # type: ignore[attr-defined]

    mock = MockChatClient(responses=[_final_response("done")])
    loop._chat_client = mock  # type: ignore[attr-defined]

    trace_ctx = TraceContext(tenant_id=tenant_id, session_id=session_id)
    [
        ev
        async for ev in loop.run(
            session_id=session_id, user_input="price?", trace_context=trace_ctx
        )
    ]

    prompt_text = _assembled_prompt_text(mock)
    assert VERIFY_BEFORE_USE_HEADER in prompt_text
    assert "LAST-QUARTER-PRICE-99" in prompt_text


# ============================================================
# Cross-tenant — tenant-B prompt shows none of tenant-A's session memory
# ============================================================


@pytest.mark.asyncio
async def test_tier2_cross_tenant_no_memory_leak(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tenant B's assembled prompt must not contain tenant A's session memory.

    Both runs use the SAME shared layers (built once per handler); isolation comes
    from the per-call ExecutionContext tenant_id, exercised on the live SSE flow.
    """
    from agent_harness._contracts import TraceContext

    _set_fake_azure(monkeypatch)
    session_id = uuid4()
    token = "tenant-a-only-secret"
    stored = f"sensitive {token} stored by tenant A"

    # Tenant A: write a session memory, then echo the token (so it re-renders).
    tenant_a = uuid4()
    loop_a = build_real_llm_handler(session_id=session_id, tenant_id=tenant_a)
    mock_a = MockChatClient(
        responses=[
            _tool_call_response(
                "memory_write",
                {"scope": "session", "key": "k", "content": stored, "time_scale": "short_term"},
                "call_w",
            ),
            _final_response("a done"),
        ]
    )
    loop_a._chat_client = mock_a  # type: ignore[attr-defined]
    ctx_a = TraceContext(tenant_id=tenant_a, session_id=session_id)
    [ev async for ev in loop_a.run(session_id=session_id, user_input=token, trace_context=ctx_a)]
    assert stored in _assembled_prompt_text(mock_a)  # tenant A sees its own

    # Tenant B: SAME session_id, queries the same token — must see nothing.
    tenant_b = uuid4()
    loop_b = build_real_llm_handler(session_id=session_id, tenant_id=tenant_b)
    mock_b = MockChatClient(responses=[_final_response("b done")])
    loop_b._chat_client = mock_b  # type: ignore[attr-defined]
    ctx_b = TraceContext(tenant_id=tenant_b, session_id=session_id)
    [ev async for ev in loop_b.run(session_id=session_id, user_input=token, trace_context=ctx_b)]

    assert stored not in _assembled_prompt_text(mock_b)
    # The tenant-A summary text must be wholly absent from tenant B's prompt.
    assert "stored by tenant A" not in _assembled_prompt_text(mock_b)


# ============================================================
# Negative — empty MemoryRetrieval standalone path renders no memory block
# ============================================================


@pytest.mark.asyncio
async def test_tier2_no_memory_deps_renders_no_block(monkeypatch: pytest.MonkeyPatch) -> None:
    """make_chat_prompt_builder(chat_client) with no retrieval → no memory block,
    run still completes (preserves the 57.64 standalone behaviour)."""
    from adapters._testing.mock_clients import MockChatClient as _MCC
    from agent_harness._contracts import LoopCompleted
    from agent_harness.orchestrator_loop.loop import AgentLoopImpl
    from agent_harness.output_parser import OutputParserImpl
    from api.v1.chat._category_factories import make_chat_prompt_builder
    from business_domain._register_all import make_default_executor

    mock = _MCC(responses=[_final_response("done")])
    registry, executor = make_default_executor()
    # Default (no memory_retrieval) → empty MemoryRetrieval(layers={}).
    prompt_builder = make_chat_prompt_builder(mock)
    loop = AgentLoopImpl(
        chat_client=mock,
        output_parser=OutputParserImpl(),
        tool_executor=executor,
        tool_registry=registry,
        prompt_builder=prompt_builder,
    )

    events = [ev async for ev in loop.run(session_id=uuid4(), user_input="hello")]

    prompt_text = _assembled_prompt_text(mock)
    assert "Memory ===" not in prompt_text  # no "=== <Layer> Memory ===" header
    assert VERIFY_BEFORE_USE_HEADER not in prompt_text
    prompt_built = [ev for ev in events if isinstance(ev, PromptBuilt)]
    assert prompt_built and all(pb.memory_layers_used == () for pb in prompt_built)
    assert any(isinstance(ev, LoopCompleted) for ev in events)


# ============================================================
# A-2 Tier2 — prompt-cache observability on LoopCompleted
# ============================================================


def _final_response_cached(
    text: str = "done", *, prompt_tokens: int = 100, cached_input_tokens: int = 60
) -> ChatResponse:
    """A final response whose usage carries cached_input_tokens (Azure auto-cache
    warm). Neutral TokenUsage field — no provider SDK involved."""
    return ChatResponse(
        model="mock",
        content=text,
        stop_reason=StopReason.END_TURN,
        tool_calls=None,
        usage=TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=10,
            cached_input_tokens=cached_input_tokens,
            total_tokens=prompt_tokens + 10,
        ),
    )


@pytest.mark.asyncio
async def test_tier2_cache_hit_metric_emitted(monkeypatch: pytest.MonkeyPatch) -> None:
    """A run whose usage carries cached_input_tokens>0 → the final LoopCompleted
    reports cached_input_tokens>0 and cache_hit_rate ≈ cached / input."""
    from agent_harness._contracts import LoopCompleted, TraceContext

    _set_fake_azure(monkeypatch)
    tenant_id = uuid4()
    session_id = uuid4()
    loop = build_real_llm_handler(session_id=session_id, tenant_id=tenant_id)

    mock = MockChatClient(
        responses=[_final_response_cached(prompt_tokens=100, cached_input_tokens=60)]
    )
    loop._chat_client = mock  # type: ignore[attr-defined]

    trace_ctx = TraceContext(tenant_id=tenant_id, session_id=session_id)
    events = [
        ev
        async for ev in loop.run(session_id=session_id, user_input="hello", trace_context=trace_ctx)
    ]

    completed = [ev for ev in events if isinstance(ev, LoopCompleted)]
    assert completed, "expected a LoopCompleted event"
    final = completed[-1]
    assert final.cached_input_tokens == 60
    assert final.input_tokens == 100
    assert final.cache_hit_rate == pytest.approx(0.6)


@pytest.mark.asyncio
async def test_tier2_cache_hit_metric_accumulates_across_turns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A 2-turn run sums cached_input_tokens; cache_hit_rate uses the totals
    (turn 1 cold = 0 cached, turn 2 warm = cached>0)."""
    from agent_harness._contracts import LoopCompleted, TraceContext

    _set_fake_azure(monkeypatch)
    tenant_id = uuid4()
    session_id = uuid4()
    loop = build_real_llm_handler(session_id=session_id, tenant_id=tenant_id)

    # Turn 1: a tool call (cold cache, 0 cached); Turn 2: final (warm cache).
    # memory_write is the proven-good tool path (see render test); its cold-cache
    # turn carries 0 cached tokens so the accumulation across turns is exercised.
    cold = ChatResponse(
        model="mock",
        content="",
        stop_reason=StopReason.TOOL_USE,
        tool_calls=[
            ToolCall(
                id="call_w",
                name="memory_write",
                arguments={
                    "scope": "session",
                    "key": "k",
                    "content": "noted",
                    "time_scale": "short_term",
                },
            )
        ],
        usage=TokenUsage(
            prompt_tokens=100, completion_tokens=2, cached_input_tokens=0, total_tokens=102
        ),
    )
    mock = MockChatClient(
        responses=[cold, _final_response_cached(prompt_tokens=100, cached_input_tokens=80)]
    )
    loop._chat_client = mock  # type: ignore[attr-defined]

    trace_ctx = TraceContext(tenant_id=tenant_id, session_id=session_id)
    events = [
        ev
        async for ev in loop.run(session_id=session_id, user_input="hello", trace_context=trace_ctx)
    ]

    final = [ev for ev in events if isinstance(ev, LoopCompleted)][-1]
    # cumulative input = 100 + 100 = 200; cached = 0 + 80 = 80 → 0.4
    assert final.cached_input_tokens == 80
    assert final.input_tokens == 200
    assert final.cache_hit_rate == pytest.approx(0.4)


@pytest.mark.asyncio
async def test_tier2_no_cached_tokens_rate_is_zero_no_crash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A run with cached_input_tokens=0 (default) → cache_hit_rate==0.0
    (div-by-0 guarded) and the run completes."""
    from agent_harness._contracts import LoopCompleted, TraceContext

    _set_fake_azure(monkeypatch)
    tenant_id = uuid4()
    session_id = uuid4()
    loop = build_real_llm_handler(session_id=session_id, tenant_id=tenant_id)

    mock = MockChatClient(responses=[_final_response("done")])
    loop._chat_client = mock  # type: ignore[attr-defined]

    trace_ctx = TraceContext(tenant_id=tenant_id, session_id=session_id)
    events = [
        ev
        async for ev in loop.run(session_id=session_id, user_input="hello", trace_context=trace_ctx)
    ]

    final = [ev for ev in events if isinstance(ev, LoopCompleted)][-1]
    assert final.cached_input_tokens == 0
    assert final.cache_hit_rate == 0.0


# ============================================================
# Combined — A-1 render + A-2 cache metric co-exist in ONE chat SSE run (Day 3)
# ============================================================


@pytest.mark.asyncio
async def test_tier2_memory_render_and_cache_metric_one_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """One run exercises BOTH Tier2 capabilities together (they must not interfere):

    - A-1: a session memory written on turn 1 renders into turn-2's system prompt.
    - A-2: turn-2's cached usage flows into LoopCompleted.cache_hit_rate.

    Turn 1 (memory_write) is a cold-cache tool turn (0 cached); turn 2 is the warm
    final response. cumulative input = 100 + 100 = 200; cached = 0 + 80 = 80 → 0.4.
    """
    from agent_harness._contracts import LoopCompleted, TraceContext

    _set_fake_azure(monkeypatch)
    tenant_id = uuid4()
    user_id = uuid4()
    session_id = uuid4()
    loop = build_real_llm_handler(session_id=session_id, tenant_id=tenant_id, user_id=user_id)

    token = "combined-tier2-token"
    stored = f"the user prefers {token} per their last note"
    cold_write = ChatResponse(
        model="mock",
        content="",
        stop_reason=StopReason.TOOL_USE,
        tool_calls=[
            ToolCall(
                id="call_w",
                name="memory_write",
                arguments={
                    "scope": "session",
                    "key": "k1",
                    "content": stored,
                    "time_scale": "short_term",
                },
            )
        ],
        usage=TokenUsage(
            prompt_tokens=100, completion_tokens=2, cached_input_tokens=0, total_tokens=102
        ),
    )
    mock = MockChatClient(
        responses=[cold_write, _final_response_cached(prompt_tokens=100, cached_input_tokens=80)]
    )
    loop._chat_client = mock  # type: ignore[attr-defined]

    trace_ctx = TraceContext(tenant_id=tenant_id, user_id=user_id, session_id=session_id)
    events = [
        ev
        async for ev in loop.run(session_id=session_id, user_input=token, trace_context=trace_ctx)
    ]

    # A-1: memory rendered into the final turn's assembled prompt.
    prompt_text = _assembled_prompt_text(mock)
    assert stored in prompt_text
    prompt_built = [ev for ev in events if isinstance(ev, PromptBuilt)]
    assert any("session" in pb.memory_layers_used for pb in prompt_built)

    # A-2: cache metric on LoopCompleted reflects the warm turn.
    final = [ev for ev in events if isinstance(ev, LoopCompleted)][-1]
    assert final.cached_input_tokens == 80
    assert final.input_tokens == 200
    assert final.cache_hit_rate == pytest.approx(0.4)
