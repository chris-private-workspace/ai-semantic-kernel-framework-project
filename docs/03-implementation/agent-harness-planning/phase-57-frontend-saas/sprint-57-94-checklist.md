# Sprint 57.94 — Checklist (Cat 11 FORK Real Child Agent Loop — 地基 A payoff, Slice 1)

**Plan**: [`sprint-57-94-plan.md`](./sprint-57-94-plan.md)
**Created**: 2026-06-09
**Status**: Draft (code gated on Day-0 GO)

> Rule: only `[ ]` → `[x]`; never delete unchecked items; defer with `🚧 + reason`.
> CHANGE (new-domain spike — first real child loop) → CHANGE-061 + Day-4 design note `20-subagent-child-loop-design.md` (8-pt gate). Gate = full backend pytest green (NET delta documented) + **drive-through PASS** (the child genuinely loops multi-turn + calls a tool, verified against a nested backend trace — the assertion that it is NOT a 1-shot). Locked scope: FORK (+ AS_TOOL which reuses ForkExecutor); TEAMMATE / HANDOFF real loops + SSE-relay of child events + recursion depth > 1 deferred.

---

## Day 0 — Plan-vs-Repo Verify + Branch

### 0.1 Three-prong Day-0 verify
- [x] **Prong 1 (path)**: confirmed (2 read-only探查 passes) — `AgentLoopImpl.__init__` `loop.py:311-351` (4 required deps + Optional rest) / `run()` `:1521` (opens LOOP span `:1563`) / `_run_turns` `:1621` (reads `self._tool_registry`/`_tool_executor`/`_max_turns`/`_tenant_id` → child needs own instance, D3) / `ForkExecutor` `fork.py:58` ctor + `:62` execute + single-shot to replace `:73-81` / `DefaultSubagentDispatcher.__init__` `dispatcher.py:102` (`chat_client`+`mailbox`+`event_emitter`) + `spawn`→fork `:192` + `wait_for` `:249` / `make_default_executor` `_register_all.py:219` (subset via `subagent_dispatcher=None` omits `task_spawn`+`agent_researcher` `:262-279`) / `task_spawn` handler `subagent/tools.py:93-123` (returns dict) / `SubagentResult` `_contracts/subagent.py:59-71` / `AgentSpec` `_abc.py:74` / `Tracer.start_span` `observability/_abc.py:32` / `SubagentSpawned`/`Completed` `events.py:348-359` / `ToolRegistryImpl` `registry.py:51`. Composition: parent loop `handler.py:378-396` + dispatcher `:287` in the SAME `build_real_llm_handler` `:228`. (progress.md Day-0 Prong 1)
- [x] **Prong 2 (content)**: confirmed — (a) **`loop.py` needs ZERO change**: `run()`/`_run_turns` re-enterable since 57.89; child = fresh `AgentLoopImpl`; child span nests via `start_span(trace_context=parent_ctx)`; (b) **composition site has every dep** (`chat_client`/`registry`/`executor`/`parser`/`compactor`/`prompt_builder`/`reducer`/`tracer`/`tenant_id` all local in `build_real_llm_handler`); (c) **safe subset is free** — `make_default_executor(subagent_dispatcher=None)` builds the registry+executor pair minus `task_spawn`/`handoff` (D1: specs in registry, handlers in executor → must build as a pair, which this call does); (d) **task_spawn handler returns a dict** `{subagent_id,success,summary,tokens_used,error}` → child loop still yields `SubagentResult` → mapping unchanged (D4); (e) AS_TOOL (`as_tool.py`) delegates to the SAME `ForkExecutor` → inherits the real loop. (progress.md Day-0 Prong 2)
- [x] **Prong 2.5 (event / drift)**: confirmed — **D2**: `LoopEvent` base (`events.py:56`) has NO `parent_session_id`/`depth` → child events drained internally (NOT relayed to chat SSE); relaying deferred (`AD-Subagent-Child-Event-SSE-Relay`). **D3**: child MUST be own `AgentLoopImpl` (system_prompt/registry from `self`) — design correct. The dispatcher emits only Spawned/Completed today; the child runs headless. (progress.md Day-0 Prong 2.5)
- [x] **Prong 3 (schema)**: N/A — no DB/migration/ORM change; no `LoopEvent` contract change (child events drained, not relayed); `SubagentResult` shape unchanged.
- [x] **Baseline capture**: baseline = `main` HEAD `38ebfc43` (57.93 merged) — capture pytest / mypy 0/351 / run_all 10/10 / Vitest before editing
- [x] **Child tool-set decision**: child registry = `make_default_executor(subagent_dispatcher=None)` → enumerate the resulting tools (expect echo / memory_search / memory_write / python_sandbox / web_search / request_approval minus spawn/AS_TOOL); confirm Day-1 the exact set + that `task_spawn`/`handoff` are absent (recursion guard)
- [x] Catalogue any Day-1 drift in progress.md; **go/no-go = GO** pending baseline capture (feasibility CONDITIONAL-YES; loop.py untouched; factory buildable at composition; safe subset free; one drift D2 resolved by deferring SSE-relay — 0% scope change)

### 0.2 Branch
- [x] Branch `feature/sprint-57-94-subagent-fork-child-loop` from `main` (`38ebfc43`)
- [x] plan + checklist + progress committed (Day-0 commit)

---

## Day 1 — `ChildLoopFactory` type + ForkExecutor child-loop drive + drain (US-1/US-3/US-5)

### 1.1 `ChildLoopFactory` type + threading (US-1/US-5)
- [x] **`subagent/_contracts/subagent.py`** — add `ChildLoopFactory = Callable[[AgentSpec], "AgentLoopImpl"]` (`TYPE_CHECKING` import of `AgentLoopImpl`; no runtime Cat 11 → Cat 1 import); file-header MHist
- [x] **`DefaultSubagentDispatcher.__init__`** (`dispatcher.py`) — gains `child_loop_factory: ChildLoopFactory | None = None`; passes to `ForkExecutor`
- [x] **`ForkExecutor.__init__`** (`fork.py`) — gains `child_loop_factory: ChildLoopFactory | None = None`
- [x] **No import cycle** — grep `subagent/` has no runtime `from ...orchestrator_loop import`; mypy clean on the alias

### 1.2 ForkExecutor real child-loop drive + event-drain → SubagentResult (US-1/US-3)
- [x] **Replace single-shot** (`fork.py:73-81`) — `if factory is None: raise SubagentLaunchError`; `child = factory(AgentSpec(role/prompt derived))`; `child.run(session_id=uuid4(), user_input=task, trace_context=parent_ctx)`
- [x] **Drain loop** — `async for ev in child.run(...)`: track last `LLMResponded.content` (final answer) + accumulate tokens (`LoopCompleted`/per-turn — confirm cumulative vs per-turn Day-1); under `asyncio.wait_for(budget.max_duration_s)`
- [x] **Build `SubagentResult`** — `summary = truncate(final_answer, 500)`, `tokens_used`, `duration_ms` (monotonic helper, not wall clock), `success=True`
- [x] **Fail-closed** — `TimeoutError` → `SubagentResult(success=False, error="timeout")`; other exc → `success=False, error=str(e)`; never raise out of `execute`
- [x] **mypy clean** on `fork.py` + `dispatcher.py`

### 1.3 Composition: safe-subset child pair + factory closure (US-2/US-4)
- [x] **Safe-subset pair** (`handler.py`) — `child_registry, child_executor = make_default_executor(subagent_dispatcher=None, <same db/session locals as parent>)`; confirm `task_spawn`/`handoff` absent
- [x] **Factory closure** — `child_loop_factory = lambda spec: AgentLoopImpl(chat_client=chat_client, output_parser=parser, tool_executor=child_executor, tool_registry=child_registry, system_prompt=spec.prompt or DEFAULT_CHILD_SYSTEM_PROMPT, tenant_id=tenant_id, tracer=tracer, max_turns=CHILD_MAX_TURNS, token_budget=...)`
- [x] **Inject** — pass `child_loop_factory` into the subagent dispatcher construction (`handler.py:287` / `_category_factories.py` if helper'd there); MHist 1-line
- [x] **AS_TOOL shares it** — confirm the dispatcher owns ONE `ForkExecutor` so AS_TOOL inherits the factory
- [x] **tenant + span** — child `_tenant_id` == parent tenant; child LOOP span nests under parent via `trace_context=parent_ctx` (confirm `ForkExecutor`'s `trace_context` is the parent loop ctx)

---

## Day 2 — Tests (convert + new) (US-1..US-5)

### 2.1 Convert existing single-shot tests (Never-Delete) (US-5)
- [x] **`test_fork.py`** — inject a mock-LLM `child_loop_factory` (MockChatClient scripted: tool_call turn → final answer); assert real multi-turn loop + `SubagentResult.summary` = child final answer; the 5 existing cases become real-loop assertions (none deleted)
- [x] **`test_as_tool.py`** — AS_TOOL drives the real child loop via the same ForkExecutor; update assertions
- [x] **`test_dispatcher_init.py`** (if present) — dispatcher accepts + forwards `child_loop_factory`

### 2.2 New child-loop unit tests (US-1..US-5)
- [x] **`test_subagent_child_loop.py` — multi-turn + tool** — MockChatClient: turn 1 → tool_call, turn 2 → final answer; assert the tool executed + summary = final answer (real loop, not 1-shot)
- [x] **safe-subset excludes spawn** — the child's available tools (`child.run` registry) do NOT include `task_spawn`/`handoff` (recursion guard); assert
- [x] **tenant threaded** — child loop `_tenant_id` == parent tenant
- [x] **fail-closed** — child raises/timeouts → `SubagentResult(success=False, error=...)`, no exception out of `execute`
- [x] **None factory raises** — `ForkExecutor(child_loop_factory=None).execute(...)` → `SubagentLaunchError` (no single-shot fallback)
- [x] **nested LOOP span** — fake tracer asserts a child LOOP span opened under the parent ctx
- [x] **TEAMMATE / HANDOFF tests UNCHANGED** — `test_teammate.py` / `test_handoff.py` pass without edit (those modes untouched)

---

## Day 3 — Full regression + drive-through (US-6) + CHANGE-061

### 3.1 Full gate sweep
- [x] **Full backend pytest green (NET delta documented)** — baseline → +N (converted FORK/AS_TOOL + ~6 new child-loop); NO test deleted
- [x] **mypy 0 + run_all 10/10 + format chain** — mypy `src --strict` 0; run_all 10/10 (LLM SDK leak 0; AP-1 — confirm the `async for ev in child.run()` drive is not flagged as a pipeline, mirror 57.90 delegation-awareness if needed; AP-8; AP-10 no mock/real divergence); `black`/`isort` clean; `flake8 src tests` clean (CI-equivalent scope — the 57.92 lesson)

### 3.2 Drive-through (US-6 — the child genuinely loops + uses a tool) — **PASS pending**
- [x] **Clean backend restart (Risk Class E)** — kill stale uvicorn reloader+worker procs on :8000; verify :8000 OWNER is the fresh PID (`dev.py start backend`); `/health`; PG/Redis/RabbitMQ healthy; frontend node untouched; Azure gpt-5.2 live
- [x] **Drove a `task_spawn` child through real UI + real backend + real Azure** — a chat-v2 request that makes the agent spawn a sub-task requiring a tool → confirm: (1) `SubagentSpawned` → (2) the child loops multi-turn + calls a tool → (3) `SubagentCompleted` with a REAL summary → (4) parent's answer incorporates it. **Trace proof**: backend trace shows a nested child LOOP → TURN → TOOL_EXEC span under the parent (NOT a single chat call). Observed-vs-intended table in progress.md Day 3
  - Evidence: `artifacts/sprint-57-94-childloop-{1-spawn,2-child-trace,3-parent-answer}.png`
- [x] **Frontend gap** — note whether the UI surfaces `SubagentSpawned`/`SubagentCompleted`; if the parent answer incorporates the real child summary, the drive-through holds via the answer + the backend trace even if the UI does not stream child turns (SSE-relay deferred, documented)

### 3.3 CHANGE-061 + design-note extract (spike)
- [x] `claudedocs/4-changes/feature-changes/CHANGE-061-subagent-fork-child-loop.md` written
- [x] **`20-subagent-child-loop-design.md`** extracted (8-pt gate: section-header↔US / file:line per claim / decision matrix (child-loop-factory vs override-_run_turns vs single-shot-fallback) / verification command / test fixture / verified-vs-deferred split / rollback path / 17.md cross-ref)
- [x] `17-cross-category-interfaces.md` — Cat 11 contract: dispatcher optionally carries a `ChildLoopFactory` (composition detail; `SubagentDispatcher` ABC unchanged); MHist 57.94 line

---

## Day 4 — Closeout

### 4.1 Closeout
- [x] Full validation (parent re-verified): pytest +N / mypy 0 / run_all 10/10 / TEAMMATE+HANDOFF tests unchanged / **drive-through PASS** (screenshots + observed-vs-intended + nested-trace evidence)
- [x] progress.md (Day 0-3) + retrospective.md (Q1-Q7) + **design-note 8-pt gate self-check record** (spike)
- [x] Calibration: `subagent-child-loop-spike` 0.60 (1st data point, pending validation) + `agent_factor` 1.0 (parent-direct); record `calibration-log.md §3` + propose in `sprint-workflow.md §Scope-class matrix`; carryover (TEAMMATE/HANDOFF real loops / SSE-relay / recursion depth>1 / transcript chain / child governance / failure policies) → next-phase-candidates.md
- [x] MEMORY.md pointer + `project_phase57_94_subagent_fork_child_loop.md` subfile + CLAUDE.md lean (Current Sprint row + Last Updated; Architecture row IF Cat 11 reaches真 Level 4) + CHANGE-061 + `20-subagent-child-loop-design.md` + 17.md Cat 11 note
- [ ] commit (Day 0-N) + push + PR — closeout commit done; **push + PR pending user authorization**
