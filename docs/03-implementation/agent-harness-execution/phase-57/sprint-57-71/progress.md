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
- **Parent re-verify gates**: black/isort/flake8 0; `mypy src/` 0/329; `run_all.py` 10/10 (`check_llm_sdk_leak` 0); pytest broad sweep (unit/agent_harness + unit/business_domain + integration/orchestrator_loop + integration/api) 1346 passed / 1 skipped (pre-existing). Verdict: **PASS**. Commit `<stage-1>`.
