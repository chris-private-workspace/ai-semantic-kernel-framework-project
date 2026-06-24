# CHANGE-106: Layered compaction — tool-result preclear yield + ACON-band measurement spike

**Date**: 2026-06-24
**Sprint**: 57.139
**Scope**: 範疇 4 (Context Management) — backend-only
**AD**: closes `AD-Context-Layered-Compaction-ACON` (research #4)

## Problem

The repo HAS tool-result clearing (`DefaultObservationMasker.mask_old_results` tombstones old `role="tool"` bodies) but it is BUNDLED inside `StructuralCompactor` step 3 (`structural.py:169-172`), gated behind the SAME `token>75% ∨ turn>30` trigger as the whole compactor, and runs only as part of `HybridCompactor`'s structural pass. There was NO measurement of the per-layer yield: does tool-result clearing ALONE land in ACON's 26–54% band? Does it DEFER the expensive semantic-summary LLM call (cheap tier, C2 57.109)? Research #4 (ACON / CC microcompact) claims clearing tool results first is the cheapest, highest-yield move.

## Root Cause

Layered compaction was never measured as a distinct cheap FIRST layer — the masking was an implementation detail of the structural pass, with no standalone earlier-trigger option and no per-layer yield evidence. (Also: `StructuralCompactor`'s internal `tokens_after` is a message-count ratio approximation — `structural.py:192-193` — blind to in-place tombstoning, so even if isolated it would under-report the masking reduction.)

## Solution

Evidence-first thin spike (same shape as 57.136/137/138):

1. **`compactor/preclear.py`** (NEW) — `PreClearCompactor(Compactor)`: a standalone, LLM-free tool-result clearing layer that triggers at a LOWER `preclear_ratio` (default 0.50). Reuses `DefaultObservationMasker` (no new masking logic), preserves system+HITL (mirrors structural), honest passthrough when nothing masked. Counts the REAL token-reduction ratio (masked/original) via an injected `TokenCounter` and applies it to the loop-tracked `tokens_before` → `tokens_after` stays in the loop's scale AND reflects the true reduction (fixes the structural message-count-ratio blindness). Reports `strategy_used=STRUCTURAL` (a structural-family tool clear — reuse avoids a wire/codegen touch per D-compaction-strategy-wire).
2. **`compactor/chained.py`** (NEW) — `ChainedCompactor(Compactor)`: runs children in sequence (preclear→hybrid), threading compacted state forward so the hybrid sees the preclear-reduced count via `should_compact` and may DEFER its semantic stage. Merges results + carries C2 LLM-usage attribution. Transparent to the loop's single `compact_if_needed` call site (`loop.py:2221`) → `loop.py` UNTOUCHED.
3. **`_category_factories.py`** (EDIT) — `_compaction_preclear_ratio()` (`CHAT_COMPACTION_PRECLEAR_RATIO`, valid (0,1) else 0=OFF) + `make_chat_compactor` branch: ratio>0 → `ChainedCompactor([PreClearCompactor(TiktokenCounter), hybrid])`; unset → bare `HybridCompactor` (DEFAULT byte-identical).
4. **`scripts/benchmark_layered_compaction.py`** (NEW) — a permanent per-layer yield harness (mirrors `benchmark_sandbox_escape.py`): measures L0 raw / L1 tool-clear-only / L2 structural / L3 hybrid-semantic with a REAL `TiktokenCounter(gpt-4o)`; reports `tool_clear_reduction` / `in_acon_band` / `semantic_reduction` / `semantic_deferred_rate` / `preclear_recommended`. LLM-free core (L0/L1/L2) + `RUN_AZURE_INTEGRATION`-gated L3.
5. Corpus `tests/fixtures/context_mgmt/layered_compaction_cases.yaml` (6 specs) + tests `test_benchmark_layered_compaction.py` (13) + `test_compactor_{preclear,chained}.py` (8+7).

NO migration / wire / codegen / frontend; `loop.py` + `observation_masker.py` + `compactor/{structural,semantic,hybrid}.py` UNTOUCHED.

## A/B Result (real Azure, 6 cases × cheap tier)

| metric | value |
|--------|-------|
| mean tool_clear_reduction | **33.72% → IN ACON band [26-54%]** ✅ |
| mean semantic_reduction | 40.65% |
| semantic_deferred_rate | **66.67%** (4/6) |
| preclear_recommended | True |

The FREE tool-clear layer captures **~83%** (33.72/40.65) of the TOTAL compaction yield the expensive semantic layer reaches, and defers semantic in 2/3 of cases. The semantic LLM layer earns its cost mainly on prose-heavy transcripts (text-heavy case: tool-clear 11% → semantic 34.6%, +23pp).

**Verdict (evidence-first)**: keep default OFF; ship preclear as a selectable env opt-in. The win is composition-dependent + the user-anchored masker NO-OPs single-send chat. Report → `sprint-57-139/artifacts/layered_compaction_report.{md,json}`.

## Verification

- `pytest tests/unit/agent_harness/context_mgmt/test_compactor_preclear.py test_compactor_chained.py tests/unit/scripts/test_benchmark_layered_compaction.py` → 28 passed
- `RUN_AZURE_INTEGRATION=1 python scripts/benchmark_layered_compaction.py` → the A/B numbers above
- **Drive-through PASS** (chat-v2, real Azure gpt-5.2): ARM A preclear ON → 3 turns (TCP/TLS/QUIC) no-regression with `ChainedCompactor` active; ARM B default OFF → "Tokyo" → bare `HybridCompactor` byte-identical. Honest 兩者結合: CATCH = the harness (yield), UI = no-regression + chain wiring (preclear masking is NOT UI-triggerable on plain tool-less chat). Screenshots in `artifacts/`.
- Gate: mypy src 376 (0) · run_all 10/10 · pytest 2825 +5skip (+28) · black/isort/flake8 clean · LLM-SDK-leak clean.

## Impact

Backend-only, default OFF → zero behavior change unless `CHAT_COMPACTION_PRECLEAR_RATIO` is set. Gives operators a free, earlier-triggering tool-result clearing layer for tool-heavy long-running (rehydrated) sessions, plus a permanent harness to re-measure the yield. KEY follow-on: the user-anchored masker NO-OPs single-send chat → a tool-anchored clear (by tool_use_id) for single-send is `AD-Compaction-ToolAnchored-Preclear-Phase58`.
