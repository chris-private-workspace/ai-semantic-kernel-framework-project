# A-4 Deep Analysis: Cat 12 Observability — Loop-Internal Tracer

**Purpose**: Single-point deep analysis of why the production loop emits no internal trace tree (per-turn / per-tool / per-LLM-call spans), the triple nature of the gap, and why this is the most purely-additive Area-A item. Analysis only.
**Category / Scope**: 範疇 12 (Observability / Tracing, cross-cutting) / Phase 57+ (post Sprint 57.63)
**Created**: 2026-05-31
**Last Modified**: 2026-05-31
**Status**: Active (analysis input for a future sprint)

> **Modification History**
> - 2026-05-31: Correction pass — fixed line refs (root span `loop.py:779`, fallback `:226`), SpanCategory enum naming-drift (code by-category 13 vs spec by-span-type), and SpanStarted/SpanEnded definition (plan intends LoopEvent subclasses → partial A-5 overlap, not cleanly separate)
> - 2026-05-31: Initial creation — A-4 of the Area-A wiring-gap deep-analysis series; 2-agent parallel audit

> **Related**
> - `integration-progress-20260531.md` — parent integration snapshot (Area A item 4 / B-area overlap)
> - `01-eleven-categories-spec.md §範疇12` / `17-cross-category-interfaces.md §Contract 12 + §4.1 + §7.2` / `06-phase-roadmap.md §Phase 49.4` / `02-architecture-design.md §Naming Drift Note` / `13-deployment-and-devops.md §observability stack`

---

## 0. Headline

`AD-Cat12-LoopTracer` is actually a **triple gap**: (1) the loop body opens **only a single root span** (`agent_loop.run`) — no per-turn / per-LLM-call child spans, so there is no reconstructable trace tree; (2) the handler **never injects a real tracer**, so even that root span runs on a `NoOpTracer` in production; (3) the **OTel exporter is env-gated** — configured in code (`setup_opentelemetry`) but only exports when the Jaeger collector + `OTEL_*` env are present. The good news: Cat 12 is the **most purely-additive** Area-A item — it requires **no control-flow change** and **no other category to be live**; it only *wraps* existing operations in spans. Router-layer recorders (SLA / cost / audit) are genuinely live and independent of the span tree.

---

## 1. Current state — triple gap (with what IS live)

| Component | Status | Evidence |
|-----------|--------|----------|
| `Tracer` ABC / `NoOpTracer` / `OTelTracer` | ✅ built | `observability/_abc.py:32`; `tracer.py:57` (NoOp, inert); `tracer.py:122` (OTel, real) |
| `MetricsRecorder` / `MetricEvent` (3-axis: latency/token/cost) | ✅ built | `_contracts/observability.py:77`; `metrics.py` |
| `SpanCategory` enum | ✅ defined (⚠️ **naming drift**) | `_contracts/observability.py:41` — code enum is **by-category** (13: ORCHESTRATOR/TOOLS/MEMORY/CONTEXT_MGMT/PROMPT_BUILDER/OUTPUT_PARSER/STATE_MGMT/ERROR_HANDLING/GUARDRAILS/VERIFICATION/SUBAGENT/OBSERVABILITY/HITL); the spec intends **by-span-type** (LOOP/TURN/LLM_CALL/TOOL_EXEC…) — acknowledged drift (`02.md §Naming Drift Note`) |
| `TraceContext` + `create_root()` | ✅ built | `_contracts/observability.py:59` |
| trace_context threaded to downstream ABCs (chat/tool/compactor/prompt_builder/reducer/checkpointer/guardrail/hitl) | ✅ plumbing exists | `loop.py:847/901/939/972/1141/1373/1381` pass `trace_context=ctx` |
| Loop opens **root span** | ⚠️ yes (one only), no-op'd in prod | `loop.py:779-783` — single `start_span(name="agent_loop.run", category=ORCHESTRATOR)` |
| Loop opens **per-turn / per-LLM-call spans** | ❌ **absent** | only one `start_span` in the whole loop body; no TURN / LLM_CALL spans. (TOOL + OUTPUT_PARSER spans are opened by `ToolExecutorImpl` / `OutputParserImpl` via their OWN injected tracers — separate instances, also NoOp in prod unless wired) |
| Per-turn `ctx.child()` nesting | ❌ inconsistent | root `ctx` (not a child) threaded to all calls; the `start_span` child ctx is not captured (`async with … :` with no `as child`) → downstream gets the **root** ctx |
| **Real tracer injected into `AgentLoopImpl`** | ❌ **no** | `handler.py` passes zero `tracer=` → `self._tracer = tracer or NoOpTracer()` (`loop.py:226`). Router's real `OTelTracer` (`router.py:140`, `Depends(get_tracer)`) goes only to `BusinessServiceFactory` (`router.py:194`), **never** to the loop ctor |
| OTel SDK + exporter | ✅ configured / ⚠️ env-gated | `platform_layer/observability/setup.py:59` `setup_opentelemetry()` wires OTLP→Jaeger + Prometheus; active only with collector + `OTEL_*` env |
| Router-layer recorders (SLA / cost / audit / DB observers) | ✅ **live** | `router.py:388` SLA, `:413/478` cost, `:444` audit, Sprint 57.7 session/tool_call rows — event-driven, independent of spans |
| Test proving a loop span tree | ⚠️ partial | `tests/integration/orchestrator_loop/test_observability_coverage.py:93` asserts the single `agent_loop.run` span + tool/parser spans (via directly-injected `RecordingTracer`); **no** assertion of per-turn / per-LLM-call spans |

**The two tracer instances don't meet**: `router.py:140` resolves a **real** `OTelTracer` via `Depends(get_tracer)` and threads it into `BusinessServiceFactory` (`router.py:194`) — so *business services* get a real tracer — but that instance is **never passed into `build_real_llm_handler` / `AgentLoopImpl`**. The loop's tracer defaults to `NoOpTracer`. (Likewise the tool executor / output parser in the chat path are constructed without a real tracer, so their span capability is also NoOp in production.)

---

## 2. Target design recap (from `01.md §範疇12`, `17.md §Contract 12 + §4.1`)

A **reconstructable trace tree per chat request** (spec's by-span-type intent):
```
LOOP (root, per request)
├── TURN (turn 1)
│   ├── PROMPT_BUILD
│   ├── LLM_CALL  {model, input_tokens, output_tokens, cost_usd}
│   ├── TOOL_EXEC (a)   ← parallel tools = sibling spans
│   └── TOOL_EXEC (b)
├── TURN (turn 2)
│   ├── LLM_CALL
│   └── MEMORY_OP / COMPACTION / VERIFICATION / GUARDRAIL (when those run)
└── ... ; SUBAGENT / HITL_WAIT / CHECKPOINT as parallel children of LOOP
```
- **Per-span 3-axis metrics** (latency / token / cost) recorded **inside the loop**, per LLM-call / per-tool, aggregated to request level — NOT only request-level aggregate.
- **trace_context through every ABC** (`17.md §7.2`, "penetrate all") with parent/child nesting; subagent root span links to the dispatching span via `parent_span_id` (cross-process continuity).
- Acceptance: **"100% turn 有對應 span"** + **"Jaeger 可重建完整 trace"** + per-span metrics + correct nesting + span status OK/ERROR on exceptions + tracer overhead < 5%.
- **Note (corrected)**: the plan (`17.md §4.1`) actually intends `SpanStarted` / `SpanEnded` / `MetricRecorded` as **first-class `LoopEvent` subclasses** (so they could also reach the frontend via SSE) **in addition to** the OTel span tree (→ Jaeger). **Current code has neither** the per-turn OTel spans **nor** these event dataclasses. So Cat 12's *core* channel is OTel→Jaeger, but the `SpanStarted`/`SpanEnded`→SSE slice **overlaps A-5** — A-4 and A-5 are *mostly*, not cleanly, separate.
- Cat 12 was scoped in **Phase 49.4** to ship the *trace_context plumbing + ABCs early* (cross-cutting); the *loop-internal span tree* is the remaining Level-4 completion work.

---

## 3. The gap, in three tiers

### Tier 0 — inject a real tracer (trivial; same 57.63 inject pattern)
- `AgentLoopImpl` already has the `tracer` ctor param. Pass a real `OTelTracer` (new `make_chat_tracer()` factory, or reuse the router's `get_tracer()` instance) into `build_real_llm_handler` (and into the chat path's tool executor / output parser). → the existing root span (`loop.py:779`) becomes real. Minutes of work, but a flat single-span tree until Tier 1.

### Tier 1 — open the child span tree in loop.py (the substance; additive loop.py edits)
- Wrap the per-turn `while` body in a `TURN` span (capture `ctx.child()` and thread it down — fixing the current "root ctx everywhere" bug); wrap `chat_client.chat(...)` in an `LLM_CALL` span; wrap each `tool_executor.execute(...)` in a `TOOL_EXEC` span; add `PROMPT_BUILD`/`COMPACTION`/`VERIFICATION`/`MEMORY_OP` spans where those operations run.
- Set 3-axis attributes per span (latency from span timing; tokens/cost on `LLM_CALL` from the `ChatResponse`).
- **Resolve the SpanCategory naming drift** (`02.md §Naming Drift Note`): decide whether to keep the code's by-category enum or move to the spec's by-span-type set; the tree above needs span-type granularity (TURN / LLM_CALL / TOOL_EXEC) that the current by-category enum does not express.
- **These are additive edits (wrap existing calls), NOT control-flow changes** — distinct from A-3b HANDOFF which rewires the loop. Lower risk, but still loop hot-path edits requiring correct async span lifecycle (always `end()`, even on exception → `ERROR` status).

### Tier 2 — make the tree reach Jaeger (ops / Area-C overlap)
- The OTel TracerProvider + OTLP exporter is already coded (`setup_opentelemetry`); it needs the collector/Jaeger **running** + `OTEL_*` env (`13-deployment`). Without it, spans are created but exported nowhere. This is a DevOps concern (overlaps Area C), and **not needed to verify Tier 1 in tests** (use an in-memory / recording span exporter — the existing `RecordingTracer` test pattern).

---

## 4. Key findings / distinctions

1. **Most purely-additive Area-A item**: Cat 12 needs **no other category to be live** (it wraps whatever IS active) and makes **no control-flow change** (wrap, not rewire). Opposite risk end from A-3b (HANDOFF).
2. **Cheapest sub-win is real but shallow**: Tier 0 (inject real tracer) gives a root span per request for near-zero effort, but a flat tree. The value is in Tier 1 (child spans).
3. **Testable without Jaeger**: the existing `RecordingTracer` pattern (`test_observability_coverage.py`) already proves the model — extend it to assert the full tree (root → TURN → LLM_CALL/TOOL_EXEC). No collector needed in CI.
4. **A-4 ≈ mostly-but-not-cleanly separate from A-5**: Cat 12's *core* is the OTel span tree → Jaeger (distinct from SSE). BUT the plan (`17.md §4.1`) also defines `SpanStarted`/`SpanEnded`/`MetricRecorded` as `LoopEvent` subclasses intended for the SSE stream — currently unbuilt. So that observability-events-over-SSE sliver overlaps A-5. Scope A-4 as the OTel tree; treat SpanStarted/SpanEnded→SSE as a shared sliver with A-5.
5. **Double-counting risk**: router-layer recorders already persist cost/SLA from the SSE event stream (`router.py:388/413/478`). If Tier 1 also records per-span cost, keep roles distinct: **span metrics = observability tree (Jaeger)**; **router recorders = billing/SLA persistence (DB/CostLedger)**. Do not let span-level cost double-write to the ledger.

---

## 5. Risks / open research questions

1. **loop.py hot-path edits (Tier 1)**: additive (wrap) but must handle async span context + guaranteed `end()` on exception (`record_exception` + `ERROR` status). Lower risk than A-3b, still loop churn.
2. **`ctx.child()` nesting bug**: today the `start_span` child ctx is discarded and the **root** ctx is threaded everywhere → even if more spans were opened they'd be flat siblings. Must capture and thread the child ctx per turn — this is a prerequisite for a real tree, not just an add.
3. **SpanCategory naming drift** (`02.md`): code by-category vs spec by-span-type — must be resolved to express TURN/LLM_CALL/TOOL_EXEC granularity.
4. **OTel exporter env-gated (Tier 2)**: spans go nowhere without a running collector — "live in code" ≠ "visible in Jaeger". DevOps/Area-C dependency; Tier 1 verifiable via RecordingTracer only.
5. **Performance overhead** of per-turn/tool spans on the hot path — plan SLO is < 5%; measure.
6. **Double-counting** cost/metrics between span attributes and router recorders (see §4.5) — reconcile ownership.
7. **Cross-process subagent span linkage** — relevant once A-3 subagents are live; design the `parent_span_id` linkage now so it's ready.

---

## 6. Recommendation

- **A-4 makes a clean standalone sprint**: **Tier 0 + Tier 1** (inject real tracer + add the child span tree in loop.py + fix the ctx.child nesting + resolve the SpanCategory drift + RecordingTracer tests asserting LOOP→TURN→LLM_CALL/TOOL_EXEC). Purely additive, no control-flow change, no cross-category dependency, fully testable without Jaeger.
- **Defer Tier 2 (real Jaeger export) to Area-C / DevOps** — stand up the OTel collector + Jaeger when the deployment stack is hardened; it's an ops config + env, not a code gap.
- **Scope A-4 as the OTel tree; carve the SpanStarted/SpanEnded→SSE sliver into A-5** (shared concern).
- **Sequencing**: A-4 is independent — runnable anytime, parallel with or after A-1/A-2/A-3a. A natural ordering is *after* A-1/A-2/A-3a so the new spans (MEMORY_OP, PROMPT_BUILD, SUBAGENT) have live operations to wrap — but it's not a hard dependency.

---

## 7. Definition-of-done signals (for the eventual sprint)

- **Tier 0**: `build_real_llm_handler` injects a real `OTelTracer`; an integration test asserts `loop._tracer` is not a `NoOpTracer` and a run opens a root span.
- **Tier 1**: every `real_llm` turn opens a `TURN` span; each LLM call opens an `LLM_CALL` span carrying token/cost attributes; each tool opens a `TOOL_EXEC` span with latency; a `RecordingTracer`/in-memory-exporter test reconstructs the tree (root → N TURN → LLM_CALL/TOOL_EXEC children) with correct parent/child nesting; span status set to ERROR on a raised exception; SpanCategory drift resolved.
- **Tier 2** (Area C): OTLP exporter live; a real chat request produces a reconstructable trace tree in Jaeger; 100% turn span coverage measured; tracer overhead < 5%.

---

## 8. Method note

Synthesized from a 2-agent parallel read-only audit (current-code-ground-truth + planning-target-spec) on main `526be549` (Sprint 57.63 merged). Corrected after cross-checking agent findings (line refs, enum naming, event-class definition). Effort/tier framing are judgement estimates, not commitments.
