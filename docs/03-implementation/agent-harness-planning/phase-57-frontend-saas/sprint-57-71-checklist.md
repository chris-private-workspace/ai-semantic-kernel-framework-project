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
- [ ] Branch `feature/sprint-57-71-loop-tracer` from `48e19846`
- [ ] plan+checklist commit; Day-0 progress commit
- [ ] Decisions: scope = **full span set** (TURN/LLM_CALL/TOOL_EXEC + PROMPT_BUILD/COMPACTION/VERIFICATION/MEMORY_OP); SpanCategory = **keep by-category enum + span-type via name/attributes** (zero blast radius); loop = **single trace-tree owner** (adapter/executor/parser tracers stay NoOp — avoids D8 double-instrumentation); span cost = **attribute only** (no ledger double-write); Tier 2 (Jaeger) + SpanStarted/SpanEnded→SSE = **deferred** (Area-C / A-5); **Agent-delegated: yes** (Stage-1 Tier0+core spans / Stage-2 extra spans+tests; parent re-verify each)

---

## Day 1 — Stage 1: Tier 0 injection + nesting fix + core spans (TURN/LLM_CALL/TOOL_EXEC)

### 1.1 Tier 0 — real tracer injection (US-1)
- [ ] `handler.py:164` — add `tracer: Tracer | None = None` to `build_real_llm_handler`; pass `tracer=tracer` into `AgentLoopImpl(...)` (`:268-292`) (mirror prompt_builder/reducer dep pattern `:255-256`/`:283-285`)
- [ ] `router.py` — thread the existing `get_tracer()` real tracer (`:144`) into the `build_real_llm_handler(...)` call (no new `Depends`; confirm any `build_handler` indirection)
- [ ] Integration test: build via `build_real_llm_handler(... tracer=real)` → assert `loop._tracer` is NOT `NoOpTracer`; a run opens a real `agent_loop.run` root span
  - Verify: `pytest backend/tests/integration -k tracer_injection`

### 1.2 Nesting fix + helper extend (US-2)
- [ ] `loop.py:788-792` — bind root span `as root_ctx` (capture yield); thread `root_ctx` (not outer `ctx`) downward
- [ ] `helpers.py:40` — extend `category_span` with optional `attributes: dict | None = None` + `span_type: str | None = None` (folds span_type into attributes); grep existing `category_span(` callers → confirm unaffected
  - Verify: `grep -rn "category_span(" backend/src`

### 1.3 Core operation spans — TURN / LLM_CALL / TOOL_EXEC (US-2/US-3)
- [ ] TURN span wrapping the per-turn `while` body — `name="agent_loop.turn"`, cat=ORCHESTRATOR, attrs `{span_type: TURN, turn: n}`, `as turn_ctx`; thread `turn_ctx` into the turn's operations
- [ ] LLM_CALL span around `chat_client.chat(...)` (`loop.py:950`) — `name="agent_loop.llm_call"`, cat=ORCHESTRATOR, attrs `{span_type: LLM_CALL, model, prompt_tokens, completion_tokens, cached_input_tokens, total_tokens, cost_usd}` (tokens from `ChatResponse.usage`; cost via adapter pricing — **span-attribute ONLY, no ledger write**)
- [ ] TOOL_EXEC span around each `tool_executor.execute(...)` (`loop.py:1183`) — `name=f"agent_loop.tool.{name}"`, cat=TOOLS, attrs `{span_type: TOOL_EXEC, tool, latency_ms}` (latency from span timing); parallel tools = sibling spans
- [ ] All via `async with` → `end()` guaranteed; ERROR status + `record_exception` on raised exception (confirm ABC error API)
- [ ] Backend green (parent re-verify): black/isort/flake8 0; `mypy src/` 0; `run_all.py` 10/10 (SDK leak 0); targeted observability tests pass

---

## Day 2 — Stage 2: full span set + tree tests

### 2.1 Extra operation spans — PROMPT_BUILD / COMPACTION / VERIFICATION / MEMORY_OP (US-2/US-3)
- [ ] Locate call sites via existing `trace_context=` threading (`loop.py:847/901/939/972/1141/...`); open a span only when the operation actually runs that turn (no empty spans)
- [ ] PROMPT_BUILD (cat=PROMPT_BUILDER) / COMPACTION (cat=CONTEXT_MGMT) / MEMORY_OP (cat=MEMORY) / VERIFICATION (cat=VERIFICATION) — each `{span_type: ...}` attr, child of `turn_ctx`
- [ ] Confirm no double-instrumentation: adapter/executor/parser internal tracers remain NoOp (not wired); verification `_obs.py:53` existing span not double-opened by loop (loop opens its own VERIFICATION around the call boundary — confirm no overlap or scope to one)

### 2.2 SpanCategory decision recorded (US-3)
- [ ] `02-architecture-design.md §Naming Drift Note` — record: KEEP by-category enum; express span-type via span name + `attributes["span_type"]` (rationale: enum load-bearing in `metrics.py` + 8 sites; zero blast radius)

### 2.3 RecordingTracer tree tests (US-4)
- [ ] Extend `RecordingTracer` (`test_observability_coverage.py:50-89`) to capture parent linkage (span_id / parent ctx) → flat list becomes reconstructable tree
- [ ] Assert multi-turn run reconstructs LOOP→N×TURN→{LLM_CALL, TOOL_EXEC×k, PROMPT_BUILD, COMPACTION?, VERIFICATION?, MEMORY_OP?} with correct parent/child nesting
- [ ] Assert LLM_CALL carries token attributes; TOOL_EXEC carries latency; span status ERROR on a raised exception
- [ ] Existing membership assertions (`:131-142`) still pass (now under the real tree)
  - Verify: `pytest backend/tests/integration/orchestrator_loop/test_observability_coverage.py -v`

---

## Day 3 — Full sweep + edge cases

- [ ] Full `pytest tests/unit tests/integration` → all green (tracer additions + no regression); record count
- [ ] Edge: zero-tool turn (no TOOL_EXEC span) / multi-tool turn (sibling TOOL_EXEC) / exception mid-turn (ERROR status + spans still `end()`) / NoOp tracer path (default, no real tracer) still works
- [ ] Confirm no span→cost-ledger write (router recorders unchanged; grep loop.py for any ledger/cost-recorder call inside spans)
- [ ] Parent decisive re-verify: pytest full; `mypy src/` 0; `run_all.py` 10/10; black unchanged + isort/flake8 0; Vitest unchanged (no FE)
- [ ] No drift beyond Day-0 D1-D9

---

## Day 4 — Closeout

### 4.1 Closeout docs
- [ ] `02.md §Naming Drift Note` (Day 2) + `01.md §範疇12` note (Tier 0+1 shipped; Tier 2 deferred; SpanStarted/SpanEnded→SSE = A-5); CHANGE-039 created
- [ ] progress.md (Day 0-4) + retrospective.md (Q1-Q7) — NO design note (feature-continuation)
- [ ] Calibration: `cat12-loop-tracer-additive` 0.60 (NEW, 1 pt) + `agent_factor` 0.65 (CAVEATED — 9th consecutive no-clean-wall-clock 57.63→71); record `calibration-log.md §3`
- [ ] MEMORY.md pointer + `project_phase57_71_loop_tracer.md` subfile + CLAUDE.md lean (Current Sprint row + footer)

### 4.2 Final verify + ship
- [ ] **Final-commit `black --check`** (AD-Final-Commit-Black-Check): black unchanged + isort/flake8 0 + mypy src 0 + run_all 10/10
- [ ] commit (Day 1-4) + push + PR — **user-authorized** (push/PR pending user approval)
- [ ] Carryover recorded (plan §9 + retrospective §Q5 + memory subfile): Tier 2 Jaeger export (Area-C/DevOps); SpanStarted/SpanEnded→SSE (A-5); nest internal spans (DRY refactor); cross-process subagent parent_span_id; A-5c Inspector UI; A-6 + FE /subagents wiring
