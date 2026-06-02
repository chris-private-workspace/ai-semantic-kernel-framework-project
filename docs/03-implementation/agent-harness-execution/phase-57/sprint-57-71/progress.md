# Sprint 57.71 Progress — A-4 Loop Tracer (Tier 0 + Tier 1, full span set)

**Plan**: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-71-plan.md`
**Checklist**: `.../sprint-57-71-checklist.md`
**Branch**: `feature/sprint-57-71-loop-tracer` (from main `48e19846`)

---

## Day 0 — 2026-06-02 — Plan-vs-Repo Verify + Branch + Decisions

### Scope selection (AskUserQuestion 2026-06-02)
- After the A+B+C integration-gap status review, the user picked **A-4 loop tracer** (Area-A item 4) as the next sprint (57.71). Two design decisions confirmed via AskUserQuestion: **scope = full span set** (TURN/LLM_CALL/TOOL_EXEC + PROMPT_BUILD/COMPACTION/VERIFICATION/MEMORY_OP); **SpanCategory drift = keep by-category enum + express span-type via span name / `attributes["span_type"]`** (zero blast radius). FE `/subagents` wiring (57.70 carryover) deferred to a future sprint.

### Three-prong Day-0 verify — drift D1-D9 (researcher ground-truth, main `48e19846`)

The A-4 analysis (`cat12-loop-tracer-analysis-20260531.md`) was written at Sprint 57.63 (`526be549`); a Day-0 researcher pass confirmed the §3 Tier 0 + Tier 1 scope is still valid (loop span structure unchanged across 57.64-70) and corrected the drifted line refs:

- **D1** — Root span at `loop.py:788-792` (analysis said :779); `async with ... start_span(name="agent_loop.run", category=ORCHESTRATOR, trace_context=ctx)` is **NOT bound `as child`** → child ctx discarded, outer `ctx` threaded everywhere (the nesting bug).
- **D2** — Tracer fallback `loop.py:235` + ctor param `loop.py:203` (analysis said :226); param exists, nothing passes it on the chat path → prod runs `NoOpTracer`.
- **D3** — `build_real_llm_handler` (`handler.py:164`) builds `AgentLoopImpl(...)` (`:268-292`) with **no `tracer=`** and **no `tracer` param** in its signature; inject template = prompt_builder/reducer dep pattern (`handler.py:255-256` + `:283-285`).
- **D4** — Router tracer `router.py:144` (`Depends(get_tracer)`) → only `BusinessServiceFactory` (`:198`), never the loop.
- **D5** — `SpanCategory` (`_contracts/observability.py:41-56`) = 13 by-category values, used at ~8 sites + `metrics.py:65-107` name→category map → **load-bearing**. `TraceContext.child()` does NOT exist (children via `start_span` yield; only `create_root()` at `:71`) — analysis's `ctx.child()` framing corrected.
- **D6** — ABC `start_span` (`_abc.py:36-43`): `name`/`category`/`trace_context`/`attributes` → `AbstractAsyncContextManager[TraceContext]`. Helper `category_span` (`helpers.py:40`) has **no `attributes` param** → must extend (or call `start_span` directly).
- **D7** — Tier-1 wrap points: LLM `loop.py:950`, tool `loop.py:1183`, parser `loop.py:988`; span style to mirror = `executor.py:214-218` / `parser.py:68-72`. Token source `ChatResponse.usage: TokenUsage` (`chat.py:102-105,122`); no cost field → adapter `get_pricing()` (`adapters/_base/pricing.py`).
- **D8 (critical)** — adapter has its OWN tracer emitting `llm_chat` under ORCHESTRATOR (`adapter.py:189-191`) **iff** wired → loop-level LLM_CALL would double-instrument. **Resolution: loop is the single trace-tree owner — leave adapter/executor/parser internal tracers NoOp (do NOT wire); loop wraps at the call boundary.** No double spans.
- **D9** — `test_observability_coverage.py:131-142` asserts membership only (no tree); `RecordingTracer` (`:50-89`) flat list → extend to capture parent linkage.

### go/no-go = **GO**
- <20% drift (line-ref corrections + the D8 single-owner design decision). Analysis Tier 0 + Tier 1 scope unchanged; loop span structure stable across 57.64-70. Plan + checklist drafted to the confirmed scope (full span set; keep enum + span-type via name/attributes; loop single owner).

### Decisions
- Scope = full span set; SpanCategory = keep enum + span-type via name/attributes (zero blast radius); loop = single trace-tree owner (adapter/executor/parser tracers stay NoOp — avoids D8 double-instrumentation); span token/cost = attribute only (no ledger double-write); Tier 2 (Jaeger) + SpanStarted/SpanEnded→SSE = deferred (Area-C / A-5).
- **Agent-delegated: yes** — Stage-1 (Tier 0 inject + nesting fix + TURN/LLM_CALL/TOOL_EXEC); Stage-2 (PROMPT_BUILD/COMPACTION/VERIFICATION/MEMORY_OP + RecordingTracer tree tests). Parent independently re-verifies each stage (reads loop.py diffs for span lifecycle + ctx threading correctness).

---

## Day 1 — 2026-06-02 — Stage-1: Tier 0 + nesting fix + core spans (agent-delegated + parent re-verify)

`code-implementer` agent built Stage-1; parent independently re-verified (read the span-boundary diffs + ran gates).

- **Changes**: `handler.py` (`build_real_llm_handler` + `build_handler` gain `tracer` param → `AgentLoopImpl(tracer=)`); `router.py:226` (thread existing `Depends(get_tracer)` into `build_handler`); `loop.py` (root span bound `as root_ctx` + `span_type=LOOP` at :796; TURN span at :894 `trace_context=root_ctx` `as turn_ctx`, opened after pre-LLM terminators; LLM_CALL span at :984 `trace_context=turn_ctx` + token attrs post-response; TOOL_EXEC span at :1252 `trace_context=turn_ctx`); `helpers.py:44` (`category_span` += optional `attributes`/`span_type`).
- **Re-indent**: the TURN span wraps the per-turn body → ~472-line +4 re-indent (888→1359), done programmatically + `py_compile`-verified. Parent confirmed the span boundaries (LOOP→while→TURN→{PromptBuild,LLM_CALL,TOOL_EXEC}) by reading :785-988 / :1222-1266 / :1340-1374 — nesting correct; control flow intact (1346 integration+unit tests pass).
- **Tests**: 2 NEW Tier-0 injection tests (`test_chat_category_activation_wiring.py`); `test_observability_coverage.py` membership assertions EXTENDED (agent_loop.turn×2 / llm_call×2 / agent_loop.tool.echo_tool); 2 unit test doubles' `start_span` signatures aligned to the ABC (`category_span` now forwards `attributes=`) — assertions unchanged, none weakened (parent verified all 4 test diffs).
- **Known limitation (carryover)**: token attrs written post-response into a shared `llm_attrs` dict → RecordingTracer (by-reference) sees them, but OTelTracer copies attrs at span-open so per-token OTel export awaits a Tracer-ABC set-attribute API (Tier-2-adjacent). `cost_usd` intentionally deferred (no adapter-pricing coupling; span attrs never feed the cost ledger).
- **Parent re-verify gates**: black/isort/flake8 0; `mypy src/` 0/329; `run_all.py` 10/10 (`check_llm_sdk_leak` 0); pytest broad sweep (unit/agent_harness + unit/business_domain + integration/orchestrator_loop + integration/api) 1346 passed / 1 skipped (pre-existing). Verdict: **PASS**. Commit `5c54bf02`.

---

## Day 2 — 2026-06-02 — Stage-2: full span set + tree tests (agent-delegated + parent re-verify)

`code-implementer` agent built Stage-2; parent independently re-verified (read the span boundaries + tree-test diff).

- **Changes**: `loop.py` — PROMPT_BUILD span (`:931`, `trace_context=turn_ctx`, gated by prompt_builder) + COMPACTION span (`:877`, `trace_context=root_ctx` — runs pre-TURN, surgical, gated by compactor). `test_observability_coverage.py` — `RecordingTracer` extended to mint a child `TraceContext` (fresh span_id, parent_span_id = incoming) + capture status/exception; 6 new tests (tree reconstruction + nesting / token attrs / ERROR status / zero-tool / multi-tool sibling / NoOp default).
- **Reality finding — VERIFICATION + MEMORY_OP deferred (N/A at loop level)**: `AgentLoopImpl.run()` has NO verifier call — verification is the outer wrapper `verification/correction_loop.py:run_with_verification` (verifiers own `verifier.{name}` spans); memory injection is inside `prompt_builder.build()` (→ PROMPT_BUILD) or via tools (→ TOOL_EXEC). No clean loop-level call boundary → deferred rather than forced (AP-4 avoided). The user-chosen "full span set" thus delivered as 6 span types (LOOP/TURN/LLM_CALL/TOOL_EXEC/PROMPT_BUILD/COMPACTION) + 2 documented deferrals.
- **Parent re-verify**: read `loop.py:860-934` (COMPACTION + PROMPT_BUILD boundaries + ctx) + the full test diff. Tree test asserts TURN.parent==LOOP, LLM_CALL/TOOL_EXEC.parent ∈ TURN ids (≠ root) — the decisive D1 nesting proof. RecordingTracer change is test-only (production OTelTracer/NoOpTracer untouched). Verdict: **PASS**. Commit `bff3aeef`.

## Day 3 — 2026-06-02 — Full sweep + edge (decisive re-verify)

- **Full backend sweep** (parent-run): `pytest tests/unit tests/integration` → **2057 passed / 4 skipped / 2 warnings** in 95.8s (= 57.70 baseline 2049 + 8 new; warnings pre-existing coroutine-cancel, unrelated).
- **Edge** (covered by new tests): zero-tool turn (TURN+LLM_CALL, no TOOL_EXEC); multi-tool turn (sibling TOOL_EXEC under one TURN); exception → ERROR status on LLM_CALL+TURN+LOOP; NoOp default path runs clean.
- **Decisive gates**: pytest 2057; `mypy src/` 0/329; `run_all.py` 10/10 (SDK leak + RLS + event-schema green); black 605 unchanged + isort/flake8 0; Vitest unchanged (no FE).
- No double-instrumentation (adapter/executor/parser tracers NoOp); no span→ledger write (router recorders unchanged). No drift beyond Day-0 D1-D9.

## Day 4 — 2026-06-02 — Closeout

- `02.md §Naming Drift Note` += SpanCategory resolution (keep enum + span-type via name/attributes); `01.md §範疇12` += Tier 0+1 shipped note + deferral list; CHANGE-039 created.
- retrospective.md (Q1-Q7, no design note — feature-continuation); calibration-log §3.
- Final verify: black 605 unchanged + isort/flake8 0 + mypy 0/329 + run_all 10/10 (AD-Final-Commit-Black-Check).
- MEMORY.md pointer + subfile + CLAUDE.md lean. Carryover (plan §9): Tier 2 Jaeger export (Area-C); SpanStarted/SpanEnded→SSE (A-5); VERIFICATION/MEMORY_OP via nest-existing-spans refactor; token attrs→OTel (Tracer set-attribute API); cross-process subagent linkage; A-5c / A-6 / FE /subagents wiring.
