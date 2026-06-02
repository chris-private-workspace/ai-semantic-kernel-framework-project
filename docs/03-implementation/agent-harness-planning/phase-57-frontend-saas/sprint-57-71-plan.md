# Sprint 57.71 Plan — A-4 Loop Tracer: Real Tracer Injection + Loop-Internal Span Tree (Tier 0 + Tier 1, full span set)

**Purpose**: Close `AD-Cat12-LoopTracer` (Area-A item 4) — the production loop currently emits **no reconstructable trace tree**: it opens only a single root span (`agent_loop.run`), that root runs on a `NoOpTracer` because the handler never injects a real tracer, and the one `start_span` is not bound `as child` so even nested spans would be flat siblings. This sprint ships **Tier 0** (inject a real `OTelTracer` into the loop via `build_real_llm_handler`, making the root span real) + **Tier 1** (open the per-turn child span tree in `loop.py` — `TURN` per turn, `LLM_CALL`/`TOOL_EXEC`/`PROMPT_BUILD`/`COMPACTION`/`VERIFICATION`/`MEMORY_OP` per operation — fix the `as child` nesting so the tree reconstructs LOOP→TURN→operation, set 3-axis span attributes, and resolve the SpanCategory naming drift by KEEPING the by-category enum and expressing span-type via span name + `attributes["span_type"]`). The loop is the **single trace-tree owner** this sprint (the chat-path adapter/executor/parser internal tracers stay NoOp — not wired — which eliminates the adapter `llm_chat` double-instrumentation risk). **Tier 2 (real Jaeger/OTLP export) is deferred to Area-C/DevOps**; the `SpanStarted`/`SpanEnded`→SSE sliver is **A-5** (out of scope). This is a **feature-continuation sprint** (it extends the already-built Cat 12 `Tracer` ABC + existing span pattern — purely additive `loop.py` wraps, no control-flow change, no new mechanism), so **no design note** is required (per `sprint-workflow.md §Step 5.5`); the SpanCategory decision is recorded in `02.md §Naming Drift Note`.
**Category / Scope**: 範疇 12 (Observability / Tracing, cross-cutting) — loop-internal span tree + real tracer injection; touches Cat 1 (Orchestrator loop hot-path wraps) + chat handler/router (tracer plumbing); Phase 57.71
**Created**: 2026-06-02
**Status**: Draft — code execution gated on Day-0 GO (Step 2.5). Ground-truth already gathered via a Day-0 researcher pass (file:line drift from the 57.63-era analysis corrected — see §0).
**Source**: A-4 deep-analysis `claudedocs/5-status/cat12-loop-tracer-analysis-20260531.md` (§3 Tier framing, §6 recommendation, §7 DoD) + A+B+C capstone `integration-gap-capstone-abc-20260601.md` (A-4 = "most purely-additive Area-A item", priority #5) + **Day-0 ground-truth researcher pass (2026-06-02, main `48e19846`)** + user AskUserQuestion decisions 2026-06-02 (**scope = full span set**; **SpanCategory = keep by-category enum + express span-type via span name / attributes**)

> **Modification History**
> - 2026-06-02: Initial creation — A-4 loop tracer Tier 0 + Tier 1 (full span set); feature-continuation (no design note); SpanCategory drift resolved via name/attributes (user decision)

---

## 0. Background

`AD-Cat12-LoopTracer` is a **triple gap** (analysis §0): (1) the loop opens **only a single root span** — no per-turn / per-LLM-call / per-tool child spans, so there is no reconstructable trace tree; (2) the handler **never injects a real tracer**, so even that root span runs on a `NoOpTracer` in production; (3) the **OTel exporter is env-gated** (configured in code but exports only with a running collector + `OTEL_*` env). Cat 12 is the **most purely-additive** Area-A item: it requires **no control-flow change** and **no other category to be live** — it only *wraps* existing operations in spans. Router-layer recorders (SLA / cost / audit) are genuinely live and independent of the span tree.

### Day-0 ground-truth (file:line corrected from the 57.63-era analysis; main `48e19846`)

A Day-0 researcher pass confirmed the analysis §3 Tier 0 + Tier 1 scope is still valid (loop span structure unchanged across 57.64-57.70) and corrected the drifted line refs:

- **D1 — Root span** at `loop.py:788-792`: `async with self._tracer.start_span(name="agent_loop.run", category=SpanCategory.ORCHESTRATOR, trace_context=ctx)` — **NOT bound `as child`**; the yielded child `TraceContext` is discarded and the loop keeps threading the **outer `ctx`** into all nested calls (the nesting bug). (Analysis said `:779`.)
- **D2 — Tracer fallback** at `loop.py:235` (`self._tracer = tracer or NoOpTracer()`); ctor param at `loop.py:203` (`tracer: Tracer | None = None`). (Analysis said `:226`.) → the param exists; nothing passes it on the chat path.
- **D3 — Handler injection point**: `build_real_llm_handler` at `api/v1/chat/handler.py:164`; constructs `AgentLoopImpl(...)` at `handler.py:268-292` with **NO `tracer=`** and the function signature has **no `tracer` param at all**. Copyable inject template = the prompt_builder/reducer dependency pattern at `handler.py:255-256` + `:283-285` (build/accept dep → pass as ctor kwarg).
- **D4 — Router tracer** at `router.py:144` (`tracer: Tracer = Depends(get_tracer)`) flows only to `BusinessServiceFactory(... tracer=tracer)` at `router.py:198` — **never to `build_handler`/loop**. → thread the same real tracer into `build_real_llm_handler`.
- **D5 — SpanCategory** at `_contracts/observability.py:41-56`: **13 by-category values** (ORCHESTRATOR/TOOLS/MEMORY/CONTEXT_MGMT/PROMPT_BUILDER/OUTPUT_PARSER/STATE_MGMT/ERROR_HANDLING/GUARDRAILS/VERIFICATION/SUBAGENT/OBSERVABILITY/HITL). Used at ~8 sites + the metric-name→category map in `observability/metrics.py:65-107` → **load-bearing**. **`TraceContext.child()` does NOT exist** — children come from the `start_span` yield; only `create_root()` exists (`observability.py:71`). (Analysis's `ctx.child()` framing corrected.)
- **D6 — ABC `start_span`** (`observability/_abc.py:36-43`): kwargs `name: str`, `category: SpanCategory`, `trace_context: TraceContext | None`, `attributes: dict | None` → returns `AbstractAsyncContextManager[TraceContext]` (yields child ctx). The helper `category_span(tracer, name, category)` at `observability/helpers.py:40` has **no `attributes` param** → must be extended (or call `start_span` directly) to carry token/cost/span_type attributes.
- **D7 — Tier-1 wrap points**: LLM call `loop.py:950` (`await self._chat_client.chat(...)`); tool call `loop.py:1183` (`await self._tool_executor.execute(...)`); parser `loop.py:988`. Existing span style to mirror: `tools/executor.py:214-218` (`name=f"tool.{call.name}"`, `SpanCategory.TOOLS`) + `output_parser/parser.py:68-72` (`name="output_parser.parse"`, `OUTPUT_PARSER`). Token source: `ChatResponse.usage: TokenUsage` (`_contracts/chat.py:122`; fields `prompt_tokens`/`completion_tokens`/`cached_input_tokens`/`total_tokens` at `:102-105`); **no cost field** on the response → cost via the adapter `get_pricing()` (`adapters/_base/pricing.py`).
- **D8 — Critical: adapter has its OWN tracer** and emits `llm_chat` under `SpanCategory.ORCHESTRATOR` (`adapters/azure_openai/adapter.py:189-191`) **only if it received a tracer**. → a loop-level `LLM_CALL` span risks double-instrumentation **iff** the adapter tracer is also wired. **Resolution (this sprint): the loop is the single trace-tree owner — leave the adapter/executor/parser internal tracers NoOp (do NOT wire them); the loop wraps `chat_client.chat()`/`tool_executor.execute()` at the call boundary.** No double spans. (Nesting the existing internal spans under the loop tree is a future DRY refactor — §9.)
- **D9 — Tests**: `tests/integration/orchestrator_loop/test_observability_coverage.py:131-142` asserts span **membership only** (`agent_loop.run` / `tool.echo_tool` / 2× `output_parser.parse`), **no parent-child tree**. `RecordingTracer` at `:50-89` captures `{name, category.value, attributes}` in a flat list → extend it to capture parent linkage so a tree can be reconstructed.

**Net** (purely-additive, loop is single owner): add a `tracer` param to `build_real_llm_handler` + thread the router's real tracer into the loop (Tier 0 → root span real); in `loop.py` bind the root span `as child`, open a `TURN` span per turn (capture + thread its child ctx), and open `LLM_CALL`/`TOOL_EXEC`/`PROMPT_BUILD`/`COMPACTION`/`VERIFICATION`/`MEMORY_OP` spans around those operations (Tier 1, full set), each tagged via span name + `attributes["span_type"]` with the closest existing `SpanCategory`; set token/cost attributes on `LLM_CALL` (span-attribute only, never to the ledger); extend the `RecordingTracer` test to reconstruct + assert the tree (LOOP→TURN→operation), ERROR status on exception, and the real-tracer injection. Tier 2 (Jaeger export) → Area-C/DevOps; SpanStarted/SpanEnded→SSE → A-5.

---

## 1. Sprint Goal

Make the production chat loop emit a **reconstructable per-request trace tree**. Tier 0: add a `tracer` parameter to `build_real_llm_handler` and thread the router's real `OTelTracer` (`get_tracer`) into `AgentLoopImpl`, so the existing root span runs on a real tracer (not NoOp). Tier 1: in `loop.py`, bind the root span `as child` and thread the child context, open a `TURN` span around each turn (capturing + threading that turn's child context into its operations), and open `LLM_CALL` (around `chat_client.chat`), `TOOL_EXEC` (around each `tool_executor.execute`), `PROMPT_BUILD`, `COMPACTION`, `VERIFICATION`, and `MEMORY_OP` spans where those operations run — the **full span set** — each carrying 3-axis attributes (latency from span timing; tokens/cost on `LLM_CALL` from `ChatResponse.usage` + adapter pricing, **as span attributes only — never double-written to the cost ledger**). Resolve the SpanCategory naming drift by **keeping the by-category enum** and expressing span-type granularity via span name + `attributes["span_type"]` (recorded in `02.md §Naming Drift Note`). Prove it with an extended `RecordingTracer` test that reconstructs the tree (LOOP→TURN→operation, correct parent/child nesting), asserts ERROR span status on a raised exception, and asserts the loop's tracer is a real tracer (not NoOp) when built via `build_real_llm_handler`. The loop is the **single trace-tree owner** (adapter/executor/parser internal tracers stay NoOp — no double-instrumentation). **Tier 2 (real Jaeger/OTLP export) is deferred to Area-C/DevOps; the SpanStarted/SpanEnded→SSE sliver is A-5** (§9).

---

## 2. User Stories

- **US-1 (Tier 0 — inject a real tracer)** — As the production chat loop, I want `build_real_llm_handler` to accept a real tracer and pass it to `AgentLoopImpl`, so the root span (and every span I open) runs on a real `OTelTracer` instead of `NoOpTracer`. → `handler.py:164` add `tracer` param + pass to `AgentLoopImpl` (`:268-292`); `router.py` threads `get_tracer()` into `build_real_llm_handler`.
- **US-2 (Tier 1 — span tree + nesting fix)** — As an operator, I want a reconstructable trace tree per request (LOOP→TURN→LLM_CALL/TOOL_EXEC/PROMPT_BUILD/COMPACTION/VERIFICATION/MEMORY_OP) with correct parent/child nesting, so I can see where each turn spent time. → `loop.py` bind root `as child`; open TURN + the 6 operation spans; capture + thread each turn's child ctx; extend `category_span` (`helpers.py:40`) to accept `attributes` + `span_type`.
- **US-3 (per-span attributes + SpanCategory resolution)** — As an operator, I want each span tagged with `span_type` + 3-axis attributes (latency always; tokens/cost on LLM_CALL) WITHOUT changing the load-bearing `SpanCategory` enum and WITHOUT double-writing cost to the ledger. → span name + `attributes["span_type"]`; `LLM_CALL` carries `TokenUsage` + cost (span-attribute only); `02.md §Naming Drift Note` records the decision.
- **US-4 (validation)** — As a reviewer, I want a `RecordingTracer` test that reconstructs the full tree (root→N TURN→operation children, correct nesting), asserts ERROR status on a raised exception, and asserts `loop._tracer` is not a `NoOpTracer` when built via `build_real_llm_handler`, so the tracer is real (non-Potemkin) and the tree is correct — provable without Jaeger.

---

## 3. Technical Specifications

### 3.0 Architecture (loop = single trace-tree owner)

```
  router.py:144  tracer = Depends(get_tracer)  ──(NEW: also thread to handler)──┐
                                                                                 ▼
  build_real_llm_handler(handler.py:164, NEW tracer param) ──► AgentLoopImpl(tracer=real)  [Tier 0]
                                                                       │
                                                                       ▼  [Tier 1]
   LOOP (agent_loop.run, root, bound `as child` — loop.py:788)         span_type=LOOP, cat=ORCHESTRATOR
   └── TURN (per turn, child ctx captured + threaded)                  span_type=TURN, cat=ORCHESTRATOR
       ├── PROMPT_BUILD   (around prompt build call)                   span_type=PROMPT_BUILD, cat=PROMPT_BUILDER
       ├── MEMORY_OP      (around memory op, when it runs)             span_type=MEMORY_OP, cat=MEMORY
       ├── COMPACTION     (around compaction, when it runs)            span_type=COMPACTION, cat=CONTEXT_MGMT
       ├── LLM_CALL       (around chat_client.chat — loop.py:950)      span_type=LLM_CALL, cat=ORCHESTRATOR
       │                    attrs: model + TokenUsage(prompt/completion/cached/total) + cost_usd (span-only)
       ├── TOOL_EXEC (a)  (around tool_executor.execute — loop.py:1183) span_type=TOOL_EXEC, cat=TOOLS, attrs: tool, latency
       ├── TOOL_EXEC (b)  (parallel tools = sibling spans)
       └── VERIFICATION   (around verification, when it runs)          span_type=VERIFICATION, cat=VERIFICATION

   Adapter / executor / parser internal tracers: LEFT NoOp (NOT wired) → loop is single owner → no double spans (D8)
   Router recorders (SLA/cost/audit): UNCHANGED → remain billing/SLA source of truth (no double-write from spans)
   Tier 2 (OTLP→Jaeger export): DEFERRED to Area-C/DevOps   ·   SpanStarted/SpanEnded→SSE: A-5 (out of scope)
```

The loop owns the structural tree; spans wrap existing calls (additive, no control-flow change). Span granularity is expressed via span name + `attributes["span_type"]`; the `SpanCategory` enum is **unchanged** (each span tagged with the closest existing category). Cost/token live as **span attributes only** — the router recorders remain the billing/SLA persistence path (no span→ledger write). Every span uses `async with` so `end()` always fires (ERROR status + `record_exception` on a raised exception).

### 3.1 Tier 0 — real tracer injection (US-1) — `handler.py` + `router.py`
- `build_real_llm_handler` (`handler.py:164`): add `tracer: Tracer | None = None` param (mirror the prompt_builder/reducer dependency pattern at `handler.py:255-256` + `:283-285`); pass `tracer=tracer` into `AgentLoopImpl(...)` (`handler.py:268-292`).
- `router.py`: thread the already-resolved `get_tracer()` real `OTelTracer` (`router.py:144`) into the `build_real_llm_handler(...)` call (Day-1 confirms the exact call site + any `build_handler` indirection). No new `Depends` — reuse the existing one.
- DoD: an integration test builds via `build_real_llm_handler` and asserts `loop._tracer` is not a `NoOpTracer`; a run opens a real root span.

### 3.2 Tier 1 — span tree + nesting fix (US-2) — `loop.py` + `helpers.py`
- **Nesting fix** (`loop.py:788-792`): bind the root `start_span` `as root_ctx` (capture the yielded child) and thread `root_ctx` (not the outer `ctx`) downward.
- **TURN span**: wrap the per-turn `while` body in `async with start_span(name="agent_loop.turn", category=ORCHESTRATOR, trace_context=root_ctx, attributes={"span_type": "TURN", "turn": n}) as turn_ctx`; thread `turn_ctx` into that turn's operation spans.
- **Operation spans** (children of `turn_ctx`):
  - `LLM_CALL` around `chat_client.chat(...)` (`loop.py:950`) — `name="agent_loop.llm_call"`, cat=ORCHESTRATOR, attrs `{span_type: LLM_CALL, model, prompt_tokens, completion_tokens, cached_input_tokens, total_tokens, cost_usd}` (tokens from `ChatResponse.usage`; cost via adapter pricing — span-attribute ONLY).
  - `TOOL_EXEC` around each `tool_executor.execute(...)` (`loop.py:1183`) — `name=f"agent_loop.tool.{name}"`, cat=TOOLS, attrs `{span_type: TOOL_EXEC, tool, latency_ms}` (latency from span timing). Parallel tools = sibling spans under the same turn.
  - `PROMPT_BUILD` / `COMPACTION` / `MEMORY_OP` / `VERIFICATION` around those operations (Day-1 locates the exact call sites via the existing `trace_context=ctx` threading at `loop.py:847/901/939/972/1141/...`) — cat = PROMPT_BUILDER / CONTEXT_MGMT / MEMORY / VERIFICATION respectively; open only when the operation actually runs that turn.
- **Helper** (`helpers.py:40`): extend `category_span` to accept optional `attributes: dict | None = None` + `span_type: str | None = None` (folds `span_type` into attributes), OR have the loop call the ABC `start_span` directly (which already accepts `attributes`). Decision: extend `category_span` (additive optional params → existing call sites unaffected) so all loop spans use one consistent path.
- **Exception safety**: all spans via `async with` → `end()` guaranteed; on a raised exception set span status ERROR + `record_exception` (Day-1 confirms the ABC's error API).

### 3.3 SpanCategory drift resolution (US-3) — `02.md §Naming Drift Note`
- **Decision (user-confirmed)**: KEEP the by-category `SpanCategory` enum (load-bearing in `metrics.py` mapping + 8 sites — renaming is high blast-radius, no upside). Express span-type granularity (LOOP/TURN/LLM_CALL/TOOL_EXEC/PROMPT_BUILD/COMPACTION/VERIFICATION/MEMORY_OP) via **span name + `attributes["span_type"]`** (already the convention: `tool.{name}`, `output_parser.parse`). Record this resolution in `02-architecture-design.md §Naming Drift Note`; note it in `01-eleven-categories-spec.md §範疇12` (loop span tree shipped Tier 0+1; Tier 2 deferred).

### 3.4 Lint / neutrality / doc single-source
- `check_llm_sdk_leak` 0 (the loop edits are tracer wraps — provider-free; no `import openai/anthropic`; cost via the neutral adapter pricing ABC). All 10 V2 lints green; **no codegen change** (SpanStarted/SpanEnded→SSE is A-5); **no FE change**; **no new wire-type**.
- **Doc single-source**: `17.md §Contract 12` UNCHANGED (the SpanStarted/SpanEnded `LoopEvent` subclasses it defines are A-5, not built here — single-source preserved). `02.md §Naming Drift Note` += the resolution; `01.md §範疇12` += the Tier 0+1 shipped note.
- **Double-instrumentation guard**: adapter/executor/parser internal tracers stay NoOp (not wired) — the loop is the single owner (D8). **Double-counting guard**: span token/cost = tree attributes only; the router recorders (`router.py:388/413/478`) remain the billing/SLA persistence — no span→ledger write.

### 3.5 Validation (US-4)
- **Integration (Tier 0)**: build via `build_real_llm_handler(... tracer=real)`; assert `loop._tracer` is not `NoOpTracer`; a run opens a real `agent_loop.run` root span.
- **Integration (Tier 1, RecordingTracer)**: extend `RecordingTracer` (`test_observability_coverage.py:50-89`) to capture parent linkage (span_id / parent ctx); a multi-turn run reconstructs LOOP→N×TURN→{LLM_CALL, TOOL_EXEC×k, PROMPT_BUILD, …} with correct parent/child nesting; `LLM_CALL` carries token attributes; `TOOL_EXEC` carries latency; a raised exception sets span status ERROR. (No Jaeger / collector needed — in-memory recording.)
- **Overhead sanity**: a coarse assertion that span wrapping doesn't materially change turn count / behavior (SLO < 5% is a Tier-2/real-export concern; with NoOp/recording exporter the per-span cost is negligible — note, don't over-engineer).
- **No regression**: all existing tests green; `test_observability_coverage.py` membership assertions still pass (now under the real tree).

---

## 4. File Change List

| File | Change |
|------|--------|
| `backend/src/api/v1/chat/handler.py` | **EDIT** (`:164`/`:268-292`) — add `tracer: Tracer \| None = None` to `build_real_llm_handler`; pass `tracer=tracer` into `AgentLoopImpl` (Tier 0, US-1) |
| `backend/src/api/v1/chat/router.py` | **EDIT** — thread the existing `get_tracer()` real tracer (`:144`) into the `build_real_llm_handler(...)` call (Tier 0, US-1) |
| `backend/src/agent_harness/orchestrator_loop/loop.py` | **EDIT** — bind root span `as child` (`:788-792`); open TURN span per turn (capture+thread child ctx); LLM_CALL (`:950`, token/cost attrs) + TOOL_EXEC (`:1183`, latency) + PROMPT_BUILD/COMPACTION/MEMORY_OP/VERIFICATION spans; span_type attributes (Tier 1, US-2/US-3) |
| `backend/src/agent_harness/observability/helpers.py` | **EDIT** (`:40`) — extend `category_span` with optional `attributes` + `span_type` (US-2) |
| `backend/tests/integration/orchestrator_loop/test_observability_coverage.py` | **EXTEND** — RecordingTracer captures parent linkage; assert LOOP→TURN→operation tree + nesting + ERROR status + token/latency attrs (US-4) |
| `backend/tests/integration/...` (chat/handler) | **NEW/extend** — Tier 0 injection test (`loop._tracer` not NoOp via `build_real_llm_handler`) (US-4) |
| `docs/03-implementation/agent-harness-planning/02-architecture-design.md` | **EDIT** §Naming Drift Note — record SpanCategory resolution (keep enum + span-type via name/attributes) (US-3) |
| `docs/03-implementation/agent-harness-planning/01-eleven-categories-spec.md` | **EDIT** §範疇12 — loop span tree shipped (Tier 0+1); Tier 2 (Jaeger) deferred; SpanStarted/SpanEnded→SSE = A-5 |
| `claudedocs/4-changes/feature-changes/CHANGE-039-loop-tracer.md` | **NEW** — change record |

**No FE change** (Vitest unchanged). **No new wire-type / no codegen / no SSE change** (SpanStarted/SpanEnded→SSE = A-5). **No adapter/executor/parser tracer wiring** (loop is single owner — D8). **No `17.md` Contract 12 change** (single-source preserved). **No span→cost-ledger write** (router recorders remain billing source of truth).

---

## 5. Acceptance Criteria

- **Tier 0**: `build_real_llm_handler` accepts a `tracer` param and injects it into `AgentLoopImpl`; on the real chat path `loop._tracer` is NOT a `NoOpTracer`; a run opens a real root `agent_loop.run` span.
- **Tier 1**: every turn opens a `TURN` span; each LLM call opens an `LLM_CALL` span carrying `TokenUsage` (prompt/completion/cached/total) + cost attributes; each tool opens a `TOOL_EXEC` span with latency; `PROMPT_BUILD`/`COMPACTION`/`VERIFICATION`/`MEMORY_OP` spans open where those operations run (full set); the root is bound `as child` and each turn's child ctx is threaded → a `RecordingTracer` test reconstructs the tree (LOOP→N×TURN→operation children) with correct parent/child nesting; span status is ERROR on a raised exception.
- **SpanCategory**: enum UNCHANGED; span-type expressed via span name + `attributes["span_type"]`; `02.md §Naming Drift Note` updated.
- **No double-instrumentation** (adapter/executor/parser tracers stay NoOp); **no double-counting** (span cost = attribute only; router recorders unchanged).
- All existing tests green (incl. `test_observability_coverage.py` membership now under the real tree); `mypy --strict src/` 0; 10/10 V2 lints (LLM SDK leak 0); Vitest unchanged (no FE). **Tier 2 (Jaeger export) explicitly deferred (Area-C/DevOps); SpanStarted/SpanEnded→SSE = A-5.**

---

## 6. Deliverables

- [ ] Tier 0: `build_real_llm_handler` `tracer` param + `AgentLoopImpl` injection + router thread (US-1)
- [ ] Tier 1: root `as child` + TURN span + LLM_CALL/TOOL_EXEC/PROMPT_BUILD/COMPACTION/VERIFICATION/MEMORY_OP spans + ctx threading + `helpers.category_span` extend (US-2)
- [ ] Per-span attributes (span_type + token/cost on LLM_CALL, span-only) + SpanCategory decision recorded in `02.md` (US-3)
- [ ] Tests: RecordingTracer tree reconstruction + nesting + ERROR status + Tier-0 injection test (US-4)
- [ ] `01.md §範疇12` note; CHANGE-039 + progress.md + retrospective.md

---

## 7. Workload Calibration

Scope class: **`cat12-loop-tracer-additive` (0.60, NEW — pending validation)** — a backend cross-cutting observability sprint: purely-additive `loop.py` hot-path span wraps (no control-flow change) + handler/router tracer plumbing + helper extend + RecordingTracer tree tests + doc drift-note. Distinct from `medium-backend` CRUD (no new table/migration/repo) and from greenfield component creation (wraps existing calls). Mid-high band 0.60 reflects loop hot-path risk (async span lifecycle + ctx threading) offset by the purely-additive shape. **Agent-delegated: yes** (staged: Stage-1 Tier 0 + nesting fix + TURN/LLM_CALL/TOOL_EXEC; Stage-2 PROMPT_BUILD/COMPACTION/VERIFICATION/MEMORY_OP + tests; parent independent re-verify each — reads loop.py diffs for span lifecycle + ctx threading correctness). `agent_factor` **`mechanical-greenfield-design-decisions` 0.65** (genuine design: span tree structure, span_type attribute scheme, ctx-threading fix, double-instrumentation/double-counting guards; heavy pattern-mirror of the existing executor/parser span style).

> Bottom-up est ~15 hr → class-calibrated commit ~9 hr (mult 0.60) → agent-adjusted commit ~5.9 hr (agent_factor 0.65).

Caveat (carried 57.63-57.70): agent-delegated sprints have no clean wall-clock (`AD-Calibration-AgentDelegated-WallClock-Measure`; would be **9th consecutive**). The NEW `cat12-loop-tracer-additive` class is a single unvalidated point — record caveated; do NOT generalize on 1 point. If the full span set (PROMPT_BUILD/COMPACTION/VERIFICATION/MEMORY_OP) proves to involve operations that don't cleanly bracket a single call (e.g. interleaved), defer the messy ones + re-confirm scope.

---

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| **Loop hot-path edits** (Tier 1) | Additive wraps (no control-flow change); all spans via `async with` → `end()` guaranteed even on exception (set ERROR status + `record_exception`); parent re-verifies span lifecycle on the loop.py diff |
| **`as child` nesting** | Capture the `start_span` yield (`as ctx`) for root + each TURN; thread the **turn's** child ctx (not root) into that turn's operation spans; the RecordingTracer test asserts parent/child linkage (Risk Class — was the original bug, D1) |
| **Adapter `llm_chat` double-instrumentation** (D8) | Loop is the single owner this sprint — adapter/executor/parser internal tracers stay NoOp (NOT wired); the loop wraps `chat_client.chat`/`tool_executor.execute` at the call boundary → no duplicate spans |
| **Cost double-counting** (§4.5 of analysis) | Span token/cost = tree attributes ONLY; the router recorders (`router.py:388/413/478`) remain the billing/SLA persistence path — no span→ledger write |
| **SpanCategory blast radius** | KEEP the enum (load-bearing: `metrics.py` map + 8 sites); express span-type via name + `attributes["span_type"]` (zero blast radius; user-confirmed); `category_span` gets optional additive params only |
| **`category_span` signature change** | New `attributes`/`span_type` params default `None` → existing call sites unaffected; Day-1 greps existing `category_span(` callers to confirm |
| **Operation span call sites** (PROMPT_BUILD/COMPACTION/MEMORY_OP/VERIFICATION) | Day-1 locates each via the existing `trace_context=` threading (`loop.py:847/901/939/972/1141/...`); open a span only when the operation actually runs that turn (no empty spans) |
| **Test isolation** (real tracer path) | RecordingTracer is in-memory (no Jaeger/collector); Tier 0 injection test uses the existing handler-build fixtures; no new module-level singleton (Risk Class C) |
| **Performance overhead** | SLO < 5% is a Tier-2/real-export concern; with NoOp/recording exporter per-span cost is negligible — coarse sanity only, don't over-engineer |

---

## 9. Out of Scope (this sprint; carryover)

- **Tier 2 — real Jaeger/OTLP export** (stand up the OTel collector + Jaeger + `OTEL_*` env so the tree is visible in Jaeger; 100% turn-coverage + < 5% overhead measured against a live exporter) → **Area-C / DevOps** (analysis §3 Tier 2, §6).
- **`SpanStarted` / `SpanEnded` / `MetricRecorded` as `LoopEvent` subclasses → SSE** (observability events to the frontend) → **A-5** (shared sliver; `17.md §4.1`). This sprint does NOT add wire-types / codegen.
- **Nesting the existing internal spans** (adapter `llm_chat`, executor `tool.{name}`, parser `output_parser.parse`) under the loop tree by wiring their real tracers + threading ctx — a future DRY refactor; this sprint keeps the loop the single owner to avoid double-instrumentation.
- **Per-span 3-axis metrics → `MetricsRecorder` aggregation** beyond span attributes — keep span attributes this sprint; MetricsRecorder integration as a follow-up if needed.
- **Cross-process subagent span linkage** (`parent_span_id` continuity) — relevant once A-3 subagents are fully live; design-ready, not wired here.
- **Other Area-A**: A-5c (diagnostic Inspector UI), A-6 (frontend real-data wiring), and the **FE `/subagents` page wiring to the agent catalog** (57.70 carryover) → future sprint.
