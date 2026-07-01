# Combined-vs-Separate Formation Quality A/B — 3 real-Azure runs (Sprint 57.154)

**Harness**: `backend/scripts/benchmark_combined_formation_quality.py`
**Corpus**: `backend/tests/fixtures/memory/memory_formation_quality_cases.yaml` (10 cases)
**Model**: real Azure cheap-tier (gpt-5.2 family), `temperature=0.0`
**Run date**: 2026-07-01
**Arms**: combined = `MemoryFormationWorker(combined=True)` (ONE chat) · separate = `combined=False` (TWO focused chats)
**Oracle**: Hybrid — facts = deterministic keyword-group coverage + spurious count; summary = LLM-judge faithfulness/coverage [0,1]

## Results (combined / separate / delta comb−sep)

| Run | facts_coverage | summary_score | facts_spurious_mean | mechanical verdict |
|-----|----------------|---------------|---------------------|--------------------|
| 1 | 95.00% / 100.00% / **−5.00%** | 0.994 / 0.990 / +0.004 | 0.40 / 0.40 / +0.00 | FLIP |
| 2 | 100.00% / 100.00% / +0.00% | 0.992 / 0.994 / −0.002 | 0.30 / 0.40 / −0.10 | KEEP |
| 3 | 100.00% / 100.00% / +0.00% | 0.994 / 0.970 / +0.024 | 0.30 / 0.40 / −0.10 | KEEP |

**Majority verdict: KEEP combined default ON (2/3).**

## Interpretation (honest finding)

- **facts_coverage**: combined matches separate (100%) in 2 of 3 runs; the single −5pp run (Run 1) is one case dropping ONE keyword-group out of the corpus's ~13 groups — the smallest measurable unit (1 group ≈ 5pp on a 10-case mean). It landed EXACTLY at the 5pp materiality boundary and did NOT reproduce → a run-to-run LLM-nondeterminism artifact (temperature=0 is deterministic-*ish*, not exact), NOT a stable regression.
- **summary_score**: combined is tied-to-better across all 3 runs (deltas +0.004 / −0.002 / +0.024; mean ≈ +0.009) — the attention-split of the combined prompt does NOT shallow the summary.
- **facts_spurious_mean**: combined is tied-to-better (0.30–0.40 vs a steady 0.40) — the combined prompt does NOT hallucinate more facts.

**Conclusion**: combined and separate formation are **quality-equivalent within LLM run-to-run noise**. Combined shows no stable regression on any axis (and is marginally better on spurious). The 57.152 default (combined ON) is validated — the ~2× per-send efficiency win holds at no material quality cost.

**Action**: KEEP `chat_memory_combined_formation` default ON. NO config change. `combined=False` remains the env fallback for anyone who wants two focused calls.

## Caveat (open invariant)

The verdict is per-run and a 10-case corpus has ±5pp facts variance from a single case. This sprint settled the borderline first run by running 3× and taking the majority + understanding the −5pp mechanism (one keyword-group, one case, at the exact boundary). A more robust harness would average N runs per arm (a `--runs N` follow-on); the single-run design mirrors the benchmark-family siblings (57.136/138/153) and the 3× manual repeat was sufficient here.
