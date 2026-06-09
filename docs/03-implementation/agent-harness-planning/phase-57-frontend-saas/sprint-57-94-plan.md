# Sprint 57.94 Plan — Cat 11 FORK Real Child Agent Loop (地基 A payoff, Slice 1)

**Purpose**: Category 11 (Subagent Orchestration) is the last範疇 whose "Level 4" is a Potemkin in spirit: every mode (FORK / TEAMMATE / AS_TOOL) runs a **single-shot, tool-less, memory-less `ChatClient.chat()` call** — a degenerate loop of length 1 (`modes/fork.py:73-81`, whose own docstring admits "runs a single ChatClient call rather than a full child AgentLoop … Phase 55+ may extend to multi-turn child loops with tools"). 地基 A (57.88-93) built the durable pause-resume + re-enterable `_run_turns` lifecycle skeleton specifically to feed Cat 11; this sprint cashes that in. It makes the **FORK** mode run a **REAL child `AgentLoopImpl`** — a multi-turn TAO loop that can call tools — instead of the single-shot call. The decisive enabling fact (Day-0 verified): a child reuses the parent's `run()` / `_run_turns` (re-enterable since 57.89) **with ZERO `loop.py` change** — a child is just a fresh `AgentLoopImpl(...)` instance with its own session_id, role-derived system prompt, tenant_id, a **recursion-safe tool subset** (parent tools MINUS `task_spawn`/`handoff`), and its own nested LOOP span; the parent + dispatcher are built in the SAME function (`build_real_llm_handler`, `handler.py:228-396`) so a **child-loop factory** closure can be built there with every dep in local scope. The `ForkExecutor` swaps its single-shot `chat()` for "build a child via the injected factory → drive `child.run()` → drain the child's `LoopEvent` stream into a `SubagentResult`". AS_TOOL inherits the real loop for free (it delegates to `ForkExecutor`); **TEAMMATE / HANDOFF stay as-is** (separate executors / routing primitive — out of scope). Because FORK behavior changes, the existing single-shot FORK / AS_TOOL unit tests are **converted (Never-Delete)** to a mock-LLM-backed child-loop factory asserting real-loop behavior (no divergent single-shot fallback → no AP-10). This is a **NEW-domain spike** (first real child loop) → **record = CHANGE-061** + a Day-4 design-note extract `20-subagent-child-loop-design.md` (8-point quality gate). **Drive-through** (real UI + real backend + real Azure): a chat-v2 request that makes the agent `task_spawn` a sub-task whose child must use a tool → the child genuinely loops multi-turn + calls a tool → its real summary returns to the parent → verified against the backend trace (a nested child LOOP → TURN → TOOL_EXEC span) so it is provably NOT a 1-shot.

**Category / Scope**: Cat 11 (Subagent — `ForkExecutor` real child-loop drive + `LoopEvent`→`SubagentResult` drain; `DefaultSubagentDispatcher` threads the factory; a `ChildLoopFactory` type) + composition wiring (`handler.py` builds the factory closure + the recursion-safe child executor/registry via `make_default_executor(subagent_dispatcher=None)`, injects into the dispatcher) + Cat 12 (the child opens its own nested LOOP span via the threaded tracer + parent trace_context). **`loop.py` UNCHANGED** (child reuses `run()`/`_run_turns` byte-identical — the 57.89 re-entrancy payoff). Phase 57.94

**Created**: 2026-06-09
**Status**: Draft (scope below; code execution gated on Day-0 GO — Day-0 head-start already run, findings in §0)
**Source**: `next-phase-candidates.md` (Sprint 57.88-93 carryover "Subagent child-loop (Cat 11) — consumes the shared re-enterable `_run_turns` + the now-generalized pause machinery; distinct larger sprint; the 地基 A lifecycle 骨架 now feeds it") + `agent-harness-cc-parity-20260607.md` §3 #7 (Subagent 🟡 + "child-loop executor hollow stub") + AskUserQuestion 2026-06-09 (direction = **Subagent child-loop (Cat 11)**; slice = **FORK real child loop + safe tool subset**).

> **Modification History**
> - 2026-06-09: Initial creation — FORK runs a real child AgentLoopImpl (reuses run()/_run_turns, zero loop.py change); child-loop factory built in build_real_llm_handler; recursion-safe subset via make_default_executor(subagent_dispatcher=None); drain child LoopEvents into SubagentResult; AS_TOOL inherits; TEAMMATE/HANDOFF out of scope

---

## 0. Background

地基 A (57.88-93) delivered the durable pause-resume keystone + the **re-enterable** per-turn loop `_run_turns` (extracted 57.89, driven by both `run()` and `resume()` since 57.90) + the generalized `_emit_deferred_pause` pause family (tool / input / between-turns / output). Its stated purpose in every carryover was to feed Cat 11: a real child loop needs a loop body that can be driven from a second entry point. That now exists. This sprint builds the **first real child agent loop** on top of it.

Cat 11 today (Day-0 mapped): `DefaultSubagentDispatcher` (`subagent/dispatcher.py`) routes FORK → `ForkExecutor.execute` (`subagent/modes/fork.py`), which makes ONE `ChatClient.chat()` call — no tools, no parent context, no multi-turn TAO, no compaction/checkpoint/guardrail/verification. It is a real LLM call but a degenerate loop of length 1. HANDOFF only `return uuid4()` (no execution; the loop-side terminator `stop_reason="handoff"` is wired but no `HandoffService` boots the child). TEAMMATE = single-shot + a best-effort mailbox send no loop consumes. The 4 modes are "Level 4" on paper but the child-loop executor is the hollow core.

### Ground truth re-confirmed (Day-0 head-start — this plan's Day-0 verify)

Re-confirmed by two READ-ONLY探查 passes (Cat 11 inventory + a focused factory-wiring verify) with file:line anchors:

- **`loop.py` needs ZERO change.** A child is a fresh `AgentLoopImpl(...)`. `AgentLoopImpl.__init__` (`loop.py:311-351`, keyword-only) requires only `chat_client`, `output_parser`, `tool_executor`, `tool_registry`; everything else is Optional (`system_prompt=""`, `max_turns=50`, `token_budget=100_000`, `tracer=None`, `compactor/prompt_builder/reducer/checkpointer/tenant_id`=None, Cat-8/9 deps, `hitl_*`). `run()` (`loop.py:1521`, `(*, session_id, user_input, trace_context=None)`) prepends `self._system_prompt`, opens the LOOP span (`:1563` `self._tracer.start_span(name="agent_loop.run", category=ORCHESTRATOR, trace_context=ctx, attributes={"span_type":"LOOP"})`), runs `_cat9_input_check`, delegates to `_run_turns`. `_run_turns` reads `self._max_turns`, `self._tool_registry.list()`, `self._tool_executor.execute(...)`, `self._tenant_id` — all from `self` → a child MUST be its own instance (D3); it CANNOT be done by overriding `_run_turns` per-call. Passing the parent's `tracer` + parent `trace_context` makes the child LOOP span **nest** under the parent automatically. **No new method, no signature change in `loop.py`.**
- **The composition site has every dep (THE crux).** `build_real_llm_handler` (`handler.py:228-396`) builds BOTH the parent `AgentLoopImpl` (`:378-396`) and the `subagent_dispatcher` (`:287`) in one function. Locals in scope: `chat_client` (`:280`), `registry`+`executor` (`:290`, from `make_default_executor`), `parser` (`:297`), `compactor` (`:309`), `prompt_builder` (`:320`), `reducer`+`checkpointer` (`:321`), `guardrail_engine` (`:341`), `tracer`, `tenant_id`, `system_prompt`, `hitl_manager`. → a `child_loop_factory` closure can be built here capturing exactly what a child needs.
- **The recursion-safe subset is FREE.** `make_default_executor(...)` (`business_domain/_register_all.py:219`) builds the `(ToolRegistryImpl, ToolExecutorImpl)` pair in lockstep; calling it **without `subagent_dispatcher`** omits `task_spawn` + the `agent_researcher` AS_TOOL (`:262-279`) — i.e. exactly the FORK-safe subset (parent tools minus the spawn/handoff tools). D1: the registry holds only `ToolSpec`s and handlers live in the executor, so a subset MUST be built as a fresh pair — `make_default_executor(subagent_dispatcher=None)` does precisely that. **The child cannot spawn → depth is bounded at 1 → no depth field / depth enforcement needed this slice.**
- **`ForkExecutor` is the single swap point.** `ForkExecutor.__init__` (`fork.py:58`, `(*, chat_client, enforcer=None)`) + `execute(*, subagent_id, task, budget, trace_context=None) -> SubagentResult` (`:62`). The single-shot lines to replace = `:73-81` (`ChatRequest(messages=[Message(role="user", content=task)])` + `asyncio.wait_for(self._chat.chat(...))`). `DefaultSubagentDispatcher.__init__` (`dispatcher.py:102`, `(*, chat_client, mailbox=None, event_emitter=None)`) → thread the factory through to `ForkExecutor`. AS_TOOL (`modes/as_tool.py`) delegates to the SAME `ForkExecutor` → inherits the real loop for free.
- **`SubagentResult` + handler mapping unchanged.** `SubagentResult` (`_contracts/subagent.py:59-71`): `subagent_id, mode, success, summary, full_artifact_pointer, tokens_used, duration_ms, error, metadata`. `wait_for` (`dispatcher.py:249`) awaits the in-flight task. The `task_spawn` handler (`subagent/tools.py:93-123`) returns a dict summary `{subagent_id, success, summary, tokens_used, error}` to the LLM — the child loop still yields a `SubagentResult`, so the handler mapping is byte-identical.
- **Child events drained, NOT relayed (this slice).** `LoopEvent` base (`events.py:56`) has only `event_id, timestamp, trace_context` — no `parent_session_id`/`depth` (D2). The dispatcher emits only `SubagentSpawned`/`SubagentCompleted` (`dispatcher.py:183, 236`). The child's `run()` yields a full `LoopEvent` stream; the `ForkExecutor` **drains it internally** (extract the final answer → `summary`, sum tokens) and does NOT relay child events onto the chat SSE. Relaying child events (so the UI shows the child looping) needs a `LoopEvent` contract addition → **deferred** (the child runs headless; `SubagentSpawned`/`SubagentCompleted` surface as today, now carrying a REAL multi-turn summary).
- **The drive-through assertion that proves it is not a 1-shot.** The child's REAL summary reflects multi-turn tool use, and the backend trace shows a **nested child LOOP → TURN → TOOL_EXEC span** under the parent — the verification that the child genuinely looped + called a tool (vs the old single `chat()`).

---

## 1. Sprint Goal

Make Cat 11 **FORK** run a real child agent loop: (1) add a `ChildLoopFactory` type (`Callable[[AgentSpec], AgentLoopImpl]`) + thread it `build_real_llm_handler` → `DefaultSubagentDispatcher` → `ForkExecutor`; (2) build the factory closure in `build_real_llm_handler` capturing the in-scope deps + a **recursion-safe** child registry/executor via `make_default_executor(subagent_dispatcher=None)` (no `task_spawn`/`handoff` → child cannot spawn → bounded depth) + `tenant_id` + `tracer`; (3) replace `ForkExecutor`'s single-shot `chat()` (`fork.py:73-81`) with: build a child `AgentLoopImpl` (role-derived `system_prompt`, child `session_id=uuid4()`, child registry/executor, `max_turns` small, `token_budget=budget.max_tokens`) → drive `child.run(session_id, user_input=task, trace_context=parent_ctx)` under `asyncio.wait_for(budget.max_duration_s)` → **drain** the `LoopEvent` stream into a `SubagentResult` (final answer → `summary`, sum tokens, `success`/`error`, `duration_ms`); (4) the child opens its own nested LOOP span (Cat 12) for free via the threaded tracer + parent ctx. **`loop.py` is UNCHANGED.** AS_TOOL inherits the real loop (same `ForkExecutor`); TEAMMATE / HANDOFF unchanged. The existing single-shot FORK / AS_TOOL unit tests are **converted** to a mock-LLM-backed child-loop factory (no single-shot fallback — avoid AP-10); NEW child-loop unit tests (real multi-turn + tool call + recursion-safe-subset-excludes-spawn + tenant threading + fail-closed) + a **drive-through** (chat-v2 `task_spawn` → real multi-turn tool-using child → real summary → nested trace verified). Out of scope: TEAMMATE / HANDOFF real loops (separate); a `HandoffService`; SSE-relay of child events (needs a `LoopEvent` contract field); parentUuid transcript chain; recursion depth > 1 (child cannot spawn this slice); failure policies (FAIL_FAST/SOFT/PARTIAL); child checkpoint persistence.

---

## 2. User Stories

- **US-1 (FORK runs a real child loop)** — As the platform, I want a FORK subagent to be a real multi-turn TAO loop that can call tools, not a single `chat()` call, so a subagent is genuinely autonomous + action-capable (vision principles 4/10). → `ForkExecutor` builds a child `AgentLoopImpl` via the injected `ChildLoopFactory` and drives `child.run(...)` instead of `self._chat.chat(...)`.
- **US-2 (recursion-safe tool subset)** — As the platform, I want the child to be able to call tools but NOT to be able to spawn further subagents, so depth is bounded and the demo cannot recurse. → the child registry/executor are built by `make_default_executor(subagent_dispatcher=None)` (omits `task_spawn` + `agent_researcher` AS_TOOL); the child gets the safe subset; no depth field/enforcement needed (a child that cannot spawn is depth-bounded at 1).
- **US-3 (child result is real, mapping unchanged)** — As the calling LLM, I want the subagent's summary to reflect what the child actually did (multi-turn + tool use), with the same `task_spawn` return shape. → `ForkExecutor` drains the child `LoopEvent` stream into a `SubagentResult` (final answer → `summary`, tokens summed, `success`/`error`/`duration_ms`); `wait_for` + the `task_spawn` handler's `{subagent_id,success,summary,tokens_used,error}` dict mapping are byte-identical.
- **US-4 (tenant + observability)** — As the enterprise platform, I want the child loop to run under the parent's tenant and appear in the trace as a nested loop. → `tenant_id` is threaded into the child `AgentLoopImpl`; the child opens its own LOOP span (Cat 12) nested under the parent via the threaded `tracer` + parent `trace_context`. (SSE-relay of child events deferred — `SubagentSpawned`/`SubagentCompleted` surface as today.)
- **US-5 (loop.py untouched / no divergent path)** — As the loop maintainer, I want the child to reuse `run()`/`_run_turns` byte-identical (the 57.89 re-entrancy payoff) and NO single-shot fallback path, so there is one real loop path (no AP-10 Mock-vs-Real divergence). → `loop.py` diff = 0 lines; `ForkExecutor` requires a `ChildLoopFactory` (no single-shot fallback); the existing single-shot FORK/AS_TOOL tests are CONVERTED to a mock-LLM child-loop factory.
- **US-6 (drive-through acceptance — provably not a 1-shot)** — As the user, I want a subagent spawned from chat to genuinely loop + use a tool, verified end-to-end. → drive-through: a chat-v2 request makes the agent `task_spawn` a sub-task whose child must use a tool → the child loops multi-turn + calls a tool → its real summary returns to the parent's answer → the backend trace shows a **nested child LOOP → TURN → TOOL_EXEC span**; screenshot + observed-vs-intended diff + trace evidence in progress.md.

---

## 3. Technical Specifications

### 3.0 Architecture (FORK: single-shot → real child loop; loop.py untouched)

```
BEFORE (degenerate loop of length 1)            AFTER (real child AgentLoopImpl)
  ForkExecutor.execute(task, budget):             ForkExecutor.execute(task, budget):
    req = ChatRequest([user: task])                 child = self._child_loop_factory(AgentSpec(role, task))
    resp = await chat(req)        # 1 shot          #   = fresh AgentLoopImpl(chat_client, parser,
    summary = truncate(resp.content)                #       child_executor, child_registry [safe subset],
    return SubagentResult(summary)                  #       system_prompt=role, tenant_id, tracer,
                                                     #       max_turns=small, token_budget=budget.max_tokens)
                                                     events = child.run(session_id=uuid4(),
                                                                        user_input=task,
                                                                        trace_context=parent_ctx)
                                                     async for ev in wait_for(events, budget.max_duration_s):
                                                        # drain: track final answer + tokens; NOT relayed to SSE
                                                     return SubagentResult(summary=final_answer, tokens, ...)

child.run() == parent run()  (UNCHANGED; opens its OWN nested LOOP span via self._tracer; multi-turn _run_turns; tools)

composition (build_real_llm_handler — ONE function, all deps local):
  child_registry, child_executor = make_default_executor(subagent_dispatcher=None)   # safe subset (no task_spawn/handoff)
  child_loop_factory = lambda spec: AgentLoopImpl(chat_client, parser, child_executor, child_registry,
                                                  system_prompt=spec.prompt or DEFAULT, tenant_id=tenant_id,
                                                  tracer=tracer, max_turns=CHILD_MAX_TURNS)
  dispatcher = make_chat_subagent_dispatcher(chat_client, ..., child_loop_factory=child_loop_factory)
```

The child reuses the entire parent loop machinery (TAO, tools, output parsing, guardrails if wired) by being a real `AgentLoopImpl`. The ONLY new code is in `subagent/` (the drive + drain) + the factory closure in `handler.py`. `loop.py` is byte-identical.

### 3.1 `ChildLoopFactory` type + threading (US-1/US-5)
- New type alias in `subagent/_contracts/subagent.py`: `ChildLoopFactory = Callable[[AgentSpec], "AgentLoopImpl"]` (forward-ref / `TYPE_CHECKING` import of `AgentLoopImpl` to avoid a Cat 11 → Cat 1 runtime import cycle; the factory is supplied at composition, so Cat 11 only needs the type for annotation). Confirm Day-1 there is no import cycle (Cat 1 does not import Cat 11 at module load).
- `DefaultSubagentDispatcher.__init__` gains `child_loop_factory: ChildLoopFactory | None = None` (Optional so non-chat constructions / older tests still build; but the chat path always supplies it). It passes it to `ForkExecutor(chat_client=..., enforcer=..., child_loop_factory=...)`.
- `ForkExecutor.__init__` gains `child_loop_factory: ChildLoopFactory | None = None`. **Decision (US-5, no AP-10):** if `child_loop_factory is None`, `execute` raises `SubagentLaunchError("FORK requires a child_loop_factory")` (fail-closed) — there is NO single-shot fallback. The existing single-shot tests are converted to supply a (mock-LLM) factory. (Alternative considered: keep the single-shot as a fallback when no factory — REJECTED: two code paths = AP-10 Mock-vs-Real divergence + the single-shot is the very Potemkin this sprint removes.)

### 3.2 Recursion-safe child registry/executor (US-2)
- The factory closure builds the child tool pair ONCE (not per-spawn): `child_registry, child_executor = make_default_executor(subagent_dispatcher=None, ...)` — passing `subagent_dispatcher=None` omits `task_spawn` + the `agent_researcher` AS_TOOL (`_register_all.py:262-279`), yielding the FORK-safe subset (echo / memory_search / memory_write / python_sandbox / web_search / request_approval — whatever the default minus spawn). Day-1: confirm `make_default_executor`'s signature accepts `subagent_dispatcher=None` cleanly + enumerate the resulting child tool set; if `make_default_executor` requires other args (db/session), pass the same locals the parent executor got.
- Because the child registry has no `task_spawn`, a child **cannot** spawn → recursion is structurally impossible this slice → no `max_subagent_depth` threading / no depth field on events needed. (Depth enforcement is a separate future concern when nested spawning is allowed.)

### 3.3 `ForkExecutor` real child-loop drive + event drain → `SubagentResult` (US-1/US-3)
- Replace `fork.py:73-81` (the single-shot) with:
  - `if self._child_loop_factory is None: raise SubagentLaunchError(...)` (US-5).
  - `child = self._child_loop_factory(AgentSpec(role=<derived>, prompt=<derived>, model=None, metadata={}))` — the spec carries the child's role/system-prompt. (Day-1: a FORK task may not carry a distinct role; default `system_prompt` = a generic "You are a focused sub-task worker. Complete the task and report a concise result." The factory uses `spec.prompt or DEFAULT_CHILD_SYSTEM_PROMPT`.)
  - `child_session_id = uuid4()`.
  - Drive + drain under the budget:
    ```python
    final_answer = ""
    tokens_used = 0
    async def _drive() -> None:
        nonlocal final_answer, tokens_used
        async for ev in child.run(session_id=child_session_id, user_input=task, trace_context=trace_context):
            if isinstance(ev, LLMResponded) and ev.content:
                final_answer = ev.content                 # last assistant answer wins
            if isinstance(ev, LoopCompleted):
                tokens_used = (ev.input_tokens or 0) + (ev.output_tokens or 0)  # or accumulate per turn
    await asyncio.wait_for(_drive(), timeout=budget.max_duration_s)
    summary, _ = self._enforcer.truncate_summary(final_answer, cap_words=500)
    return SubagentResult(subagent_id=subagent_id, mode=SubagentMode.FORK, success=True,
                          summary=summary, tokens_used=tokens_used, duration_ms=<elapsed>, error=None)
    ```
  - Token accounting: Day-1 confirm whether `LoopCompleted` carries cumulative tokens or per-turn; if per-turn, accumulate across `LLMResponded`/`LoopCompleted`. Keep it the minimal honest number (the child's total tokens).
  - Fail-closed: wrap in try/except; `asyncio.TimeoutError` → `SubagentResult(success=False, error="timeout", ...)`; any other exception → `success=False, error=str(e)` (mirror the existing fail-closed at `fork.py` today). Never raise out of `execute` for a child-loop failure (the parent LLM gets `success=False` + error and decides).
- `duration_ms`: measure around the drive (the codebase has a monotonic clock helper used elsewhere; reuse it — do NOT use `Date.now()`-style wall clock if a helper exists; Day-1 confirm the existing timing approach in `fork.py`/dispatcher).
- AS_TOOL: no change to `as_tool.py` — it delegates to the same `ForkExecutor`, so it inherits the real loop. Day-1: confirm the AS_TOOL path constructs/receives the factory-bearing `ForkExecutor` (it should, since the dispatcher owns the single `ForkExecutor`).

### 3.4 What is explicitly NOT done (separate sprints / ADs)
- **TEAMMATE real loop** — `teammate.py` stays single-shot + mailbox send; a mailbox-consuming multi-turn teammate is a separate slice.
- **HANDOFF consumer / `HandoffService`** — the loop-side `stop_reason="handoff"` terminator stays; no service boots the child session. Separate slice.
- **SSE-relay of child events** — the child runs headless (events drained, not relayed); the UI shows `SubagentSpawned`/`SubagentCompleted` (now with a real summary) but not the child's turn-by-turn stream. Relaying needs a `LoopEvent` `parent_session_id`/`depth` contract field → deferred (`AD-Subagent-Child-Event-SSE-Relay`).
- **Recursion depth > 1** — the child has no `task_spawn` (cannot spawn), so depth is bounded at 1; nested spawning + `max_subagent_depth` enforcement is a future concern.
- **parentUuid transcript chain / child checkpoint persistence** — the child is ephemeral (no checkpointer); CC's `agent-{id}.jsonl` + parentUuid chain analog is deferred (`AD-Subagent-Transcript-Isolation`).
- **Failure policies (FAIL_FAST/SOFT/PARTIAL)** — `SubagentBudget` has no `failure_policy`; deferred.
- **Verification / guardrails inside the child** — the child gets the safe tool subset but (this slice) NO guardrail_engine/verifier wired (lean child); whether a child should run its own Cat 9/10 is a deliberate future decision (`AD-Subagent-Child-Governance`).

### 3.5 tenant + Cat 12 span threading (US-4)
- `tenant_id`: the factory closure captures `tenant_id` from `build_real_llm_handler` scope → `AgentLoopImpl(tenant_id=tenant_id)` → the child's `_run_turns` reads `self._tenant_id` (`loop.py:1708/1813`). No dispatcher tenant param needed (the factory carries it).
- Cat 12 span: the factory passes `tracer=tracer`; `ForkExecutor` passes `trace_context=<parent ctx>` into `child.run(trace_context=...)`; `run()` opens `start_span(name="agent_loop.run", ..., trace_context=parent_ctx)` → the child LOOP span **nests** under the parent (the tracer's context-manager threads parent→child). No new span code — the child reuses `run()`'s existing span. Day-1: confirm the `trace_context` available in `ForkExecutor.execute` (its `trace_context` param) is the parent's loop ctx (so nesting is correct); if the dispatcher only has the request ctx, thread the parent loop ctx through `spawn(... trace_context=...)` (already a param everywhere per the inventory).

### 3.6 Lint / neutrality / doc single-source
- `check_llm_sdk_leak` 0 (no adapter/SDK touched; the child uses the same `ChatClient` ABC). `check_ap1_pipeline_disguise` green (the child is a real `while True` `_run_turns`, the opposite of a pipeline — if the AP-1 detector flags `ForkExecutor` driving a loop via `async for`, confirm it recognizes loop-driving like it did for `resume()` in 57.90). AP-8 PromptBuilder green (untouched; the child reuses the parent's prompt_builder only if the factory passes it — this slice may omit it for a lean child; Day-1 decide). `category-boundaries`: the `ChildLoopFactory` type lives in Cat 11 `_contracts/`; the `AgentLoopImpl` import is `TYPE_CHECKING`-only (no Cat 11 → Cat 1 runtime import). AP-10 (Mock vs Real): no divergent single-shot path (US-5) — the mock-LLM child loop tests the SAME path as production (real child loop, mock LLM). **17.md**: add the `ChildLoopFactory` composition note to the Cat 11 contract section (the dispatcher now optionally carries a child-loop factory; `SubagentDispatcher` ABC unchanged — the factory is a composition detail, not an ABC method). CHANGE-061 records it. **Design note** `20-subagent-child-loop-design.md` extracted Day 4 (8-pt gate) — the new-domain spike record.

### 3.7 Validation (US-1..US-6)
- **mypy `src/ --strict` 0**; `run_all` 10/10; `black`/`isort`/`flake8 src/ tests/` clean (CI-equivalent scope, NOT a path subset — the 57.92 lesson).
- **pytest**:
  - **Converted (Never-Delete)**: the existing single-shot `test_fork.py` (5 tests) + `test_as_tool.py` are updated to inject a mock-LLM-backed `child_loop_factory` and assert real-loop behavior (the child runs ≥1 turn against a `MockChatClient` scripted to call a tool then answer; the `SubagentResult.summary` reflects the child's final answer). No test deleted; the single-shot assertions become real-loop assertions.
  - **NEW** `test_subagent_child_loop.py`: (a) FORK child runs MULTI-TURN + calls a tool (MockChatClient scripted: turn 1 → tool_call, turn 2 → final answer; assert the tool was executed + the summary = the final answer); (b) the child registry is the SAFE SUBSET — `task_spawn`/`handoff` are NOT in `child.run`'s available tools (assert the child cannot spawn); (c) `tenant_id` threaded — the child loop's `_tenant_id` == parent tenant; (d) fail-closed — child raises/timeouts → `SubagentResult(success=False, error=...)`, no exception out of `execute`; (e) `child_loop_factory is None` → `SubagentLaunchError` (no single-shot fallback); (f) the child opens a nested LOOP span (assert a child span under the parent ctx via a fake tracer).
  - `test_teammate.py` / `test_handoff.py` UNCHANGED (those modes untouched).
  - Full backend suite green (NET delta documented — expect a small net change: converted FORK/AS_TOOL tests + ~6 new child-loop tests).
- **Drive-through** (US-6): real UI + real backend + real Azure — a chat-v2 request that makes the agent `task_spawn` a sub-task requiring a tool (e.g. "spawn a sub-agent to look up X and report back", where X needs `web_search`/`memory_search`) → confirm via the backend trace a **nested child LOOP → TURN → TOOL_EXEC span** + the child's real summary in the parent's answer; screenshot + observed-vs-intended diff + the trace evidence in progress.md. (Per CLAUDE.md §Drive-Through Acceptance — the "child genuinely looped + used a tool, not a 1-shot" is the leg-specific assertion that distinguishes this from the old Potemkin.)

---

## 4. File Change List

| File | Change |
|------|--------|
| `backend/src/agent_harness/subagent/_contracts/subagent.py` | **EDIT** — add `ChildLoopFactory = Callable[[AgentSpec], "AgentLoopImpl"]` type alias (`TYPE_CHECKING` import of `AgentLoopImpl`; no runtime Cat 1 import). MHist 1-line. |
| `backend/src/agent_harness/subagent/modes/fork.py` | **EDIT** — `ForkExecutor.__init__` gains `child_loop_factory`; `execute` replaces the single-shot `chat()` (`:73-81`) with build-child → `child.run()` → drain `LoopEvent` stream → `SubagentResult` (fail-closed); `None` factory → `SubagentLaunchError`. File-header MHist. |
| `backend/src/agent_harness/subagent/dispatcher.py` | **EDIT** — `DefaultSubagentDispatcher.__init__` gains `child_loop_factory`; passes it to `ForkExecutor`. MHist 1-line. |
| `backend/src/api/v1/chat/handler.py` | **EDIT** — build the recursion-safe child pair `make_default_executor(subagent_dispatcher=None)` + the `child_loop_factory` closure (captures chat_client/parser/child_executor/child_registry/tracer/tenant_id/max_turns); inject into the subagent dispatcher construction. MHist 1-line. |
| `backend/src/api/v1/chat/_category_factories.py` (if the dispatcher is built/helper'd here) | **EDIT (conditional)** — if `make_chat_subagent_dispatcher` lives here, thread `child_loop_factory` through. (Day-1 confirm the construction site.) |
| `backend/tests/unit/agent_harness/subagent/test_fork.py` | **EDIT (convert)** — inject a mock-LLM `child_loop_factory`; assert real multi-turn loop behavior (no single-shot). No test deleted. |
| `backend/tests/unit/agent_harness/subagent/test_as_tool.py` | **EDIT (convert)** — AS_TOOL now drives the real child loop (via the same ForkExecutor); update assertions. |
| `backend/tests/unit/agent_harness/subagent/test_subagent_child_loop.py` | **NEW** — multi-turn+tool / safe-subset-excludes-spawn / tenant-threaded / fail-closed / None-factory-raises / nested-LOOP-span (US-1..US-5). |
| `backend/tests/unit/agent_harness/subagent/test_dispatcher_init.py` | **EDIT (if present)** — dispatcher accepts + forwards `child_loop_factory`. |
| `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-94-plan.md` + `-checklist.md` | **NEW** — this plan + checklist |
| `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-94/progress.md` + `retrospective.md` | **NEW** — Day 0-N progress + retro |
| `docs/03-implementation/agent-harness-planning/20-subagent-child-loop-design.md` | **NEW (Day-4 extract)** — the spike design note (8-pt gate): FORK real child-loop architecture, factory-at-composition, recursion-safe subset, drain→SubagentResult, deferred invariants. |
| `claudedocs/4-changes/feature-changes/CHANGE-061-subagent-fork-child-loop.md` | **NEW** — the change record (FORK real child loop + factory + safe subset + drive-through). |
| `docs/03-implementation/agent-harness-planning/17-cross-category-interfaces.md` | **EDIT** — Cat 11 contract section: note the dispatcher optionally carries a `ChildLoopFactory` (composition detail; `SubagentDispatcher` ABC unchanged). |

**`loop.py` is NOT in this list — it is UNCHANGED** (the child reuses `run()`/`_run_turns` byte-identical). No new DB table / no migration / no Azure-adapter change / no `/resume` or ResumeService change / no `LoopEvent` contract change (child events drained, not relayed).

---

## 5. Acceptance Criteria

- FORK runs a REAL child `AgentLoopImpl` (multi-turn, tool-capable) via the injected `ChildLoopFactory`, NOT a single `chat()` call; `loop.py` diff = 0 lines (the child reuses `run()`/`_run_turns`) (US-1/US-5).
- The child tool set is the recursion-safe subset (no `task_spawn`/`handoff`, via `make_default_executor(subagent_dispatcher=None)`); a child cannot spawn → depth bounded at 1 (US-2).
- `ForkExecutor` drains the child `LoopEvent` stream into a `SubagentResult` (final answer → `summary`, tokens summed, fail-closed on timeout/error); `wait_for` + the `task_spawn` handler dict mapping are byte-identical; AS_TOOL inherits the real loop (US-3).
- `tenant_id` is threaded into the child; the child opens a nested LOOP span under the parent (Cat 12) (US-4).
- No divergent single-shot path (`None` factory → `SubagentLaunchError`); the converted FORK/AS_TOOL tests assert real-loop behavior; no test deleted (US-5).
- `mypy --strict src/` 0; `run_all` 10/10 (LLM SDK leak 0; AP-1; AP-8; AP-10 no mock/real divergence); `black`/`isort`/`flake8 src/ tests/` clean; full backend pytest green (NET delta documented). 17.md Cat 11 note + CHANGE-061 + `20-subagent-child-loop-design.md` (8-pt gate) written.
- **Drive-through PASS**: real UI + real backend + real Azure — a chat-v2 `task_spawn` → a child that genuinely loops multi-turn + calls a tool → real summary in the parent answer → backend trace shows a nested child LOOP → TURN → TOOL_EXEC span; screenshot + observed-vs-intended diff + trace evidence. (No "gate-only" claimed as drive-through.)

---

## 6. Deliverables

- [ ] `ChildLoopFactory` type alias (Cat 11 `_contracts/`, TYPE_CHECKING AgentLoopImpl import) (US-1/US-5)
- [ ] `ForkExecutor` real child-loop drive + `LoopEvent`→`SubagentResult` drain + fail-closed + `None`-factory raise (US-1/US-3/US-5)
- [ ] `DefaultSubagentDispatcher` threads `child_loop_factory` → `ForkExecutor` (US-1)
- [ ] `build_real_llm_handler` builds the safe-subset child pair (`make_default_executor(subagent_dispatcher=None)`) + the `child_loop_factory` closure (tenant_id + tracer captured) + injects it (US-2/US-4)
- [ ] Converted FORK + AS_TOOL tests (mock-LLM child-loop factory, real-loop assertions; no test deleted) + NEW `test_subagent_child_loop.py` (multi-turn+tool / safe-subset / tenant / fail-closed / None-raises / nested-span) (US-1..US-5)
- [ ] mypy 0 + run_all 10/10 + format chain `flake8 src/ tests/` (validation)
- [ ] **drive-through PASS** (real UI + real backend + real Azure; child loops + uses a tool; nested-trace verified; screenshot + diff) (US-6)
- [ ] CHANGE-061 + `20-subagent-child-loop-design.md` (8-pt gate) + 17.md Cat 11 note + progress.md + retrospective.md
- [ ] commit (Day 0-N) — push + PR user-authorized

---

## 7. Workload Calibration

Scope class: **`subagent-child-loop-spike` (NEW, 0.60 mid-band) — 1st data point, pending 2-3 sprint validation**. This is a new-domain feature build in the Cat 11 hollow core, NOT the `backend-core-loop-refactor` pause-point shape (that touched `loop.py`; this does NOT). The work splits: ~`ChildLoopFactory` type + dispatcher/ForkExecutor threading (~1.5 hr) / the child-loop drive + event-drain → `SubagentResult` in `ForkExecutor` (~2.25 hr; the drain adapter + fail-closed + budget is the core new logic) / the factory closure + safe-subset wiring in `build_real_llm_handler` (~1.75 hr; the composition is where the deps come together) / tenant + span threading (~0.5 hr; mostly free — the child reuses `run()`'s span) / tests (~3 hr; converting the single-shot FORK/AS_TOOL tests to mock-LLM child loops + the new multi-turn/tool/safe-subset/fail-closed cases) / drive-through (~1.75 hr; spawn a tool-using child + verify the nested trace) / docs incl. the design-note extract (~1.75 hr). Dominant costs = tests + drive-through + the design note (spike). **Agent-delegated: no** (parent-direct) — this is the FIRST real child loop + a new-domain design (factory-at-composition) + a drive-through with a trace-nesting assertion; the design judgment + the drive-through are parent work. Future Cat 11 mode extensions (TEAMMATE/AS_TOOL deepening) MAY be agent-delegated once this pattern is proven. `agent_factor = 1.0`; does NOT extend the `AD-Calibration-AgentDelegated-WallClock-Measure` streak.

> Bottom-up est ~12.5 hr → class-calibrated commit ~7.5 hr (mult 0.60). **Agent-delegated: no.**

If Day-1 shows the child-loop drive ripples wider than `subagent/` + the factory closure (e.g. a Cat 11 → Cat 1 import cycle that `TYPE_CHECKING` does not resolve; `make_default_executor(subagent_dispatcher=None)` needs args not available at the composition site; the AP-1 detector flags the `async for ev in child.run()` drive as a pipeline; the `trace_context` in `ForkExecutor` is the request ctx not the parent loop ctx so the span does not nest), STOP and re-scope (split the drive-through / AS_TOOL conversion into a follow-up) rather than rush.

---

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| **Cat 11 → Cat 1 import cycle** (the factory's `AgentLoopImpl` type) | `ChildLoopFactory` uses a `TYPE_CHECKING` import + a string forward-ref; the actual `AgentLoopImpl` is constructed at composition (`handler.py`, which already imports Cat 1). Day-1 grep that `agent_harness/subagent/` has no runtime `from ...orchestrator_loop` import; if `mypy` complains, keep the alias as `Callable[..., Any]` with a docstring (last resort). |
| **`make_default_executor(subagent_dispatcher=None)` needs other args** | Day-0 confirmed it builds the pair + omitting `subagent_dispatcher` drops `task_spawn`+`agent_researcher`. Day-1 confirm the full signature (db/session/etc.) + pass the SAME locals the parent executor received in `build_real_llm_handler`. If it cannot run without a dispatcher arg, build a fresh `ToolRegistryImpl` + re-register the kept ToolSpecs/handlers manually (the D1 fallback). |
| **AP-1 flags the child-loop drive as a pipeline** | The child is a real `while True` `_run_turns` (the opposite of AP-1); `ForkExecutor` merely `async for`s the child's event stream (same shape as `resume()` driving `_run_turns`, which the AP-1 detector already accepts post-57.90). If the detector flags `ForkExecutor`, extend its delegation-awareness (a method that consumes a loop-driving generator is not a pipeline) — mirror the 57.89/90 detector fix. |
| **Child span does not nest** (orphaned trace) | The child's `run()` opens `start_span(trace_context=parent_ctx)`; pass the PARENT loop ctx into `child.run(trace_context=...)`. Day-1 confirm `ForkExecutor.execute`'s `trace_context` is the parent loop ctx (threaded via `spawn(... trace_context=...)`); the drive-through's trace check (nested LOOP under parent) is the proof. |
| **Token/duration accounting wrong** | Drain accumulates tokens from `LoopCompleted`/`LLMResponded`; Day-1 confirm whether `LoopCompleted` carries cumulative or per-turn tokens (accumulate if per-turn). `duration_ms` via the existing monotonic helper (not wall clock). The number is the child's honest total. |
| **AP-10 Mock-vs-Real divergence** (single-shot fallback) | NO fallback — `None` factory raises. The converted tests use a mock-LLM child loop = the SAME real-loop path with a mock `ChatClient` (mock at the ABC boundary, not a divergent code path). |
| **Recursion** (child spawns child → blow-up) | Structurally impossible: the child registry (`make_default_executor(subagent_dispatcher=None)`) has no `task_spawn`/`handoff`. A test asserts the child's tool set excludes them. No depth field needed. |
| **AS_TOOL regressed** | AS_TOOL delegates to the same `ForkExecutor` → inherits the factory for free. The converted `test_as_tool.py` guards it. Day-1 confirm the dispatcher owns ONE `ForkExecutor` (so AS_TOOL + FORK share the factory). |
| **Drive-through non-determinism (real LLM spawns?)** | The parent LLM must choose to call `task_spawn`; DEMO_SYSTEM_PROMPT / the request phrasing nudges it (the chat path already wires `task_spawn` per 57.64). Fall back: ALSO a scripted real-backend drive (call the dispatcher with a real child loop against the real LLM, assert the nested trace) + the UI drive; record exactly what was driven. |
| **Risk Class E (stale `--reload` backend)** | Clean restart before the drive-through (kill stale uvicorn reloader+worker procs; verify :8000 OWNER is the fresh PID) — the factory wiring is startup-built; a stale process runs the old single-shot dispatcher. Bit 57.91/92/93. |
| **Risk Class C (test isolation)** | The child loop builds fresh per spawn (no module singleton); run the full suite; existing `agent_harness/conftest.py` reset fixtures cover the dispatcher. |
| **Over-abstraction** | One factory type + one drive/drain method; no parameterized mega-executor, no premature TEAMMATE/HANDOFF generalization (Karpathy §2/§3). The child is a plain `AgentLoopImpl` — reuse, not a new loop class. |
| **Smuggling unrelated change** | The diff is exactly `subagent/` (factory type + ForkExecutor drive/drain + dispatcher threading) + the `handler.py` factory closure + converted/new tests + docs. `loop.py` diff = 0; TEAMMATE/HANDOFF diff = 0. |
| **LLM-neutrality** | The child uses the same `ChatClient` ABC; no adapter/SDK touched; `check_llm_sdk_leak` gates. |

---

## 9. Out of Scope (this sprint; → separate slices / ADs)

- **TEAMMATE real loop** (mailbox-consuming multi-turn teammate) — separate slice.
- **HANDOFF consumer / `HandoffService`** (boot the child session on `stop_reason="handoff"`) — separate slice.
- **SSE-relay of child loop events** (the UI showing the child's turn-by-turn stream) — needs a `LoopEvent` `parent_session_id`/`depth` contract field → `AD-Subagent-Child-Event-SSE-Relay`.
- **Recursion depth > 1 / nested spawning** — the child has no `task_spawn` (bounded at 1); nested spawn + `max_subagent_depth` enforcement is future.
- **parentUuid transcript chain / child checkpoint persistence** — the child is ephemeral; CC's `agent-{id}.jsonl` analog → `AD-Subagent-Transcript-Isolation`.
- **Child-internal governance** (the child running its own Cat 9 guardrails / Cat 10 verification) — `AD-Subagent-Child-Governance`.
- **Failure policies (FAIL_FAST / FAIL_SOFT / PARTIAL_RESULT)** — `SubagentBudget` has no `failure_policy`; deferred.
