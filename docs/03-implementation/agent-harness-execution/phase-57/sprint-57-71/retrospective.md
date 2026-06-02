# Sprint 57.71 Retrospective — A-4 Loop Tracer (Tier 0 + Tier 1, full span set)

**Closed**: 2026-06-02
**Plan**: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-71-plan.md`
**Branch**: `feature/sprint-57-71-loop-tracer` (from `48e19846`)

---

## Q1 — What was delivered?

The production chat loop now emits a reconstructable per-request trace tree (closing `AD-Cat12-LoopTracer`, Area-A item 4). **Tier 0**: `build_real_llm_handler` + `build_handler` gained a `tracer` param; `router.py` threads its real `OTelTracer` into the loop (was NoOp on the chat path). **Tier 1**: `loop.py` binds the root span `as child` (D1 nesting fix) and opens `TURN` per turn + `LLM_CALL`/`TOOL_EXEC`/`PROMPT_BUILD`/`COMPACTION` spans, span-type via span name + `attributes["span_type"]` (SpanCategory enum unchanged). The loop is the single trace-tree owner (adapter/executor/parser tracers stay NoOp — no double-instrumentation); span token/cost stay attributes only (no ledger double-write). **VERIFICATION + MEMORY_OP deferred** (no clean loop-level call site). Tier 2 (Jaeger export) → Area-C; SpanStarted/SpanEnded→SSE → A-5.

## Q2 — Estimate accuracy / calibration

- Scope class **`cat12-loop-tracer-additive` (0.60, NEW — 1 data point)**; `agent_factor` **`mechanical-greenfield-design-decisions` 0.65**; **Agent-delegated: yes** (2 staged `code-implementer` — Stage-1 Tier 0 + nesting fix + TURN/LLM_CALL/TOOL_EXEC; Stage-2 PROMPT_BUILD/COMPACTION + tree tests — + parent independent re-verify each; closeout parent-authored).
- Plan: bottom-up ~15 hr → class-calibrated ~9 hr (0.60) → agent-adjusted ~5.9 hr (0.65).
- **No clean wall-clock** (agent-delegated, multi-tool session) → **9th consecutive** agent-delegated no-clean-measure (57.63→57.71) → reinforces `AD-Calibration-AgentDelegated-WallClock-Measure`. CAVEATED; the NEW `cat12-loop-tracer-additive` 0.60 is a single unvalidated point — do NOT generalize. `agent_factor` 0.65 kept.

## Q3 — What went well?

- **Day-0 researcher ground-truth corrected the analysis's drifted line refs cheaply** — the A-4 analysis was written at 57.63; a single researcher pass re-anchored every file:line (root :788, fallback :235, handler :164, wrap points :950/:1183) AND surfaced the critical D8 finding (the adapter already emits `llm_chat` under ORCHESTRATOR) before any code — which drove the "loop is single owner, leave adapter/executor/parser tracers NoOp" design that sidesteps double-instrumentation by construction.
- **The 472-line TURN-span re-indent landed clean** — the agent did it programmatically + `py_compile`-verified; the parent confirmed the span boundaries by reading the 4 structural regions, and the full integration suite (multi-turn + tool) passing was decisive functional proof.
- **The tree-reconstruction test is the right DoD** — `test_reconstructs_loop_turn_operation_tree_with_correct_nesting` asserts TURN.parent==LOOP and LLM_CALL/TOOL_EXEC.parent ∈ TURN ids (≠ root) — directly proving the D1 nesting bug is fixed, not just that spans exist. Plus ERROR-status + zero/multi-tool + NoOp-default edge tests.

## Q4 — What to improve / lessons

- **"Full span set" had two members with no loop-level home** — the user chose the full set (8 span types), but Stage-2 found VERIFICATION is an *outer wrapper* around `agent_loop.run()` (verifiers own their own spans) and MEMORY_OP runs *inside* PromptBuilder / via tools. The plan §7 caveat anticipated exactly this ("defer the messy ones"); the agent correctly deferred rather than forcing Potemkin spans. Lesson reinforced: for "wrap every operation" scopes, Day-0 should also verify each operation HAS a loop-level call boundary — 2 of the 6 here did not. Delivered 6 span types (LOOP/TURN/LLM_CALL/TOOL_EXEC/PROMPT_BUILD/COMPACTION) + 2 documented deferrals.
- **Token attrs don't reach OTel yet** — written post-response into a shared dict, which RecordingTracer observes by reference but `OTelTracer` (copies attrs at span-open) does not. Acceptable since Tier 2 (real export) is deferred, but the proper fix (a Tracer-ABC set-attribute API, or a close-and-reopen) is a real Tier-2-adjacent carryover.
- **COMPACTION nests under LOOP, not TURN** — it runs structurally before the TURN span opens; the agent kept it surgical (no control-flow move) and documented the honest nesting. Fine, but the idealized tree diagram (plan §3.0) showed it under TURN — reality差.

## Q5 — Carryover / open items (plan §9)

- **Tier 2** — real OTLP→Jaeger export (collector + `OTEL_*` env; 100% turn-coverage + < 5% overhead measured) → Area-C / DevOps.
- **`SpanStarted`/`SpanEnded`/`MetricRecorded` → SSE LoopEvent subclasses** → A-5 (shared sliver; `17.md §4.1`).
- **VERIFICATION + MEMORY_OP in the tree** — via the "nest existing internal spans" DRY refactor (wire adapter `llm_chat` / executor `tool.{name}` / verifier spans + thread ctx) rather than loop-level wraps.
- **Token attrs → OTel** — add a Tracer-ABC set-attribute API so post-response tokens reach Jaeger (currently RecordingTracer-only by reference); `cost_usd` on LLM_CALL.
- **Cross-process subagent span linkage** (`parent_span_id`) — once A-3 subagents are fully live.
- **Other Area-A**: A-5c (Inspector UI), A-6 (frontend real data), FE `/subagents` wiring (57.70 carryover).

## Q6 — Anti-pattern audit (04-anti-patterns.md)

- AP-4 (Potemkin): the loop tracer is exercised end-to-end (the tree test reconstructs LOOP→TURN→operation with real parent linkage; the Tier-0 test asserts `loop._tracer` is not NoOp) — closes the prior Cat 12 Potemkin (root span ran on NoOp). VERIFICATION/MEMORY_OP were deferred rather than shipped as empty spans (AP-4 avoided). ✅
- AP-2 (no orphan / single owner): the loop is the single trace-tree owner; adapter/executor/parser internal tracers stay NoOp (not wired) → no double-instrumentation, no orphan span paths. ✅
- LLM neutrality: loop edits are provider-free tracer wraps (`check_llm_sdk_leak` 0); no `import openai/anthropic`. ✅
- Double-counting guard: span token/cost = attributes only; router recorders unchanged (billing/SLA source of truth). ✅
- AP-3 (cross-dir scatter): changes cohere in `agent_harness/orchestrator_loop` + `observability/helpers` + `api/v1/chat`; no scatter. ✅

## Q7 — Final verification

`pytest tests/unit tests/integration` **2057 passed / 4 skipped** (= 57.70 baseline 2049 + 8 new); `mypy src/` 0 / 329; `run_all.py` 10/10 (LLM SDK leak 0); black 605 unchanged + isort/flake8 0; Vitest unchanged (no FE). No design note (feature-continuation — extends the built Cat 12 Tracer ABC + existing span pattern). SpanCategory decision recorded in `02.md §Naming Drift Note`.
