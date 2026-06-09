# CHANGE-061: Cat 11 FORK runs a real child agent loop (地基 A payoff)

**Change Date**: 2026-06-09
**Change Type**: New Feature (Cat 11 Subagent Orchestration)
**Sprint**: 57.94
**Scope**: 範疇 11 (Subagent) + composition wiring (`api/v1/chat/handler.py`) + Cat 12 (child LOOP span)
**Status**: ✅ Completed (drive-through PASS)

## Change Summary

Make Category 11 **FORK** run a **real child `AgentLoop`** (multi-turn, tool-capable) instead of the single-shot `ChatClient.chat()` call that had stood in for it since Sprint 54.2. This cashes in the 地基 A investment (57.88-93): the child reuses the parent's re-enterable `run()`/`_run_turns` (extracted Sprint 57.89) with **ZERO `loop.py` change** — a child is just a fresh `AgentLoopImpl` instance with its own session_id, a role-derived system prompt, the tenant, and a recursion-safe tool subset.

## Change Reason

Cat 11 was the last範疇 whose "Level 4" was a Potemkin in spirit: every mode (FORK / TEAMMATE / AS_TOOL) ran a single-shot, tool-less, memory-less `chat()` — a degenerate loop of length 1 (`modes/fork.py`'s own docstring admitted it: "runs a single ChatClient call rather than a full child AgentLoop … Phase 55+ may extend to multi-turn child loops with tools"). A subagent that cannot use tools or iterate is not autonomous (vision principles 4/10). 地基 A built the durable pause-resume + re-enterable loop lifecycle specifically to feed this.

## Detailed Changes

- **`ChildLoopFactory` type** (`agent_harness/_contracts/subagent.py`): `Callable[[SubagentBudget], "AgentLoop"]` (TYPE_CHECKING-only `AgentLoop` import → no runtime Cat 11 → Cat 1 cycle). Each call returns a fresh child loop; the budget caps the child's `token_budget`.
- **`ForkExecutor`** (`subagent/modes/fork.py`): dropped `chat_client`; gained `child_loop_factory`. `execute()` builds a fresh child via the factory, drives `child.run(user_input=task)` under `asyncio.wait_for(budget.max_duration_s)`, and **drains** the `LoopEvent` stream into a `SubagentResult` (last `LLMResponded.content` → summary; `LoopCompleted.total_tokens` → tokens). Fail-closed (never raises): `None` factory → `child_loop_factory_unavailable`; timeout → `timeout`; empty → `empty_response`; any child error → `child_loop_error`.
- **`DefaultSubagentDispatcher`** (`subagent/dispatcher.py`): threads `child_loop_factory` → `ForkExecutor`. AS_TOOL shares the SAME `ForkExecutor`, so it inherits the real loop for free. TEAMMATE (single-shot) keeps `chat_client`.
- **Composition** (`api/v1/chat/handler.py` + `_category_factories.py`): when `session_id` is present, builds a recursion-safe child tool pair via `make_default_executor(subagent_dispatcher=None)` (omits `task_spawn` + the `agent_researcher` AS_TOOL → a child cannot itself spawn → depth bounded at 1) + the `_make_child_loop` factory closure (captures chat_client / parser / child registry+executor / tenant_id / tracer; `CHILD_SUBAGENT_SYSTEM_PROMPT` + `CHILD_SUBAGENT_MAX_TURNS=4`) + injects it via `make_chat_subagent_dispatcher`.
- **No single-shot fallback** (US-5, no AP-10 divergence): `None` factory fails closed; existing single-shot FORK/AS_TOOL tests **converted** (Never-Delete) to a mock-LLM child-loop factory (`tests/.../subagent/_child_loop_helpers.py`).

## Modified Files List

| File | Change |
|------|--------|
| `backend/src/agent_harness/_contracts/subagent.py` + `_contracts/__init__.py` | NEW `ChildLoopFactory` type + re-export |
| `backend/src/agent_harness/subagent/modes/fork.py` | ForkExecutor real child-loop drive + drain |
| `backend/src/agent_harness/subagent/dispatcher.py` | thread `child_loop_factory` |
| `backend/src/api/v1/chat/_category_factories.py` | `make_chat_subagent_dispatcher(child_loop_factory=)` |
| `backend/src/api/v1/chat/handler.py` | safe-subset child pair + factory closure + inject |
| `backend/tests/unit/agent_harness/subagent/_child_loop_helpers.py` (NEW) + `test_fork.py` / `test_as_tool.py` / `test_subagent_tools.py` / `test_subagent_sse_emission.py` (converted) + `test_subagent_child_loop.py` (NEW) | mock-LLM child-loop factory + real-loop assertions |
| `backend/tests/integration/api/test_chat_keystone_wiring.py` | `_redirect_subagent_chat` → swap `child_loop_factory` |
| `docs/.../20-subagent-child-loop-design.md` (NEW) | spike design note (8-pt gate) |
| `docs/.../17-cross-category-interfaces.md` | Cat 11 `ChildLoopFactory` composition note |

**`loop.py` is UNCHANGED** (the child reuses `run()`/`_run_turns`). No DB / migration / `LoopEvent` contract change.

## Test Verification

- mypy `src --strict` **0/351** · full backend pytest **2271 passed** (baseline 2266 → +5) · run_all **10/10** (AP-1 does not flag the `async for ev in child.run()` drive; LLM SDK leak 0; cross-category-import OK) · black/isort/flake8 (src+tests) clean.
- NEW `test_subagent_child_loop.py`: multi-turn+tool (a 2-step tool→answer script proves a real loop — a single-shot would `empty_response` on the turn-1 tool-call) / recursion-safe subset (child registry excludes `task_spawn`/`handoff`) / tenant threaded / child opens `agent_loop.run` LOOP span.
- **Drive-through PASS** (real chat-v2 UI + real backend + real Azure gpt-5.2, dan@acme.com/acme-prod): a `task_spawn` delegation whose child uses `echo_tool` → `{success: true, summary: "child loop is real", tokens_used: 3684}` + a 2389ms `task_spawn` TOOL_EXEC span. The echoed summary + 3684 tokens are **impossible** under the old single-shot (which would `empty_response` on the child's tool-call response) → the child genuinely looped + used a tool. Evidence: `artifacts/sprint-57-94-childloop-{0,1}.png`.

## Impact

- Backend-only. FORK + AS_TOOL now run real child loops; TEAMMATE / HANDOFF unchanged.
- Deferred (separate slices / ADs): TEAMMATE/HANDOFF real loops, `HandoffService`, SSE-relay of child/subagent events (`AD-Subagent-Child-Event-SSE-Relay` — the chat dispatcher has no `event_emitter`, so the Inspector Tree tab shows "no subagents"; the child is headless), child-span nesting (`AD-Subagent-Child-Span-Nesting`), recursion depth > 1, parentUuid transcript chain, child-internal governance, failure policies.
