# Sprint 57.71 — Checklist (A-4 Loop Tracer: Real Tracer Injection + Loop-Internal Span Tree — Tier 0 + Tier 1, full span set)

**Plan**: [`sprint-57-71-plan.md`](./sprint-57-71-plan.md)
**Created**: 2026-06-02
**Status**: Draft (commit/push/PR user-gated)

> Rule: only `[ ]` → `[x]`; never delete unchecked items; defer with `🚧 + reason`.
> Feature-continuation (extends built Cat 12 Tracer ABC + existing span pattern; purely-additive loop wraps) → **no design note**. SpanCategory decision recorded in `02.md §Naming Drift Note`. Scope (user-confirmed): full span set; keep enum + span-type via name/attributes.

---

## Day 0 — Plan-vs-Repo Verify + Branch + Decisions

### 0.1 Three-prong Day-0 verify (researcher ground-truth pass, main `48e19846`)
- [x] **Prong 1 (path)**: `loop.py` root span (:788-792, NOT `as child`) + tracer fallback (:235) + ctor param (:203); `build_real_llm_handler` (`handler.py:164`) + `AgentLoopImpl(...)` (`:268-292`, no tracer param); `router.py:144` `get_tracer` → only `BusinessServiceFactory` (:198); `helpers.category_span` (:40, no attributes); `_contracts/observability.py` SpanCategory (:41-56) + `start_span` ABC (`_abc.py:36-43`); `test_observability_coverage.py` + `RecordingTracer` (:50-89)
- [x] **Prong 2 (content)**: root span child ctx discarded (nesting bug D1); `TraceContext.child()` does NOT exist (children via start_span yield — analysis corrected); SpanCategory load-bearing (`metrics.py:65-107` map + 8 sites) → keep enum (user decision); wrap points LLM `loop.py:950` / tool `:1183` / parser `:988`; token source `ChatResponse.usage: TokenUsage` (`chat.py:102-105,122`); no cost field → adapter `get_pricing()`; **adapter has own tracer emitting `llm_chat` (`adapter.py:189-191`) → double-instrumentation risk D8 → loop is single owner, adapter/executor/parser tracers stay NoOp**
- [x] **Prong 3 (schema)**: N/A — no DB table / migration / ORM in this sprint (observability-only)
- [x] **Doc-location**: `02.md §Naming Drift Note` (record SpanCategory resolution); `01.md §範疇12` (Tier 0+1 shipped note); `17.md §Contract 12` UNCHANGED (SpanStarted/SpanEnded→SSE = A-5, single-source preserved); CHANGE-039
- [x] Catalogued drift D1-D9 in plan §0; **go/no-go = GO** (scope unchanged across 57.64-70; analysis Tier 0+1 still valid; <20% drift — only line-ref corrections + D8 single-owner design decision)

### 0.2 Branch + decisions
- [x] Branch `feature/sprint-57-71-loop-tracer` from `48e19846`
- [x] plan+checklist commit; Day-0 progress commit (`ced0616a`)
- [x] Decisions: scope = **full span set** (TURN/LLM_CALL/TOOL_EXEC + PROMPT_BUILD/COMPACTION/VERIFICATION/MEMORY_OP); SpanCategory = **keep by-category enum + span-type via name/attributes** (zero blast radius); loop = **single trace-tree owner** (adapter/executor/parser tracers stay NoOp — avoids D8 double-instrumentation); span cost = **attribute only** (no ledger double-write); Tier 2 (Jaeger) + SpanStarted/SpanEnded→SSE = **deferred** (Area-C / A-5); **Agent-delegated: yes** (Stage-1 Tier0+core spans / Stage-2 extra spans+tests; parent re-verify each)

---

## Day 1 — Stage 1: Tier 0 injection + nesting fix + core spans (TURN/LLM_CALL/TOOL_EXEC)

### 1.1 Tier 0 — real tracer injection (US-1)
- [x] `handler.py:173` — added `tracer: Tracer | None = None` to `build_real_llm_handler`; passed `tracer=tracer` into `AgentLoopImpl(...)`; also threaded through `build_handler` dispatcher (`:323/:359`) (TYPE_CHECKING `Tracer` import)
- [x] `router.py:226` — threaded the existing `Depends(get_tracer)` real tracer into the `build_handler(...)` call (no new `Depends`)
- [x] Integration test: `test_real_handler_injects_real_tracer` + `test_real_handler_tracer_defaults_to_noop` (`test_chat_category_activation_wiring.py`) → assert `loop._tracer is real OTelTracer` / NoOp default
  - Verify: `pytest backend/tests/integration/api/test_chat_category_activation_wiring.py -k tracer` ✅

### 1.2 Nesting fix + helper extend (US-2)
- [x] `loop.py:796-801` — bound root span `as root_ctx` + `attributes={"span_type":"LOOP"}`; thread `root_ctx` → TURN spans (D1 nesting fix)
- [x] `helpers.py:44` — extended `category_span` with optional `attributes` + `span_type` (additive default None; folds span_type into attributes); grep confirmed existing 3-arg callers unaffected (verification/business_domain)

### 1.3 Core operation spans — TURN / LLM_CALL / TOOL_EXEC (US-2/US-3)
- [x] TURN span (`loop.py:894-899`) — `name="agent_loop.turn"`, cat=ORCHESTRATOR, `trace_context=root_ctx`, attrs `{span_type: TURN, turn}`, `as turn_ctx`; opened AFTER pre-LLM terminators (no empty TURN on MAX_TURNS exit); wraps the genuine per-turn body
- [x] LLM_CALL span (`loop.py:984`) — `name="agent_loop.llm_call"`, cat=ORCHESTRATOR, `trace_context=turn_ctx`, attrs `{span_type: LLM_CALL, model}` + token attrs written post-response into shared `llm_attrs` dict (🚧 by-reference — RecordingTracer sees tokens; OTel per-token export awaits Tier 2 set-attribute API; **cost_usd deferred** to avoid adapter-pricing coupling + ledger double-count)
- [x] TOOL_EXEC span (`loop.py:1252-1257`) — `name=f"agent_loop.tool.{tc.name}"`, cat=TOOLS, `trace_context=turn_ctx`, attrs `{span_type: TOOL_EXEC, tool}` (latency from span timing); parallel tools = sibling spans
- [x] All via `async with` → `end()` guaranteed; ERROR status + `record_exception` fire automatically via the tracer's `_span_cm` (`tracer.py:192-195`) when an exception propagates
- [x] Backend green (parent re-verified): black/isort/flake8 0; `mypy src/` 0/329; `run_all.py` 10/10 (SDK leak 0); pytest broad sweep 1346 passed / 1 skipped (pre-existing)

---

## Day 2 — Stage 2: full span set + tree tests

### 2.1 Extra operation spans — PROMPT_BUILD / COMPACTION / VERIFICATION / MEMORY_OP (US-2/US-3)
- [x] Located call sites; opened spans only when the operation runs (no empty spans)
- [x] PROMPT_BUILD (`loop.py:931`, cat=PROMPT_BUILDER, `trace_context=turn_ctx`, gated by prompt_builder) + COMPACTION (`loop.py:877`, cat=CONTEXT_MGMT, `trace_context=root_ctx` — runs pre-TURN, gated by compactor)
- 🚧 VERIFICATION + MEMORY_OP **DEFERRED (N/A at loop level)**: `AgentLoopImpl.run()` has no verifier call (verification is the outer wrapper `correction_loop.py:run_with_verification`, verifiers own `verifier.{name}` spans); memory is inside `prompt_builder.build()` (→ PROMPT_BUILD) / via tools (→ TOOL_EXEC). No clean call boundary → forcing a span = AP-4 Potemkin. Carryover = "nest existing internal spans" DRY refactor (plan §9)
- [x] Confirmed no double-instrumentation: adapter/executor/parser internal tracers remain NoOp (loop is single owner, D8)

### 2.2 SpanCategory decision recorded (US-3)
- [x] `02-architecture-design.md §Naming Drift Note` — recorded: KEEP by-category enum; express span-type via span name + `attributes["span_type"]` (enum load-bearing in `metrics.py` + 8 sites; zero blast radius)

### 2.3 RecordingTracer tree tests (US-4)
- [x] Extended `RecordingTracer` to mint a child `TraceContext` (fresh span_id, parent_span_id = incoming) + capture status/exception → reconstructable tree (test-only; production tracer untouched)
- [x] `test_reconstructs_loop_turn_operation_tree_with_correct_nesting` — asserts TURN.parent==LOOP + LLM_CALL/TOOL_EXEC.parent ∈ TURN ids (≠ root LOOP) — the D1 nesting fix
- [x] LLM_CALL token attrs (by-reference) + TOOL_EXEC tool attr asserted; `test_raised_exception_sets_error_span_status` (ERROR on LLM_CALL+TURN+LOOP)
- [x] Existing membership assertions extended (now under the real tree); `test_observability_coverage.py` 9/9
  - Verify: `pytest backend/tests/integration/orchestrator_loop/test_observability_coverage.py -v` ✅

---

## Day 3 — Full sweep + edge cases

- [x] Full `pytest tests/unit tests/integration` → **2057 passed / 4 skipped** (= 57.70 baseline 2049 + 8 new; no regression)
- [x] Edge (new tests): zero-tool turn (no TOOL_EXEC) / multi-tool turn (sibling TOOL_EXEC under one TURN) / exception → ERROR status / NoOp default path runs clean
- [x] Confirmed no span→cost-ledger write (router recorders unchanged; span token/cost = attribute only)
- [x] Parent decisive re-verify: pytest 2057; `mypy src/` 0/329; `run_all.py` 10/10; black 605 unchanged + isort/flake8 0; Vitest unchanged (no FE)
- [x] No drift beyond Day-0 D1-D9

---

## Day 4 — Closeout

### 4.1 Closeout docs
- [x] `02.md §Naming Drift Note` (SpanCategory resolution) + `01.md §範疇12` note (Tier 0+1 shipped; Tier 2 deferred; SpanStarted/SpanEnded→SSE = A-5; VERIFICATION/MEMORY_OP deferred); CHANGE-039 created
- [x] progress.md (Day 0-4) + retrospective.md (Q1-Q7) — NO design note (feature-continuation)
- [x] Calibration: `cat12-loop-tracer-additive` 0.60 (NEW, 1 pt) + `agent_factor` 0.65 (CAVEATED — 9th consecutive no-clean-wall-clock 57.63→71); record `calibration-log.md §3`
- [x] MEMORY.md pointer + `project_phase57_71_loop_tracer.md` subfile + CLAUDE.md lean (Current Sprint row + footer)

### 4.2 Final verify + ship
- [x] **Final-commit `black --check`** (AD-Final-Commit-Black-Check): black 605 unchanged + isort/flake8 0 + mypy src 0/329 + run_all 10/10
- [ ] commit (Day 1-4) + push + PR — **user-authorized** (push/PR pending user approval)
- [x] Carryover recorded (plan §9 + retrospective §Q5 + memory subfile): Tier 2 Jaeger export (Area-C/DevOps); SpanStarted/SpanEnded→SSE (A-5); VERIFICATION/MEMORY_OP via nest-existing-spans refactor; token attrs→OTel (Tracer set-attribute API); cross-process subagent parent_span_id; A-5c Inspector UI; A-6 + FE /subagents wiring
