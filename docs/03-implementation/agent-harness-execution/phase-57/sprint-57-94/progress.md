# Sprint 57.94 Progress — Cat 11 FORK Real Child Agent Loop (地基 A payoff, Slice 1)

**Plan**: `agent-harness-planning/phase-57-frontend-saas/sprint-57-94-plan.md`
**Checklist**: `…/sprint-57-94-checklist.md`
**Branch**: `feature/sprint-57-94-subagent-fork-child-loop` (from `main` `38ebfc43`)

---

## Day 0 — 2026-06-09 — Plan-vs-Repo Verify + Branch

### Three-prong verify (head-start via 2 read-only research passes; anchors in checklist 0.1)

- **Prong 1 (path)** ✅ — confirmed `AgentLoopImpl.__init__` (`loop.py:311-351`, 4 required + Optional rest), `run()`/`_run_turns` re-enterable, `ForkExecutor`/`DefaultSubagentDispatcher` signatures, `make_default_executor(subagent_dispatcher=None)` → safe subset, composition site `build_real_llm_handler` (`handler.py:228-396`) builds BOTH parent loop + dispatcher.
- **Prong 2 (content)** ✅ — `loop.py` needs ZERO change (child = fresh `AgentLoopImpl`, reuses `run()`); composition site has every dep local; safe subset is free; task_spawn handler returns a dict (mapping unchanged); AS_TOOL delegates to the same `ForkExecutor` (inherits the real loop).
- **Prong 2.5 (event/drift)** ✅ — D2: `LoopEvent` base has no `parent_session_id`/`depth` → child events drained internally (NOT relayed to SSE; deferred). D3: child must be its own instance.
- **Prong 3 (schema)** ✅ N/A — no DB/migration/ORM/contract-event change.
- **Baseline** ✅ — `main` `38ebfc43`: pytest **2266 passed, 4 skipped** (106.9s) / mypy 0/351 / (run_all/Vitest pre-existing baselines unchanged this sprint — backend-only).

### Drift findings (Day-0 head-start + Day-1 first edits)

- **D-DAY0-1 (path correction)** — the plan §3.1/§4 referenced `subagent/_contracts/subagent.py`; the real single-source is `agent_harness/_contracts/subagent.py` (re-exported via `_contracts/__init__.py`). `ChildLoopFactory` added there. 0% scope change.
- **D-DAY1-1 (design refinement)** — `ChildLoopFactory = Callable[[SubagentBudget], "AgentLoop"]` (takes the budget so the factory caps the child's `token_budget` per spawn; returns the **`AgentLoop` ABC**, not the concrete `AgentLoopImpl` — cleaner, ABC lives in `orchestrator_loop/_abc.py`). TYPE_CHECKING-only import → no runtime Cat 11 → Cat 1 cycle.
- **D-DAY1-2 (fail-closed over raise)** — plan §3.1 said `None` factory → `SubagentLaunchError`. Changed to **fail-closed `SubagentResult(success=False, error="child_loop_factory_unavailable")`** — `ForkExecutor.execute` MUST never raise (a raise propagates through `wait_for` and crashes the parent turn; `wait_for` only catches `TimeoutError`). Consistent with the existing fail-closed contract.
- **D-DAY1-3 (drop chat_client from ForkExecutor)** — the real child loop carries its own `chat_client` via the factory, so `ForkExecutor` no longer needs `chat_client` (removed; Karpathy §3 no dead param). The dispatcher keeps `chat_client` for `TeammateExecutor` (still single-shot).
- **D-DAY1-4 (child span nesting best-effort)** — the `task_spawn` handler calls `dispatcher.spawn(...)` WITHOUT a `trace_context`, so the child loop's `run(trace_context=None)` opens a LOOP span that nests under the parent only if the tracer is contextvar-ambient (the child runs inside the parent's tool-exec span). The child IS traced (its own LOOP→TURN→TOOL_EXEC); explicit parent-ctx threading → deferred `AD-Subagent-Child-Span-Nesting`.

**go/no-go = GO** — feasibility CONDITIONAL-YES realized; `loop.py` untouched; all drifts are refinements (0% scope change).

---

## Day 1 — 2026-06-09 — ChildLoopFactory + ForkExecutor child-loop drive + composition

### Done
- **`_contracts/subagent.py`** — `ChildLoopFactory = Callable[[SubagentBudget], "AgentLoop"]` (TYPE_CHECKING AgentLoop import) + re-export from `_contracts/__init__.py`.
- **`fork.py`** — `ForkExecutor` rewritten: drops `chat_client`, gains `child_loop_factory`; `execute` builds a fresh child loop per spawn, drives `child.run(user_input=task)` under `asyncio.wait_for(budget.max_duration_s)`, drains the `LoopEvent` stream (last `LLMResponded.content` → summary; `LoopCompleted.total_tokens` → tokens), fail-closed on None-factory / timeout / empty / exception. `loop.py` unchanged.
- **`dispatcher.py`** — `DefaultSubagentDispatcher.__init__` gains `child_loop_factory`, passes it to `ForkExecutor`; `chat_client` retained for TEAMMATE.
- **`_category_factories.py`** — `make_chat_subagent_dispatcher(chat_client, *, child_loop_factory=None)`.
- **`handler.py`** — `parser` built early; when `session_id` present, builds the recursion-safe child pair (`make_default_executor(subagent_dispatcher=None)`) + the `_make_child_loop` factory closure (captures chat_client/parser/child_executor/child_registry/tenant_id/tracer; `CHILD_SUBAGENT_SYSTEM_PROMPT` + `CHILD_SUBAGENT_MAX_TURNS=4`) + injects it. AS_TOOL inherits it (same ForkExecutor).

### Gate (Day 1)
- mypy `src --strict` **0/351** ✅
- black 5 files unchanged ✅ / flake8 changed files clean ✅
- subagent unit tests: **12 failed / 38 passed** — the 12 are ALL the FORK path (test_fork / test_as_tool / test_subagent_sse_emission / test_subagent_tools) that constructed `ForkExecutor(chat_client=...)` / expected single-shot. Expected; conversion = Day 2 (Never-Delete → mock-LLM child-loop factory).

---

## Day 2 — 2026-06-09 — Test conversion (Never-Delete) + new child-loop tests

### Done
- **NEW `tests/.../subagent/_child_loop_helpers.py`** — `make_child_loop_factory(chat, *, registry, executor, tenant_id, tracer, max_turns)` (builds a real child `AgentLoopImpl` on a mock LLM — the SAME real-loop path, mock at the ChatClient ABC boundary → no AP-10 divergence) + `RecordingTracer` (NoOpTracer subclass recording span names).
- **Converted (Never-Delete)** — `test_fork.py` (5→6: all use the factory; +`test_fork_no_factory_fails_closed`), `test_as_tool.py` (3 ForkExecutor ctors), `test_subagent_tools.py` (1 dispatcher), `test_subagent_sse_emission.py` (3 dispatchers). No test deleted; single-shot assertions became real-loop assertions.
- **NEW `test_subagent_child_loop.py`** (4) — multi-turn+tool (a 2-step tool→answer script PROVES a real loop: a single-shot would fail with `empty_response` on the turn-1 tool-call response) / recursion-guard (`make_default_executor(subagent_dispatcher=None)` omits `task_spawn`/`handoff`/`agent_researcher`, parent keeps them) / tenant threaded into the child / child opens its own `agent_loop.run` LOOP span.
- **Integration fix** — `test_chat_keystone_wiring.py` `_redirect_subagent_chat` rewired from `dispatcher._fork._chat = client` (removed `_chat` attr) to swapping `dispatcher._fork._child_loop_factory` to a mock-backed child loop (the child consumes exactly 1 scripted response, same as the prior single-shot → shared mock counter stays aligned). 2 previously-failing FORK tests now pass.

### Gate (Day 2)
- subagent unit tests: **55 passed** (was 50; +5 = +4 new child-loop + 1 new fork) ✅
- `test_chat_keystone_wiring.py` **11 passed** ✅ (the 2 FORK integration tests fixed)
- mypy `src --strict` **0/351** ✅ / run_all **10/10** ✅ (AP-1 does NOT flag the `async for ev in child.run()` drive; LLM SDK leak 0; cross-category-import OK — `ChildLoopFactory` AgentLoop import is TYPE_CHECKING-only) / black + isort + flake8 (src + tests) clean ✅
- Full backend pytest: **2271 passed, 4 skipped** (baseline 2266 → +5; the 2 keystone FORK integration tests fixed) ✅. Committed Day 0-2 as `6522cf18` (Day-0 docs `9e435278`).

---

## Day 3 — 2026-06-09 — Drive-through (US-6) + CHANGE-061 + design note

### Clean backend restart (Risk Class E)
- :8000 was owned by the STALE 57.93 backend: uvicorn `--reload` reloader PID 43408 (owns :8000) + its `multiprocessing.spawn` worker child PID 51700 (the Risk-Class-E "cmdline-lacks-uvicorn" worker; parent reloader 46876 already dead). Killed BOTH (Python, not node — frontend node :3007 untouched) → verified :8000 **FREE** (no residual uvicorn).
- Fresh backend via `dev.py start backend` → PID **14580** on :8000 (loads repo-root .env + Azure config); `/health` → 401 = app UP (57.94 code); frontend :3007 PID 6200 (node) untouched.

### Drive-through (real UI chat-v2 + real backend + real Azure gpt-5.2; dan@acme.com admin / acme-prod) — **PASS**

**Request**: "delegate to a sub-agent using task_spawn (mode fork); the sub-task is 'Use the echo_tool to echo the phrase: child loop is real, then report the echoed result'."

| Observed (UI / parent trace) | Intended | ✓ |
|------------------------------|----------|---|
| Parent **turn 2**: `task_spawn` tool call — input `{task: "Use the echo_tool to echo...child loop is real...", mode: fork}` → output `{success: true, summary: "child loop is real", tokens_used: 3684, error: null}` | Parent delegates via task_spawn → child returns a real result | ✅ |
| `summary: "child loop is real"` = the **echoed phrase** (echo_tool output) | The child EXECUTES echo_tool then reports — a real multi-turn tool-using loop | ✅ |
| `tokens_used: 3684` (vs a ~tens-of-tokens single-shot) + `agent_loop.tool.task_spawn` **TOOL_EXEC span = 2389ms** | The child ran a real multi-turn loop (NOT a 1-shot) | ✅ |
| Parent **turn 3**: `end_turn` → "It returned: child loop is real" + Verification passed (0.52) | Parent merges the child summary into its answer | ✅ |

**THE proof it is NOT the old single-shot**: the old `ForkExecutor` made ONE chat call; on a task that requires a tool, the child's first response is a `task_spawn`→`echo_tool` tool-call with `content=""` → the old code returned `empty_response` (success=False). A `success=true` + `summary="child loop is real"` (the echoed phrase) + 3684 tokens is **impossible** under the single-shot → the child genuinely looped + used a tool.

**Honest gap (not a regression)**: the Inspector **Tree** tab shows "no subagents spawned this session" — the chat path's `DefaultSubagentDispatcher` is built WITHOUT an `event_emitter` (pre-existing since 57.12/57.64), so `SubagentSpawned`/`SubagentCompleted` are not relayed to the chat SSE; the child runs **headless** (consistent with the deferred D2 `AD-Subagent-Child-Event-SSE-Relay`). The subagent DID run (proven by the task_spawn result + the 2389ms span). Child LOOP/TURN spans are separate/headless (the parent trace shows only the wrapping `task_spawn` TOOL_EXEC span — child-span nesting is the deferred `AD-Subagent-Child-Span-Nesting`).

- Evidence: `artifacts/sprint-57-94-childloop-{0-initial,1-spawn-and-answer}.png`
- Backend log: dev.py does not persist backend stdout to a readable file (grep returned nothing); the UI trace + tool result are the authoritative evidence.

### Gate (Day 3) — parent re-verified
- pytest **2271** / mypy 0/351 / run_all 10/10 / black+isort+flake8 (src+tests) clean / **drive-through PASS** (real loop, not 1-shot).
