# CHANGE-039: A-4 Loop Tracer — Real Tracer Injection + Loop-Internal Span Tree (Tier 0 + Tier 1)

**Date**: 2026-06-02
**Sprint**: 57.71
**Scope**: 範疇 12 (Observability / Tracing) — loop-internal span tree + real tracer injection; touches Cat 1 (loop hot-path wraps) + chat handler/router (tracer plumbing)

## Change Summary

Closed `AD-Cat12-LoopTracer` (Area-A item 4): the production chat loop now emits a **reconstructable per-request trace tree** instead of a single no-op'd root span.

- **Tier 0** — `build_real_llm_handler` (+ the `build_handler` dispatcher) gained a `tracer` param; `router.py` threads its existing `Depends(get_tracer)` real `OTelTracer` into the loop. The loop's tracer is now real on the chat path (was `NoOpTracer`).
- **Tier 1** — `loop.py` binds the root span `as child` (fixing the D1 nesting bug) and opens a per-turn span tree: `TURN` per turn, `LLM_CALL` (token attrs) + `TOOL_EXEC` (per execute) under each TURN, `PROMPT_BUILD` (when a prompt_builder is injected), `COMPACTION` (when a compactor is injected, nested under root since it runs pre-TURN). Span-type granularity is expressed via span name + `attributes["span_type"]`; the `SpanCategory` enum is unchanged.
- The loop is the **single trace-tree owner** — the adapter/executor/parser internal tracers stay NoOp (not wired), eliminating the adapter `llm_chat` double-instrumentation risk. Span token/cost stay span attributes only — never written to the cost ledger (router recorders remain the billing/SLA source of truth).

## Change Reason

The loop opened only a single root span, on a `NoOpTracer` (handler never injected a real one), and that span was not bound `as child` so even nested spans would be flat siblings — no reconstructable trace tree existed in production (Cat 12 was Potemkin-adjacent, AP-4). A-4 was scoped as "the most purely-additive Area-A item" (analysis `cat12-loop-tracer-analysis-20260531.md`): wrap existing operations in spans, no control-flow change, no cross-category dependency.

## Detailed Changes

- `agent_harness/orchestrator_loop/loop.py` — root span `as root_ctx` + `span_type=LOOP`; TURN span (`trace_context=root_ctx`, opened after pre-LLM terminators, `as turn_ctx`); LLM_CALL span (`trace_context=turn_ctx`, token attrs written post-response into a shared dict); TOOL_EXEC span per `tool_executor.execute` (`trace_context=turn_ctx`); PROMPT_BUILD span (gated by prompt_builder); COMPACTION span (gated by compactor, `trace_context=root_ctx`). All via `async with` → ERROR status + record_exception fire automatically via the tracer's `_span_cm` on a propagating exception.
- `agent_harness/observability/helpers.py` — `category_span` gained optional `attributes` + `span_type` (additive; existing callers unaffected).
- `api/v1/chat/handler.py` — `build_real_llm_handler` + `build_handler` gained a `tracer` param → `AgentLoopImpl(tracer=)`.
- `api/v1/chat/router.py` — threaded the existing `Depends(get_tracer)` real tracer into `build_handler`.
- `02-architecture-design.md §Naming Drift Note` — recorded the SpanCategory resolution. `01-eleven-categories-spec.md §範疇12` — Tier 0+1 shipped note + deferral list.

## Deferred (carryover)

- **Tier 2** — real OTLP→Jaeger export (collector + `OTEL_*` env) → Area-C / DevOps.
- **`SpanStarted`/`SpanEnded`→SSE** (observability events to the frontend, `17.md §4.1`) → A-5 (this sprint added no wire-type/codegen).
- **VERIFICATION + MEMORY_OP loop-level spans** — no clean loop-level call site: verification is an outer wrapper (`verification/correction_loop.py:run_with_verification`) whose verifiers own their own `verifier.{name}` spans; memory injection is inside `prompt_builder.build()` (covered by PROMPT_BUILD) or via tools (covered by TOOL_EXEC). Forcing a span = AP-4 Potemkin → deferred. Wiring the existing internal spans (adapter `llm_chat` / executor `tool.{name}` / verifier spans) into the tree is the "nest existing spans" DRY refactor.
- **Token attrs in OTel** — written post-response into a shared dict (RecordingTracer sees them by reference; `OTelTracer` copies attrs at span-open) → full per-token OTel export awaits a Tracer-ABC set-attribute API (Tier-2-adjacent). `cost_usd` deferred (no adapter-pricing coupling; never feeds the ledger).

## Verification

- `pytest tests/unit tests/integration` → **2057 passed / 4 skipped** (= 57.70 baseline 2049 + 8 new: 6 tree/edge/ERROR tests + 2 Tier-0 injection tests).
- `mypy src/` 0 / 329; `run_all.py` 10/10 (LLM SDK leak 0); black 605 unchanged + isort/flake8 0.
- Decisive test: `test_reconstructs_loop_turn_operation_tree_with_correct_nesting` asserts TURN.parent==LOOP and LLM_CALL/TOOL_EXEC.parent ∈ TURN ids (≠ root LOOP) — the D1 nesting fix. `test_raised_exception_sets_error_span_status` asserts ERROR propagation.

## Impact

Backend-only (Cat 12 + Cat 1 + chat handler/router). No FE change (Vitest unchanged), no new wire-type/codegen, no DB/migration, no `17.md §Contract 12` change (SpanStarted/SpanEnded→SSE = A-5). No behavior change for the NoOp default path. PR pending.
