# 57 — Combined-vs-Separate Memory-Formation Quality A/B (design note)

**Purpose**: Extract the verified design of the Sprint 57.154 A/B harness that settles whether `MemoryFormationWorker`'s combined single-call formation degrades either half's quality vs two focused calls — validating the 57.152 default with real numbers.
**Category / Scope**: 範疇 3 (Memory) — eval tooling / Phase 57 / Sprint 57.154
**Created**: 2026-07-01
**Status**: Active
**Slice**: closes `AD-Memory-Combined-Formation-AB-Quality` (57.152 carryover)

> **Modification History**
> - 2026-07-01: Initial creation (Sprint 57.154) — combined-vs-separate formation quality A/B

---

## 1. Spike Summary (US: measure combined-vs-separate formation quality)

Sprint 57.152 shipped `MemoryFormationWorker` (`backend/src/agent_harness/memory/formation.py:93`) — one combined cheap-tier `chat()` returning both the durable-facts array AND the session-summary object, default ON via `chat_memory_combined_formation`, halving per-send background token+latency. It settled the COST but not the QUALITY: does the combined prompt lower fact recall or summary faithfulness vs the two focused 57.149/57.151 calls? This spike answers with a real-Azure A/B harness + a Hybrid oracle, and acts on the verdict.

**Verdict (3 real-Azure runs)**: KEEP combined default ON — combined ≈ separate quality-equivalent within LLM run-to-run noise. NO src change (config default validated as-is).

## 2. Decision Matrix

### 2.1 Oracle methodology (user-picked, AskUserQuestion 2026-07-01)

| Option | Facts | Summary | Cost | Verdict |
|--------|-------|---------|------|---------|
| **Hybrid (CHOSEN)** | deterministic keyword-group coverage + spurious | LLM-judge faithfulness [0,1] | 1 judge call/case | ✅ catches subtle summary drift a rule can't, pins facts objectively; mirrors 57.141 hybrid + 57.138/153 judge |
| Pure deterministic rules | keyword coverage | keyword coverage | 0 LLM | ❌ misses "technically-covering but less faithful" summaries — the combined prompt's most likely degradation mode |
| Dual LLM-judge | judge | judge | 2 judge calls/case | ❌ deepest but 2× judge cost + max non-determinism; facts recall is objectively rule-checkable so a judge there adds noise not signal |

### 2.2 How the harness drives the arms

| Option | Fidelity | Src change | Verdict |
|--------|----------|-----------|---------|
| **Capturing sinks (CHOSEN)** | drives REAL `form()` end-to-end (build→chat→parse→dispatch), captures only the terminal DB write | ZERO | ✅ byte-faithful to production (AP-10); the sinks are the sole doubles |
| Reach into private `_build_prompt`/`_parse_combined` | reuses real prompt/parse but not the dispatch | ZERO | ❌ smells (reaches into privates); skips the dispatch path |
| Re-implement the prompts in the harness | none | ZERO | ❌ AP-10 divergence — measures a different prompt than production |

### 2.3 Summary judge implementation

| Option | Fit | Src change | Verdict |
|--------|-----|-----------|---------|
| **Self-contained rubric in harness (CHOSEN)** | a summary-faithfulness rubric via the ChatClient ABC, under `backend/scripts/` | ZERO (outside AP-8 root) | ✅ honest fit; no production-template pollution |
| Reuse `LLMJudgeVerifier` + new `summary_faithfulness.txt` | production judge, but a summary is not an agent-OUTPUT-vs-trace | +1 template file | ❌ a production-selectable template no production path uses = orphan smell |

## 3. Verified Invariants (each with file:line + verification command)

- **The two arms differ only by the ctor `combined` flag** — `MemoryFormationWorker.form()` dispatches to `_form_combined` (`formation.py:151`, ONE `chat()` at `:176`) vs `_form_separate` (`formation.py:193`, TWO `chat()` via `extract_session_to_user` `extraction.py:80` + `summarize_and_store` `session_summarizer.py:90`).
  - Verify: `test_run_arm_combined_one_call_per_case` (combined = 1 chat/case) + `test_run_arm_separate_two_calls_per_case` (separate = 2 chat/case) — `backend/tests/unit/scripts/test_benchmark_combined_formation_quality.py`.
- **The capturing sinks match the real write seams** — `_CapturingUserLayer.write(*, content, tenant_id, user_id, time_scale, confidence, source, trace_context)` mirrors `UserLayer.write` (`memory/layers/user_layer.py:124`); `_CapturingSummaryStore.upsert_summary(*, session_id, summary, key_decisions, unresolved_issues)` mirrors `DBSessionSummaryStore.upsert_summary` (`memory/session_summary_store.py:117`). Byte-faithful dispatch → the harness scores exactly what production would write.
- **The Hybrid oracle discriminates** — a scripted worse arm scores lower: `test_score_facts_partial_coverage` (0.5), `test_score_facts_spurious_count`, `test_build_report_flip_on_*` (facts/summary/spurious regression → FLIP).
- **The verdict is two-sided** — `build_report` (`benchmark_combined_formation_quality.py`) flags KEEP iff `facts_coverage_delta ≥ −0.05 AND summary_score_delta ≥ −0.05 AND spurious_delta ≤ 1.0`.
  - Verify: `python -m pytest tests/unit/scripts/test_benchmark_combined_formation_quality.py -q` → **24 passed**.
- **Real-Azure A/B (3 runs)** — facts_coverage combined {95,100,100}% vs separate {100,100,100}% (Run-1 −5pp = one keyword-group in one case at the exact boundary; did NOT reproduce → LLM noise); summary tied-to-better (mean Δ ≈ +0.009); spurious tied-to-better (0.30–0.40 vs 0.40) → **KEEP combined default ON**.
  - Verify: `RUN_AZURE_INTEGRATION=1 python scripts/benchmark_combined_formation_quality.py` (needs Azure env; loads the root `.env`).

## 4. Cross-Category Contracts

- **No new contract.** The harness is eval tooling consuming EXISTING contracts: the ChatClient ABC (`17-cross-category-interfaces.md §2.1`) for both formation + judging, and the 範疇 3 `MemoryFormationWorker`/`MemoryExtractor`/`SessionSummarizer` as-shipped (57.149/151/152). No ABC / event / DB change. Wire count unchanged (26).

## 5. Open Invariants (verified vs deferred)

**Verified in this spike**: the combined-vs-separate quality delta on a 10-case corpus over 3 real-Azure runs (facts coverage / summary faithfulness / spurious); the efficiency invariant (combined 1 call vs separate 2); the two-sided verdict logic; the capturing-sink fidelity.

**Deferred (NOT verified here)**:
- Single-run variance: a 10-case corpus has ±5pp facts variance from one case (Run-1 flipped on it). Settled by 3× manual repeat + majority; a `--runs N` averaging flag is `AD-Memory-Formation-AB-Robustness-MultiRun`.
- Weaker models / larger corpora: the verdict is for the strong cheap-tier model on 10 cases; a weaker model may show a real combined penalty (the reflection-family caveat) — a follow-on if a future verdict is inconclusive.
- Per-tenant combined/separate policy — `AD-Memory-Combined-Formation-PerTenant-Phase58` (C3 seam).

## 6. Rollback / Fallback

The spike ships NO production code change (harness + corpus + tests only). If the KEEP decision is later reversed (e.g. a weaker-model run shows a real penalty), flip one line — `chat_memory_combined_formation` default `True → False` in `backend/src/core/config/__init__.py` — reverting to the proven two focused calls; `combined=False` already delegates to the full single-call `MemoryExtractor.extract_session_to_user` + `SessionSummarizer.summarize_and_store` (`formation.py:193`), so the fallback is battle-tested (it IS the 57.149/151 path). Est: 1-line + a config test. No data migration.

## 7. References

- `backend/scripts/benchmark_combined_formation_quality.py` — the harness
- `backend/tests/fixtures/memory/memory_formation_quality_cases.yaml` — the golden corpus (10 cases)
- `backend/tests/unit/scripts/test_benchmark_combined_formation_quality.py` — 24 CI-safe tests
- `docs/.../sprint-57-154/artifacts/combined-formation-quality-ab-3runs.md` — the 3-run evidence
- `55-memory-combined-formation-design.md` — the combined-vs-separate design (57.152, what this A/B validates)
- `backend/scripts/benchmark_memory_grounded_judge.py` — the mirrored scaffold (57.153)
- `17-cross-category-interfaces.md §2.1` — ChatClient ABC (the sole contract consumed)
- CHANGE-121

## 8. Modification History

- 2026-07-01: Initial creation (Sprint 57.154) — combined-vs-separate formation quality A/B (KEEP verdict)
