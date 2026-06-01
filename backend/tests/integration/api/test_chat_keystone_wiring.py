"""
File: backend/tests/integration/api/test_chat_keystone_wiring.py
Purpose: Integration tests proving Sprint 57.64 chat-path keystone wiring —
    build_real_llm_handler injects the Cat 5 PromptBuilder into AgentLoopImpl,
    so the production chat flow takes the structured build() path (emits
    PromptBuilt) instead of the naked fallback.
Category: Tests / integration / api
Scope: Phase 57 / Sprint 57.64 Day 1 + Day 2

Description:
    Day 1 — Cat 5 keystone: build_real_llm_handler injects the PromptBuilder so the
    chat flow takes the structured build() path (emits PromptBuilt).

    Day 2 — Cat 3 memory tools + Cat 11 subagent tools: make_default_executor now
    registers (via opt-in deps) the REAL memory_search / memory_write handlers and
    the FORK/TEAMMATE/AS_TOOL subagent tools on the chat executor.

    All deterministic and Azure-call-free: monkeypatch fake AZURE_OPENAI_* env so
    build_real_llm_handler constructs an AzureOpenAIAdapter config object (no
    network), then swap loop._chat_client for a MockChatClient before run() so
    the SSE flow is driven by a scripted response.

    Cat 5 (Day 1):
    - Injection completeness (AP-4 Potemkin guard): the handler-built loop carries
      a non-None _prompt_builder.
    - Positive runtime: running the wired loop on the chat SSE flow emits exactly
      one PromptBuilt event (the loop.py:881 true-branch is reached).
    - Negative guard: an otherwise-identical loop built WITHOUT prompt_builder
      emits NO PromptBuilt.

    Cat 3 (Day 2):
    - Registration is the REAL handler (NOT memory_placeholder_handler; AP-4).
    - memory_write + memory_search emit ToolCallExecuted on the chat SSE path
      (using the in-memory session scope so no live DB is needed).
    - Cross-tenant isolation: a tenant-B search does not see a tenant-A write.
    - Negative: with no memory deps the registry routes to the placeholder.

    Cat 11 (Day 2):
    - A FORK task_spawn emits ToolCallExecuted + the merged SubagentResult summary.
    - Subagent failure (mock raises) does NOT crash the parent loop (fail_soft).
    - Negative: with no dispatcher, task_spawn is unregistered.

    Combined (Day 3):
    - All three active in ONE chat SSE run: PromptBuilt (Cat 5) + a memory_write→
      memory_search round-trip (Cat 3) + a FORK task_spawn merge (Cat 11), proving
      build_real_llm_handler wires them simultaneously (not just in isolation) and
      that memory scoping round-trips on the live SSE flow with all three active.

Created: 2026-06-01 (Sprint 57.64 Day 1)
Last Modified: 2026-06-01 (Sprint 57.64 Day 3 — combined all-three-active test)
"""

from __future__ import annotations

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
from agent_harness.orchestrator_loop.loop import AgentLoopImpl
from api.v1.chat.handler import build_real_llm_handler

_FAKE_AZURE_ENV = {
    "AZURE_OPENAI_ENDPOINT": "https://fake.openai.azure.com/",
    "AZURE_OPENAI_API_KEY": "fake-key-not-used",
    "AZURE_OPENAI_DEPLOYMENT_NAME": "fake-deploy",
}


def _set_fake_azure(monkeypatch: pytest.MonkeyPatch) -> None:
    for k, v in _FAKE_AZURE_ENV.items():
        monkeypatch.setenv(k, v)


@pytest.fixture(autouse=True)
def _reset_settings_cache():
    """Clear get_settings lru_cache before+after each test (mirrors the
    conftest module-level singleton-reset pattern used by the 57.63 wiring
    tests; build_real_llm_handler reads Settings)."""
    from core.config import get_settings

    get_settings.cache_clear()  # type: ignore[attr-defined]
    yield
    get_settings.cache_clear()  # type: ignore[attr-defined]


def _final_response(text: str = "done") -> ChatResponse:
    """A single END_TURN response (no tool calls) — one-turn chat flow."""
    return ChatResponse(
        model="mock",
        content=text,
        stop_reason=StopReason.END_TURN,
        tool_calls=None,
        usage=TokenUsage(prompt_tokens=10, completion_tokens=2, total_tokens=12),
    )


# ============================================================
# Cat 5 keystone — injection completeness + runtime + negative guard
# ============================================================


def test_cat5_real_handler_injects_prompt_builder(monkeypatch: pytest.MonkeyPatch) -> None:
    """AP-4 Potemkin guard: the handler-built loop carries a PromptBuilder."""
    _set_fake_azure(monkeypatch)
    loop, _registry = build_real_llm_handler()
    # Cat 5 keystone: prompt_builder present → loop.py:881 true-branch is live.
    assert loop._prompt_builder is not None  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_cat5_chat_path_emits_prompt_built(monkeypatch: pytest.MonkeyPatch) -> None:
    """Running the wired chat loop emits a PromptBuilt event (fallback NOT taken).

    Swap the (config-only) Azure adapter for a MockChatClient so the SSE flow is
    scripted and offline; the prompt_builder injected by the handler is what
    drives the PromptBuilt emission.
    """
    _set_fake_azure(monkeypatch)
    loop, _registry = build_real_llm_handler()
    loop._chat_client = MockChatClient(responses=[_final_response()])  # type: ignore[attr-defined]

    events = [ev async for ev in loop.run(session_id=uuid4(), user_input="hello")]
    prompt_built = [ev for ev in events if isinstance(ev, PromptBuilt)]

    assert len(prompt_built) == 1
    assert prompt_built[0].messages_count >= 1


@pytest.mark.asyncio
async def test_cat5_no_prompt_built_when_builder_absent() -> None:
    """Negative guard: an AgentLoopImpl built WITHOUT prompt_builder emits no
    PromptBuilt — confirming the event in the positive test is caused by the
    Cat 5 injection (this is the pre-57.64 fallback behaviour)."""
    from agent_harness.output_parser import OutputParserImpl
    from business_domain._register_all import make_default_executor

    registry, executor = make_default_executor()
    loop = AgentLoopImpl(
        chat_client=MockChatClient(responses=[_final_response()]),
        output_parser=OutputParserImpl(),
        tool_executor=executor,
        tool_registry=registry,
        # prompt_builder deliberately omitted → fallback path.
    )

    events = [ev async for ev in loop.run(session_id=uuid4(), user_input="hello")]
    prompt_built = [ev for ev in events if isinstance(ev, PromptBuilt)]

    assert prompt_built == []


# ============================================================
# Cat 3 memory tools — registration + runtime + cross-tenant + negative guard
# ============================================================


def _tool_call_response(name: str, arguments: dict, call_id: str) -> ChatResponse:
    """A TOOL_USE response invoking a single tool."""
    return ChatResponse(
        model="mock",
        content="",
        stop_reason=StopReason.TOOL_USE,
        tool_calls=[ToolCall(id=call_id, name=name, arguments=arguments)],
        usage=TokenUsage(prompt_tokens=10, completion_tokens=2, total_tokens=12),
    )


def test_cat3_real_handler_registered_not_placeholder() -> None:
    """AP-4 Potemkin guard: the memory deps wire the REAL handlers, not the stub."""
    from agent_harness.tools.memory_tools import memory_placeholder_handler
    from api.v1.chat._category_factories import make_chat_memory_deps
    from business_domain._register_all import make_default_executor

    retrieval, layers = make_chat_memory_deps(db=None)
    registry, executor = make_default_executor(
        memory_retrieval=retrieval,
        memory_layers=layers,
    )
    handlers = executor._handlers  # type: ignore[attr-defined]
    assert "memory_search" in handlers
    assert "memory_write" in handlers
    # The real factory-built handlers are closures, NOT the module-level stub.
    assert handlers["memory_search"] is not memory_placeholder_handler
    assert handlers["memory_write"] is not memory_placeholder_handler


@pytest.mark.asyncio
async def test_cat3_chat_path_memory_tools_execute(monkeypatch: pytest.MonkeyPatch) -> None:
    """memory_write then memory_search emit ToolCallExecuted on the chat SSE path.

    Uses the in-memory session scope (SessionLayer) so the test needs no live DB.
    The loop builds ExecutionContext from the TraceContext (tenant + user +
    session), which the real memory handlers consume for scoping.
    """
    from agent_harness._contracts import TraceContext
    from agent_harness._contracts.events import ToolCallExecuted

    _set_fake_azure(monkeypatch)
    tenant_id = uuid4()
    user_id = uuid4()
    session_id = uuid4()
    loop, _registry = build_real_llm_handler(session_id=session_id, tenant_id=tenant_id)

    # Scripted: write a session memory, then search it, then END_TURN.
    loop._chat_client = MockChatClient(  # type: ignore[attr-defined]
        responses=[
            _tool_call_response(
                "memory_write",
                {
                    "scope": "session",
                    "key": "k1",
                    "content": "blue widget",
                    "time_scale": "short_term",
                },
                "call_w",
            ),
            _tool_call_response(
                "memory_search",
                {"query": "blue", "scopes": ["session"], "time_scales": ["short_term"]},
                "call_s",
            ),
            _final_response(),
        ]
    )

    trace_ctx = TraceContext(tenant_id=tenant_id, user_id=user_id, session_id=session_id)
    events = [
        ev
        async for ev in loop.run(
            session_id=session_id, user_input="remember this", trace_context=trace_ctx
        )
    ]
    executed = [ev for ev in events if isinstance(ev, ToolCallExecuted)]
    names = {ev.tool_name for ev in executed}
    assert "memory_write" in names
    assert "memory_search" in names


@pytest.mark.asyncio
async def test_cat3_cross_tenant_isolation(monkeypatch: pytest.MonkeyPatch) -> None:
    """A tenant-B memory_search must not see a tenant-A session write.

    Both runs share ONE registry/executor (built once) — proving the isolation
    is enforced per-call by the ExecutionContext (TraceContext.tenant_id), not by
    constructing separate layer instances per tenant.
    """
    import json

    from agent_harness._contracts import ExecutionContext, ToolCall
    from api.v1.chat._category_factories import make_chat_memory_deps
    from business_domain._register_all import make_default_executor

    _set_fake_azure(monkeypatch)
    retrieval, layers = make_chat_memory_deps(db=None)
    _registry, executor = make_default_executor(
        memory_retrieval=retrieval,
        memory_layers=layers,
    )

    tenant_a = uuid4()
    tenant_b = uuid4()
    session = uuid4()

    # Tenant A writes a session memory.
    write_ctx = ExecutionContext(tenant_id=tenant_a, session_id=session)
    write_call = ToolCall(
        id="w",
        name="memory_write",
        arguments={
            "scope": "session",
            "key": "k",
            "content": "tenant A secret",
            "time_scale": "short_term",
        },
    )
    write_res = await executor.execute(write_call, context=write_ctx)
    assert write_res.success is True

    # Tenant A can find it.
    search_call = ToolCall(
        id="s",
        name="memory_search",
        arguments={"query": "secret", "scopes": ["session"], "time_scales": ["short_term"]},
    )
    res_a = await executor.execute(
        search_call, context=ExecutionContext(tenant_id=tenant_a, session_id=session)
    )
    hints_a = json.loads(res_a.content)["hints"]
    assert any("tenant A secret" in h["summary"] for h in hints_a)

    # Tenant B (same session_id) sees nothing — composite (tenant_id, session_id) key.
    res_b = await executor.execute(
        search_call, context=ExecutionContext(tenant_id=tenant_b, session_id=session)
    )
    hints_b = json.loads(res_b.content)["hints"]
    assert hints_b == []


@pytest.mark.asyncio
async def test_cat3_negative_no_deps_memory_unregistered() -> None:
    """With no memory deps, make_default_executor does NOT register memory tools.

    (The no-deps path registers only echo + 18 business tools — register_builtin_tools
    is not called, so memory_search / memory_write are absent from the registry. The
    agent still runs; a call to memory_search resolves to "unknown tool".) This is the
    AP-4 negative guard: memory is present ONLY when the real deps are wired.
    """
    from agent_harness._contracts import ToolCall
    from business_domain._register_all import make_default_executor

    registry, executor = make_default_executor()  # no memory deps
    assert registry.get("memory_search") is None
    assert registry.get("memory_write") is None
    res = await executor.execute(ToolCall(id="s", name="memory_search", arguments={"query": "x"}))
    assert res.success is False
    assert "unknown tool" in (res.error or "")


# ============================================================
# Cat 11 subagent tools (A-3a) — runtime + fail_soft + negative guard
# ============================================================


@pytest.mark.asyncio
async def test_cat11_chat_path_fork_spawn_and_merge(monkeypatch: pytest.MonkeyPatch) -> None:
    """A FORK task_spawn emits ToolCallExecuted + merges the SubagentResult summary.

    The subagent dispatcher shares the loop's ChatClient; we swap in a MockChatClient
    whose responses serve BOTH the parent turns and the subagent's single-shot call.
    """
    import json

    from agent_harness._contracts import TraceContext
    from agent_harness._contracts.events import ToolCallExecuted

    _set_fake_azure(monkeypatch)
    session_id = uuid4()
    tenant_id = uuid4()
    loop, _registry = build_real_llm_handler(session_id=session_id, tenant_id=tenant_id)

    # Parent: turn 1 = task_spawn(FORK); subagent consumes one response;
    # parent turn 2 = END_TURN. MockChatClient is shared (loop + subagent dispatcher),
    # but the dispatcher was built with the Azure adapter at handler time — so we
    # swap the loop's client AND rebuild the dispatcher's fork executor client by
    # pointing the loop client only; the subagent FORK uses the SAME mock via the
    # dispatcher's shared adapter reference set at construction. To keep the test
    # deterministic we give enough scripted responses for both consumers.
    mock = MockChatClient(
        responses=[
            _tool_call_response("task_spawn", {"task": "research X", "mode": "fork"}, "call_t"),
            ChatResponse(
                model="mock",
                content="subagent findings",
                stop_reason=StopReason.END_TURN,
                usage=TokenUsage(prompt_tokens=5, completion_tokens=3, total_tokens=8),
            ),
            _final_response("parent done"),
        ]
    )
    loop._chat_client = mock  # type: ignore[attr-defined]
    # Point the subagent dispatcher's fork executor at the same mock (it was built
    # with the Azure adapter; redirect so the FORK call is offline). Assert the
    # redirect succeeded (closure-walk found the dispatcher) so the merge below
    # reflects the scripted subagent response, not a fallback failure.
    redirected = _redirect_subagent_chat(loop, mock)
    assert redirected is True

    trace_ctx = TraceContext(tenant_id=tenant_id, session_id=session_id)
    events = [
        ev
        async for ev in loop.run(
            session_id=session_id, user_input="delegate", trace_context=trace_ctx
        )
    ]
    executed = [ev for ev in events if isinstance(ev, ToolCallExecuted)]
    spawn = [ev for ev in executed if ev.tool_name == "task_spawn"]
    assert len(spawn) == 1
    # The merged SubagentResult summary flows back through the tool result content.
    merged = json.loads(spawn[0].result_content)
    assert merged["success"] is True
    assert "subagent findings" in merged["summary"]


@pytest.mark.asyncio
async def test_cat11_fork_failure_does_not_crash_parent(monkeypatch: pytest.MonkeyPatch) -> None:
    """A subagent FORK failure surfaces as a soft tool error; the parent reaches END_TURN."""
    from agent_harness._contracts import LoopCompleted, TraceContext

    _set_fake_azure(monkeypatch)
    session_id = uuid4()
    tenant_id = uuid4()
    loop, _registry = build_real_llm_handler(session_id=session_id, tenant_id=tenant_id)

    mock = MockChatClient(
        responses=[
            _tool_call_response("task_spawn", {"task": "boom", "mode": "fork"}, "call_t"),
            _final_response("parent recovered"),
        ]
    )
    loop._chat_client = mock  # type: ignore[attr-defined]
    # Subagent's ForkExecutor uses a client that raises → SubagentResult(success=False).
    _redirect_subagent_chat(loop, _RaisingChatClient())

    trace_ctx = TraceContext(tenant_id=tenant_id, session_id=session_id)
    events = [
        ev
        async for ev in loop.run(
            session_id=session_id, user_input="delegate", trace_context=trace_ctx
        )
    ]
    # Parent loop still terminates normally despite the subagent failure.
    assert any(isinstance(ev, LoopCompleted) for ev in events)


def test_cat11_negative_no_dispatcher_unregistered() -> None:
    """With no subagent dispatcher, task_spawn is not registered."""
    from business_domain._register_all import make_default_executor

    registry, _executor = make_default_executor()  # no dispatcher
    assert registry.get("task_spawn") is None


# ============================================================
# Combined — Cat 5 + Cat 3 + Cat 11 all active in ONE chat SSE run (Day 3)
# ============================================================


@pytest.mark.asyncio
async def test_combined_all_three_active_one_run(monkeypatch: pytest.MonkeyPatch) -> None:
    """One chat SSE run exercises all three keystone capabilities together.

    build_real_llm_handler wires Cat 5 (prompt_builder) + Cat 3 (memory deps) +
    Cat 11 (subagent dispatcher) simultaneously. A single scripted run proves they
    co-exist on the live SSE flow — not just in the isolated per-cat tests:

    - Cat 5: a PromptBuilt event is emitted (structured build path, not fallback).
    - Cat 3: memory_write then memory_search both ToolCallExecuted, AND the search
      finds the just-written session memory (per-tenant round-trip on the live path).
    - Cat 11: a FORK task_spawn ToolCallExecuted with a merged SubagentResult.

    The MockChatClient is shared by parent + subagent fork (sequential counter), so
    the scripted responses are ordered: parent t1 (write) → parent t2 (spawn) →
    subagent single-shot → parent t3 (search) → parent t4 (END_TURN).
    """
    import json

    from agent_harness._contracts import TraceContext
    from agent_harness._contracts.events import ToolCallExecuted

    _set_fake_azure(monkeypatch)
    tenant_id = uuid4()
    user_id = uuid4()
    session_id = uuid4()
    loop, _registry = build_real_llm_handler(session_id=session_id, tenant_id=tenant_id)

    mock = MockChatClient(
        responses=[
            _tool_call_response(
                "memory_write",
                {
                    "scope": "session",
                    "key": "k1",
                    "content": "combined-run secret",
                    "time_scale": "short_term",
                },
                "call_w",
            ),
            _tool_call_response("task_spawn", {"task": "research", "mode": "fork"}, "call_t"),
            ChatResponse(
                model="mock",
                content="subagent findings",
                stop_reason=StopReason.END_TURN,
                usage=TokenUsage(prompt_tokens=5, completion_tokens=3, total_tokens=8),
            ),
            _tool_call_response(
                "memory_search",
                {"query": "combined-run", "scopes": ["session"], "time_scales": ["short_term"]},
                "call_s",
            ),
            _final_response("all done"),
        ]
    )
    loop._chat_client = mock  # type: ignore[attr-defined]
    # Point the subagent FORK executor at the same mock (offline determinism).
    assert _redirect_subagent_chat(loop, mock) is True

    trace_ctx = TraceContext(tenant_id=tenant_id, user_id=user_id, session_id=session_id)
    events = [
        ev
        async for ev in loop.run(
            session_id=session_id, user_input="do everything", trace_context=trace_ctx
        )
    ]

    # Cat 5 — structured build path reached.
    assert sum(1 for ev in events if isinstance(ev, PromptBuilt)) >= 1

    executed = [ev for ev in events if isinstance(ev, ToolCallExecuted)]
    names = {ev.tool_name for ev in executed}
    # Cat 3 + Cat 11 — all three tool kinds fired in this one run.
    assert {"memory_write", "memory_search", "task_spawn"} <= names

    # Cat 3 — the search round-trips the memory written earlier in the SAME run.
    search_ev = next(ev for ev in executed if ev.tool_name == "memory_search")
    hints = json.loads(search_ev.result_content)["hints"]
    assert any("combined-run secret" in h["summary"] for h in hints)

    # Cat 11 — the subagent summary merged back through the tool result.
    spawn_ev = next(ev for ev in executed if ev.tool_name == "task_spawn")
    merged = json.loads(spawn_ev.result_content)
    assert merged["success"] is True
    assert "subagent findings" in merged["summary"]


# ---- Cat 11 test helpers ----


class _RaisingChatClient(MockChatClient):
    """A ChatClient whose chat() always raises — drives the FORK fail-closed path."""

    async def chat(  # type: ignore[override]
        self, request, *, cache_breakpoints=None, trace_context=None
    ):
        raise RuntimeError("simulated subagent failure")


def _redirect_subagent_chat(loop: AgentLoopImpl, client: MockChatClient) -> bool:
    """Point the registered task_spawn dispatcher's ForkExecutor at `client`.

    The handler built the dispatcher with the Azure adapter; to keep the test
    offline we reach into the FORK executor (the only thing task_spawn invokes for
    mode='fork') and swap its ChatClient. This mirrors the loop._chat_client swap
    the other tests use and keeps the assertion about the SSE flow, not the
    provider. Returns True when the dispatcher was found + redirected.
    """
    # The dispatcher is captured in the task_spawn handler closure; the simplest
    # deterministic redirect is via the dispatcher instance the handler closed
    # over. The executor's registered handler is the adapter closure, so we walk
    # its closure cells to recover the dispatcher.
    handlers = loop._tool_executor._handlers  # type: ignore[attr-defined]
    adapted = handlers.get("task_spawn")
    if adapted is None:
        return False
    dispatcher = _extract_dispatcher_from_closure(adapted)
    if dispatcher is None:
        return False
    dispatcher._fork._chat = client  # type: ignore[attr-defined]
    dispatcher._as_tool_wrapper._fork._chat = client  # type: ignore[attr-defined]
    return True


def _extract_dispatcher_from_closure(adapted) -> object | None:  # type: ignore[no-untyped-def]
    """Walk the adapter closure → the (dict)->dict subagent handler → its dispatcher."""
    for cell in getattr(adapted, "__closure__", None) or ():
        inner = cell.cell_contents
        for inner_cell in getattr(inner, "__closure__", None) or ():
            cand = inner_cell.cell_contents
            if cand.__class__.__name__ == "DefaultSubagentDispatcher":
                return cand
    return None
