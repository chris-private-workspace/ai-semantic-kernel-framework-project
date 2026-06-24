# Sprint 57.139 Plan — layered compaction: tool-result preclear yield + ACON-band measurement spike

**Summary**: Evidence-first thin spike closing `AD-Context-Layered-Compaction-ACON` (research #4, Cat 4 — next per the canonical order after #6/#3/#8). Builds a permanent measurement harness quantifying, per compaction layer, how much context tool-result clearing ALONE reclaims (the ACON 26–54% target band) and how often that cheap, LLM-free layer DEFERS the expensive semantic-summary layer. Ships a minimal **default-OFF earlier-triggering tool-result preclear lever** (reusing the existing `DefaultObservationMasker`, provider-neutral, no LLM) wired so the DEFAULT path stays byte-identical; the harness verdict sets the enable RECOMMENDATION (keep-OFF / opt-in), NOT a default flip. The "different axis from C2 (57.109)": C2 made the semantic summarizer cheap; #4 makes the cheap tool-clear layer run FIRST/earlier to avoid invoking semantic at all. Backend-only, NO migration/wire/frontend (unless D-compaction-strategy-wire forces a contained enum+codegen). Drive-through = the chat-v2 compaction path (honest limit: forcing 75%+ context live is hard → CATCH = the harness, UI = lever wiring + no-regression). Design note required (spike).

**Status**: Approved-to-execute (user "執行 #4 AD-Context-Layered-Compaction-ACON" + confirmed the thin-spike framework incl. the earlier-trigger preclear lever, 2026-06-24)
**Branch**: `feature/sprint-57-139-layered-compaction-spike`
**Base**: `main` HEAD `3bf4a727` (57.138 key-condition merge; #330 flip in flight, docs-only — sync before closeout navigator edits)
**Slice**: closes `AD-Context-Layered-Compaction-ACON` (research #4); standalone (the remaining C-slice axis distinct from C2)
**Scope decisions**: (a) evidence-first — the harness is the CERTAIN deliverable, the lever is default-OFF opt-in; (b) measure tool-clear in ISOLATION via a real `TokenCounter` (not the compactor's internal message-ratio approximation `structural.py:192-193`); (c) REUSE `DefaultObservationMasker.mask_old_results` for the preclear layer (no new masking logic, provider-neutral); (d) DEFAULT path byte-identical (factory returns the bare `HybridCompactor` when the preclear ratio is unset); (e) NOT a redo of C2's cheap-tier semantic routing.

---

## 0. Background

### The gap (AD-Context-Layered-Compaction-ACON, research #4; Cat 4)

The repo HAS tool-result clearing — but it's not a measured, standalone, early layer:

- `DefaultObservationMasker.mask_old_results` tombstones old `role="tool"` bodies, but it is **bundled inside** `StructuralCompactor` step 3 (`structural.py:169-172`), gated behind the SAME `token>75% ∨ turn>30` trigger as the whole compactor (`_abc.py:57-58`), and runs only as part of `HybridCompactor`'s structural pass.
- There is **NO measurement** of the per-layer yield: how much does tool-result clearing ALONE reclaim? Does it land in ACON's **26–54% band**? Does it DEFER the expensive semantic summary (a cheap-tier LLM call, C2 57.109)?
- ACON / CC-microcompact insight: tool-result clearing is the cheapest, highest-yield first move; running it EARLIER (a lower threshold) can keep tokens under budget WITHOUT ever calling the LLM summarizer.

### Why it matters (the missing capability)

The semantic layer costs a cheap-tier LLM call + ~seconds of latency. If a FREE, deterministic tool-clear layer running earlier defers/avoids it, that's pure cost + latency savings on long tool-heavy agent runs — directly serving the autonomous long-running capability (the `max_turns=8` bounded-burst + rehydration model leans on compaction staying cheap).

### Root cause (recon code read, file:line; ALL re-verified §checklist 0.1)

| Layer | Reality (on `main` HEAD `3bf4a727`) | Anchor |
|-------|-------------------------------------|--------|
| Tool-clear is bundled, not standalone/early | masking runs as structural step 3 under the 75%/turn-30 trigger | `structural.py:169-172`, `_abc.py:57-58` |
| The masker is deterministic, LLM-free, reusable | `mask_old_results(messages, *, keep_recent=5)` tombstones old `role="tool"` bodies; NO-OPs if `len(user_indices) <= keep_recent` | `observation_masker.py:50-78` (NO-OP guard `:63-64`) |
| Hybrid = structural→semantic; semantic is cheap-tier (C2) | semantic runs only if post-structural tokens > threshold | `hybrid.py:100-130`; C2 routing `handler.py:527` |
| Per-layer yield is UNMEASURED + the internal count is approximate | structural `tokens_after` is a message-count RATIO approximation, not a real token count | `structural.py:192-193` |

→ The fix: (1) build a harness that measures REAL per-layer token reduction (via a real `TokenCounter`, not the approximation) to test the ACON-band + semantic-deferral hypotheses; (2) ship a minimal default-OFF earlier-trigger preclear lever so operators can run the cheap layer first; let evidence set the recommendation.

### The design (backend-only: 1 new preclear compactor + 1 thin chain + factory wire + harness + corpus + tests)

```
NEW  compactor/preclear.py    — PreClearCompactor(Compactor): standalone mask_old_results,
                                 own preclear_ratio + keep_recent, LLM-free; reuses DefaultObservationMasker
NEW  compactor/chained.py     — ChainedCompactor(Compactor): run children in sequence, thread
                                 compacted_state (preclear → hybrid); merge CompactionResult
EDIT _category_factories.py   — make_chat_compactor: if CHAT_COMPACTION_PRECLEAR_RATIO > 0 →
                                 ChainedCompactor([preclear, hybrid]); else BARE hybrid (byte-identical default)
NEW  scripts/benchmark_layered_compaction.py — Cat 4 eval (mirror benchmark_sandbox_escape.py):
                                 per-layer token reduction; tool_clear_reduction_pct / in_acon_band /
                                 semantic_deferred_rate; CI-safe LLM-free core + RUN_AZURE_INTEGRATION semantic leg
NEW  tests/fixtures/context_mgmt/layered_compaction_cases.yaml — tool-heavy transcripts (varying tool-result sizes)
NEW  tests/unit/scripts/test_benchmark_layered_compaction.py   — CI-safe (importlib idiom)
NEW  tests/unit/agent_harness/context_mgmt/compactor/test_preclear_compactor.py
NEW  tests/unit/agent_harness/context_mgmt/compactor/test_chained_compactor.py
```

Why this over alternatives: folding the preclear INTO `HybridCompactor` muddies its single responsibility (AP-3 risk); a `ChainedCompactor` is a clean Cat-4 composition primitive AND lets the factory keep the DEFAULT path (the bare `HybridCompactor`) byte-identical when the lever is off.

### Ground truth (recon head-start — code read on `main` HEAD `3bf4a727`; ALL re-verified §checklist 0.1)

- `observation_masker.py:63-64` — masker NO-OPs when `len(user_indices) <= keep_recent` → the harness corpus MUST have > keep_recent user turns to actually mask.
- `structural.py:192-193` — internal `tokens_after` is a message-count approximation → the harness must use a real `TokenCounter.count()` for honest measurement.
- benchmark harness pattern: `scripts/benchmark_{judge,correction_hygiene,sandbox_escape}.py` — `load_cases / run_* / build_report / report_to_markdown / _amain (RUN_AZURE_INTEGRATION-gated) / main()`. Mirror.
- `compactor/_abc.py:76-89` — `compact_if_needed(state, *, trace_context) -> CompactionResult`; the loop calls it once/turn (`loop.py` ~2221).

**Baselines (57.138 closeout)**: pytest 2797+5skip · wire 25 · Vitest 915 · mockup 51 · mypy 0/374 · run_all 10/10. Re-verify Day-0.

### STALE / drift findings (Day-0; full detail → progress.md — placeholder, filled in §checklist 0.1)

- **D-compaction-strategy-wire** — does `CompactionStrategy` (STRUCTURAL/SEMANTIC/HYBRID) / `ContextCompacted` appear on the SSE wire schema / codegen? If YES → reuse `STRUCTURAL` for preclear (avoid wire touch); if NO → add a `PRECLEAR` enum cleanly. grep `CompactionStrategy` + `ContextCompacted` in `sse.py` / `WIRE_SCHEMA`. → shifts §3.1 + §8.
- **D-factory-location** — confirm `make_chat_compactor` + the env helpers (`CHAT_COMPACTION_TOKEN_BUDGET` / `CHAT_COMPACTION_KEEP_RECENT_TURNS`). Recon cited `_category_factories.py` + a `factory.py` env helper — verify the real file(s). → shifts §4.
- **D-tokencounter-default** — which `TokenCounter` the chat flow actually uses (Tiktoken vs GenericApprox) so the harness measures with the SAME counter. → shifts §3.2.
- **D-loop-call-site** — confirm the loop calls a single `self._compactor.compact_if_needed` so a `ChainedCompactor` is transparent (no loop edit). → shifts §3.1 / §4 (loop UNTOUCHED).
- **D-masker-noop-threshold** — re-confirm the `keep_recent` NO-OP guard so the corpus is valid (enough user turns).

## 1. Sprint Goal

Quantify the layered-compaction hypothesis (tool-result clearing in the ACON 26–54% band; defers the semantic layer) with a permanent measurement harness, and ship a minimal **default-OFF** earlier-trigger tool-result preclear lever (provider-neutral, byte-identical default). PROVEN by: all gates green + the harness report (CI-safe LLM-free core measuring `tool_clear_reduction_pct` + `in_acon_band`; RUN_AZURE_INTEGRATION semantic leg measuring `semantic_deferred_rate`) + a chat-v2 drive-through (lever wiring + no-regression). Produces **CHANGE-106 + design note `43-layered-compaction-acon-design.md`** (spike). Verdict expected (per the #136/#138 pattern): keep default OFF; the lever is selectable; recommendation set by evidence.

## 2. User Stories

- **US-1** (preclear layer): 作為平台維運者，我希望有一個獨立、便宜（無 LLM）的 tool-result 清理層可在較低門檻先觸發，以便在呼叫昂貴 semantic 摘要前就把 context 壓回預算內。
- **US-2** (measurement harness): 作為平台維運者，我希望一個可重複的 harness 量測每層壓縮的 real token reduction（tool-clear 是否落在 ACON 26–54% band、是否延後 semantic），以便用證據決定是否啟用 preclear。
- **US-3** (selectability, default-OFF): 作為平台維運者，我希望 preclear 經 env 選用、預設 OFF、預設路徑 byte-identical，以便零風險導入。
- **US-4** (drive-through, MANDATORY): 作為使用者，我在 chat-v2 長對話啟用 preclear 後行為正常（no-regression），且壓縮事件可見。
- **US-5** (closeout): CHANGE-106 + design note 43 + calibration + navigators + AD CLOSED.

## 3. Technical Specifications

### 3.0 Architecture (backend-only; NO migration/frontend; wire only if D-compaction-strategy-wire forces a contained enum)

```
EDIT  backend/src/api/v1/chat/_category_factories.py   — make_chat_compactor preclear branch (default = bare hybrid)
NEW   backend/src/agent_harness/context_mgmt/compactor/preclear.py
NEW   backend/src/agent_harness/context_mgmt/compactor/chained.py
NEW   backend/scripts/benchmark_layered_compaction.py
NEW   backend/tests/fixtures/context_mgmt/layered_compaction_cases.yaml
NEW   backend/tests/unit/scripts/test_benchmark_layered_compaction.py
NEW   backend/tests/unit/agent_harness/context_mgmt/compactor/test_preclear_compactor.py
NEW   backend/tests/unit/agent_harness/context_mgmt/compactor/test_chained_compactor.py
UNTOUCHED  orchestrator_loop/loop.py (ChainedCompactor is transparent — single compact_if_needed call site)
UNTOUCHED  compactor/{structural,semantic,hybrid}.py · observation_masker.py (reused, not modified)
```

### 3.1 PreClearCompactor + ChainedCompactor (US-1) — `compactor/preclear.py`, `compactor/chained.py`

- **`PreClearCompactor(Compactor)`**: `should_compact` triggers at `token_usage_so_far > preclear_ratio * token_budget` (ratio default e.g. 0.50 — LOWER than the 0.75 structural trigger; configurable). `compact_if_needed` runs ONLY `self.masker.mask_old_results(messages, keep_recent=...)` (reusing `DefaultObservationMasker`), rebuilds the state, returns a `CompactionResult` with `strategy_used=STRUCTURAL` (D-compaction-strategy-wire: reuse to avoid wire touch; OR `PRECLEAR` if contained). No LLM, no contract change.
- **`ChainedCompactor(Compactor)`**: holds an ordered `list[Compactor]`; `compact_if_needed` runs each in sequence, threading the compacted state forward (preclear's output → hybrid's input), merging `messages_compacted` and carrying the final stage's tokens/usage/model. `should_compact` = any child would trigger.

### 3.2 Measurement harness (US-2) — `scripts/benchmark_layered_compaction.py`

Mirror `benchmark_sandbox_escape.py`. Over the corpus, for each transcript measure with a REAL `TokenCounter` (the same one the chat flow uses — D-tokencounter-default):
- L0 = `count(raw_messages)`; L1 = `count(mask_old_results(raw, keep_recent))` (tool-clear ONLY); L2 = `count(StructuralCompactor result)`; L3 = `count(HybridCompactor result)` (semantic — RUN_AZURE_INTEGRATION only).
- `build_report`: `tool_clear_reduction_pct` = (L0−L1)/L0 (per-case + mean); `in_acon_band` = mean ∈ [0.26, 0.54]; `structural_reduction_pct`; `semantic_reduction_pct`; `semantic_deferred_rate` = fraction where L1 already ≤ 0.75*budget (semantic unneeded); `preclear_recommended` = in_acon_band AND semantic_deferred_rate ≥ a stated floor.
- `report_to_markdown` + `_amain` (RUN_AZURE_INTEGRATION-gated for the L3 leg) + `main()`. The LLM-free L0/L1/L2 legs always run (CI-safe core).

### 3.3 Corpus + tests (US-2)

- `layered_compaction_cases.yaml`: tool-heavy transcripts (varying #tools, tool-result blob sizes, > keep_recent user turns so masking fires). Each case labeled with expected ranges (sanity, not exact).
- `test_benchmark_layered_compaction.py` (importlib idiom): load_cases (schema/dup) · run with a real counter (no LLM) · build_report (reduction math / band / deferral) · the LLM-free invariant.
- `test_preclear_compactor.py` + `test_chained_compactor.py`: preclear masks only / triggers at lower ratio / NO-OP under threshold; chained threads state / merges results / default-equivalence.

### 3.4 Selectability + factory wire (US-3) — `_category_factories.py`

`make_chat_compactor`: read `CHAT_COMPACTION_PRECLEAR_RATIO` (+ optional `CHAT_COMPACTION_PRECLEAR_KEEP_RECENT`). If ratio > 0 → return `ChainedCompactor([PreClearCompactor(...), hybrid])`; else return the bare `HybridCompactor` (byte-identical default). Env-only (anti-AP-6: no per-tenant this spike).

### 3.x What is explicitly NOT done

- NOT building new masking logic (reuse `DefaultObservationMasker`).
- NOT touching the semantic / cheap-tier routing (that's C2 — the different axis).
- NOT per-tenant preclear config (→ Phase 58 AD; env-only this spike).
- NOT a default flip / preclear default-ON (evidence sets the recommendation).
- NOT the full CC 5-layer ladder (snip/microcompact/collapse) — tool-result preclear only.
- NOT migration / frontend; wire only if D-compaction-strategy-wire forces a contained enum+codegen.

### 3.y Validation (US-1..US-5)

Gates: mypy `src` 0 · run_all 10/10 · pytest 2797+ + new · Vitest 915 · mockup 51 (`diff` empty) · `npm run lint && npm run build` (NO `--silent`; FE untouched → sentinel) · black/isort/flake8 clean · LLM-SDK-leak clean. Plus the §3 harness report + the §US-4 drive-through (MANDATORY).

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `backend/src/agent_harness/context_mgmt/compactor/preclear.py` | NEW |
| 2 | `backend/src/agent_harness/context_mgmt/compactor/chained.py` | NEW |
| 3 | `backend/src/api/v1/chat/_category_factories.py` | EDIT (preclear branch; default bare hybrid) |
| 4 | `backend/scripts/benchmark_layered_compaction.py` | NEW |
| 5 | `backend/tests/fixtures/context_mgmt/layered_compaction_cases.yaml` | NEW |
| 6 | `backend/tests/unit/scripts/test_benchmark_layered_compaction.py` | NEW |
| 7 | `backend/tests/unit/agent_harness/context_mgmt/compactor/test_preclear_compactor.py` | NEW |
| 8 | `backend/tests/unit/agent_harness/context_mgmt/compactor/test_chained_compactor.py` | NEW |
| 9 | `claudedocs/4-changes/feature-changes/CHANGE-106-layered-compaction-acon.md` | NEW |
| 10 | `docs/03-implementation/agent-harness-planning/43-layered-compaction-acon-design.md` | NEW (spike design note) |
| 11 | `docs/.../sprint-57-139/{progress,retrospective}.md` + `artifacts/` | NEW |
| 12 | navigators (CLAUDE.md / MEMORY.md / next-phase-candidates / sprint-workflow matrix) | EDIT (closeout) |
| — | `backend/src/agent_harness/orchestrator_loop/loop.py` | **UNTOUCHED** (ChainedCompactor transparent) |
| — | `compactor/{structural,semantic,hybrid}.py` · `observation_masker.py` | **UNTOUCHED** (reused) |
| — | migration / wire / codegen / frontend | **UNTOUCHED** (unless D-compaction-strategy-wire forces a contained enum) |

## 5. Acceptance Criteria

1. `PreClearCompactor` reuses `mask_old_results`, is LLM-free, has its own `preclear_ratio` + `keep_recent`, NO-OPs under threshold — unit-tested.
2. `ChainedCompactor` threads state preclear→hybrid + merges results — unit-tested; the DEFAULT factory path is the bare `HybridCompactor` (byte-identical) when the ratio is unset.
3. The harness reports `tool_clear_reduction_pct` + `in_acon_band` + `semantic_deferred_rate` over the corpus; the LLM-free core (L0/L1/L2) runs in CI; the semantic leg (L3) is RUN_AZURE_INTEGRATION-gated.
4. A/B verdict recorded (recommend enable vs keep-OFF) in progress.md + `artifacts/` — default stays OFF regardless.
5. **Drive-through PASS (MANDATORY, real UI + backend + LLM)** — chat-v2 with preclear enabled (via env) → long conversation behaves normally (no-regression) + a compaction event is observable; honest CATCH=harness note (forcing 75%+ live is hard); screenshot + observed-vs-intended in progress.md. (NOT gate-only.)
6. `AD-Context-Layered-Compaction-ACON` CLOSED; CHANGE-106 + design note 43 (8-point gate); calibration `layered-compaction-spike` ~0.60 recorded; navigators + next-phase-candidates updated (advance to #1 next).

## 6. Deliverables

- [ ] US-1 `PreClearCompactor` + `ChainedCompactor` (Cat 4)
- [ ] US-2 `benchmark_layered_compaction.py` + corpus + CI-safe test
- [ ] US-3 factory preclear branch (default byte-identical) + env knob
- [ ] US-4 drive-through (chat-v2, real LLM, preclear enabled, no-regression)
- [ ] US-5 CHANGE-106 + design note 43 + retro + calibration + navigators

## 7. Workload Calibration

- Scope class **NEW `layered-compaction-spike` 0.60** (kin to `verification-in-loop-spike` 0.60 / `guardrail-restrict-spike` 0.60 / `verification-keycondition-spike` 0.60 — a Cat-4 structural spike paired with a measurement harness + a bounded config lever + a drive-through; the harness + 2 new compactors are a real-code core ≥ ~3 hr so the 0.60 bottom-up haircut fits per the 57.137 lesson; LIGHTER on Azure than #136/#138 because the ACON-band core is LLM-free).
- **Agent-delegated: no** (parent-direct). `agent_factor` 1.0 → 3-segment form.
- Bottom-up est ~12 hr (preclear 1.5 + chained 1.5 + factory 0.5 + harness 3 + corpus 1 + harness test 1.5 + compactor tests 1.5 + drive-through 1 + Day-0/closeout ~0.5) → class-calibrated commit ~7.2 hr (mult 0.60). Day-4 retro Q2 verifies.

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| **Risk Class E** — drive-through against a stale `--reload` / orphan spawn-worker (startup-resolved compactor + env read at startup) | Clean restart; kill stale workers; `Get-CimInstance Win32_Process` PID/PPID/StartTime; set `CHAT_COMPACTION_PRECLEAR_RATIO` + `CHAT_COMPACTION_TOKEN_BUDGET` BEFORE restart (env read at startup via `get_settings` lru_cache) |
| Live drive-through can't easily force 75%+ context | Lower `CHAT_COMPACTION_TOKEN_BUDGET` to force compaction in a few turns; honest CATCH=harness note (same limit as prior compaction work) |
| **D-compaction-strategy-wire** — adding a `PRECLEAR` enum could ripple to wire/codegen | Day-0 decides: reuse `STRUCTURAL` (no wire touch) vs contained `PRECLEAR` enum |
| Synthetic corpus may not reflect real tool-result size distribution | Vary blob sizes + #tools; state the synthetic-corpus caveat in the design note (honesty over overclaim) |
| Internal `tokens_after` approximation (`structural.py:192-193`) could mislead | Harness measures with a real `TokenCounter`, NOT the compactor's internal field |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- Per-tenant preclear config → `AD-Compaction-Preclear-PerTenant-Phase58` (C3 seam).
- The full CC 5-layer ladder (snip / microcompact / context-collapse) → future Cat-4 slices if evidence warrants.
- Default flip / preclear default-ON → only if a later, larger corpus proves a strong, low-risk win.
- Next per canonical order = **#1 Explicit task primitive (DAG)** — has its own thin-spike eval (`5-status/task-primitive-thin-spike-eval-20260618.md`).
