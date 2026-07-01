# CHANGE-121: Combined-vs-separate memory-formation quality A/B (validate the 57.152 default)

**Date**: 2026-07-01
**Sprint**: 57.154
**Scope**: 範疇 3 (Memory) — eval tooling; backend-only, ZERO src change

## Problem

Sprint 57.152 combined the two post-send cheap-tier memory-formation calls (57.149 `MemoryExtractor` facts + 57.151 `SessionSummarizer` summary) into ONE `chat()` via `MemoryFormationWorker`, shipping `chat_memory_combined_formation` default ON on a flag + a single drive-through — with **no numbers** proving the combined prompt does not DEGRADE either half's quality vs the two focused calls. `AD-Memory-Combined-Formation-AB-Quality` (57.152 carryover) is that evidence gap, on a default-ON path that runs after every chat send.

## Root Cause

Combining two focused prompts into one structured-JSON request is a quality-vs-cost trade (the model splits attention; the shared prompt is longer). 57.152 measured the cost win (~2× fewer calls) but never the quality side, so the default rested on intuition + one drive-through.

## Solution

A real-Azure A/B harness (backend-only, ZERO src change) settling the trade with numbers:

- **NEW `backend/scripts/benchmark_combined_formation_quality.py`** — drives the REAL `MemoryFormationWorker.form()` under two arms (`combined=True` = one call / `combined=False` = two focused calls) over a golden corpus, capturing (not persisting) the terminal write via `_CapturingUserLayer`/`_CapturingSummaryStore` so the harness is byte-faithful to production (AP-10 — no divergent prompt re-implementation).
- **Hybrid oracle** (user-picked, AskUserQuestion): facts = deterministic keyword-group coverage + spurious count; summary = an LLM-judge faithfulness/coverage score `[0,1]` via a self-contained rubric over the neutral ChatClient ABC (NOT a production `verification/templates/` file — avoids an orphan production-selectable template).
- **Two-sided verdict** — KEEP combined default ON iff it does NOT materially regress facts_coverage OR summary_score (≥ −5pp) AND does not inflate spurious facts; the ~2× efficiency win was established 57.152, so the A/B only guards quality.
- **NEW corpus** `backend/tests/fixtures/memory/memory_formation_quality_cases.yaml` (10 difficulty-graded cases) + **NEW** 24 CI-safe unit tests (spy formation + judge ChatClients + capturing sinks; `run_arm` drives the REAL worker offline asserting combined = 1 chat() / separate = 2).

Code location: `backend/scripts/benchmark_combined_formation_quality.py`, `backend/tests/fixtures/memory/`, `backend/tests/unit/scripts/`. PR #<pending>.

## Verification

- **Real-Azure A/B, 3 runs** (real cheap-tier over the real production formation path): facts_coverage combined {95, 100, 100}% vs separate {100, 100, 100}% — the single Run-1 −5pp is one case dropping one keyword-group at the exact 5pp boundary and did NOT reproduce (run-to-run LLM noise, temp=0 is deterministic-*ish*); summary_score combined tied-to-better (mean Δ ≈ +0.009); facts_spurious combined tied-to-better (0.30–0.40 vs 0.40). **Majority verdict KEEP** (2/3) → combined ≈ separate quality-equivalent within LLM noise.
- **Gates**: 24 new unit tests pass · run_all 11/11 · black/isort/flake8 clean · LLM-SDK-leak clean · mypy `src/` 0/397 (src untouched; harness in `scripts/` is not CI-mypy-gated).
- Full 3-run evidence: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-154/artifacts/combined-formation-quality-ab-3runs.md`.

## Impact

- **Decision**: KEEP `chat_memory_combined_formation` default ON (the 57.152 default is validated). **NO src change** — the config default stays as-is; `combined=False` remains the env fallback.
- Backend-only measurement spike. NO migration / wire (26) / frontend / loop.py. No user-facing behavior change (default unchanged) → no chat-v2 drive-through required.
- `AD-Memory-Combined-Formation-AB-Quality` CLOSED. The memory-formation arc (57.148→152) efficiency decision is now evidence-backed.
- Carryover: `AD-Memory-Formation-AB-Robustness-MultiRun` (a `--runs N` averaging flag to remove the single-run ±5pp variance) + `AD-Memory-Combined-Formation-PerTenant-Phase58` (C3 per-tenant combined/separate override) + extend the A/B to weaker models / harder corpora if a future strong-model verdict is inconclusive.
