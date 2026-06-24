# Sprint 57.139 Retrospective — layered compaction (tool-result preclear yield + ACON-band spike)

Closes `AD-Context-Layered-Compaction-ACON` (research #4, Cat 4). Branch `feature/sprint-57-139-layered-compaction-spike` from `main` `3bf4a727`.

## Q1 — Goal achieved?

**Yes.** Built a permanent per-layer compaction-yield harness + shipped a default-OFF earlier-trigger tool-result preclear lever (provider-neutral, byte-identical default). The A/B settled research #4: mean tool_clear_reduction **33.72% → IN the ACON 26-54% band**, capturing ~83% of total compaction yield for free + deferring semantic in 2/3 of cases → keep default OFF, ship as selectable opt-in. Drive-through proved no-regression + byte-identical default. AD CLOSED.

## Q2 — Estimate accuracy (calibration)

- NEW scope class **`layered-compaction-spike` 0.60** (1st data point). Bottom-up ~12 hr → committed ~7.2 hr (mult 0.60) → actual ~7 hr → **ratio ~0.97 IN band** → KEEP 0.60 pending 2-3 sprint validation.
- Agent-delegated: **no** (parent-direct), `agent_factor` 1.0 → 3-segment.
- Kin to the other Cat-spike measurement+lever sprints (`verification-in-loop-spike` 0.60 / `guardrail-restrict-spike` 0.60 / `verification-keycondition-spike` 0.60). The harness + 2 new compactors are a real-code core (≥3 hr) so the 0.60 bottom-up haircut fit (per the 57.137 lesson: a real implementation core holds the spike mult; the ceremony-only 0.85 re-points don't apply). LIGHTER on Azure than #136/#138 because the ACON-band core (L0/L1/L2) is LLM-free.

## Q3 — What went well

- Day-0 三-prong caught 5 drifts BEFORE code: D-compaction-strategy-wire (→ reuse STRUCTURAL, NO wire touch) · D-factory-location (recon's `factory.py` was a misattribution — all in `_category_factories.py`) · **D-masker-user-anchored** (the KEY finding — sharpened the corpus + drive-through + spawned a Phase 58 AD) · D-loop-call-site (→ ChainedCompactor transparent, loop UNTOUCHED) · D-tokencounter-default.
- The token-reduction-ratio insight (vs structural's message-count ratio) emerged from reading `loop.py:2234` (loop uses `result.tokens_after` directly) — a real correctness fix, not just a measurement nicety.
- Evidence-first paid off: the harness produced a clean, honest, composition-aware verdict (in-band on average, 0-64% spread) rather than an overclaim.

## Q4 — What to improve / drift

- The drive-through could not trigger preclear masking in the UI (user-anchored + tool-less plain chat + short single-send) — same honest limit as 57.136/138. Acceptable (CATCH = harness) but worth noting: compaction-mechanism spikes are inherently hard to drive-through on plain chat; the harness IS the primary evidence.
- Test-path drift (caught Day 1): existing compactor tests are FLAT `test_compactor_<name>.py`, not a `compactor/` subdir — adjusted to convention.
- The L1==L2 result (structural adds nothing beyond tool-clear on the synthetic corpus) is honest but means the corpus doesn't exercise dedup; a future corpus with redundant tool retries would separate the layers.

## Q5 — Anti-pattern self-check

- AP-2 (no orphan): ✅ all new code reachable from `make_chat_compactor` (when enabled) / the harness CLI; root screenshots cleaned up.
- AP-3 (no scattering): ✅ all in `compactor/`; tests at the existing flat convention.
- AP-4 (no Potemkin): ✅ preclear does real masking (unit-proven), harness measures real tokens; drive-through honest about what the UI proves vs the harness.
- AP-6 (no speculative abstraction): ✅ env-only (no per-tenant); ChainedCompactor is a real composition need (not speculative); default OFF.
- AP-8 (PromptBuilder): N/A. AP-11 (no version suffix): ✅.
- v2 lints 10/10 (incl. check_llm_sdk_leak — preclear/chained/harness LLM-neutral).

## Q6 — Carryover (→ next-phase-candidates)

- `AD-Compaction-ToolAnchored-Preclear-Phase58` — tool-anchored clear (by tool_use_id) to cover single-send chat (the user-anchored masker NO-OPs there).
- `AD-Compaction-Preclear-PerTenant-Phase58` — per-tenant preclear ratio (C3 seam).
- Larger / real-traffic corpus + a redundant-retry corpus to separate the structural-dedup layer.

## Q7 — Next

Per canonical research order #6 → #3 → #8 → **#4 (this) DONE** → next = **#1 Explicit task primitive (DAG)** (has its own thin-spike eval `5-status/task-primitive-thin-spike-eval-20260618.md`), then the 3 net-new #2/#5/#7. Rolling discipline: no pre-write — next sprint opens on explicit user go.

## Gate (final)

mypy src 376 (0) · run_all 10/10 · pytest 2825 +5skip (+28) · black/isort/flake8 clean · LLM-SDK-leak clean · Vitest 915 / mockup 51 / wire 25 untouched sentinels (backend-only). CHANGE-106 + design note 43 (8/8 gate, NO new 17.md contract).

## Design Note Extract (spike sprint)

**File**: `docs/03-implementation/agent-harness-planning/43-layered-compaction-acon-design.md`
**Verified ratio (estimated)**: ≥ 95%
**8-Point Quality Gate**:
- [x] 1. Section header per US
- [x] 2. file:line on every claim
- [x] 3. Decision matrix (6 rows)
- [x] 4. Verification command (pytest + RUN_AZURE_INTEGRATION)
- [x] 5. Test fixture (layered_compaction_cases.yaml + in-test stubs)
- [x] 6. Open invariant boundary (§4 deferred)
- [x] 7. Rollback path (§5, default-OFF sentinel)
- [x] 8. 17.md cross-ref (§3 — N/A justified, no new contract)

**Reviewer pass**: self-review.
