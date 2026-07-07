# Sprint 57.158 Retrospective — memory vector-recall precision A/B

**Closed**: 2026-07-06
**Branch**: `feature/sprint-57-158-memory-recall-precision-ab` (from `main` `65157788`)
**Closes**: `AD-Memory-Vector-Recall-Precision-AB`

## Q1 — What shipped?

An **evidence-first A/B benchmark spike, ZERO `src/` change**, that settled 57.155's honest gap: does the semantic vector axis actually out-recall confidence-ranked `profile()` at many-fact scale? A 3-arm harness (profile / keyword / semantic) + a discriminating 10-case corpus + a CI-safe offline test, run against real `text-embedding-3-large` + real Qdrant.

- NEW `scripts/benchmark_memory_recall_precision.py` (3 arms, recall@k/precision@k/MRR oracle, two-sided verdict).
- NEW `tests/fixtures/memory/memory_recall_precision_cases.yaml` (8/10 discriminating).
- NEW `tests/unit/scripts/test_benchmark_memory_recall_precision.py` (17 offline tests).
- **Verdict: semantic-wins** — semantic recall@k 100% vs profile 20% vs keyword 10% (+80pp, MRR 1.0).

## Q2 — Calibration (estimate accuracy)

- Class **NEW `memory-vector-recall-precision-ab-spike` 0.60**; **agent-delegated: no** (parent-direct, `agent_factor` 1.0, 3-segment).
- Bottom-up ~6 hr → class-calibrated commit **~3.6 hr** (×0.60).
- Actual ~3.6-3.8 hr-equivalent → **ratio ~1.0-1.05 IN band**. The real-code core (3-arm harness + oracle + discriminating corpus + 17 offline tests) held the 0.60 per the 57.137 lesson; Day-0 was 0-drift; the single real-Azure run was smooth (no re-drive, no re-architecture — UNLIKE 57.149). Every scaffold (57.154 mirror), double (`DeterministicEmbeddingClient` + `_FakeMemStore`), and idiom (importlib shadow) pre-existed → the bottom-up haircut fit.
- **Verdict**: KEEP 0.60 as the 1st data point. Per plan §7: if a 2nd `*-ab-spike` lands > 1.20, re-point 0.75.

## Q3 — What went well?

- **The rows-as-param insight** (Day-0 D-search-ingest-idempotency + recon) made the harness DB-free: `MemoryVectorIndex.search(rows=…)` takes rows directly, so all 3 arms rank the case's fact list with no Postgres — offline-runnable AND real-runnable with the same code.
- **The corpus discriminated cleanly** (8/10, asserted statically by the offline test) — so the real-Azure run produced a decisive, not muddy, verdict.
- **Honest measurement discipline**: the corpus was NOT tuned to force a win (the discrimination property is a realistic "buried low-confidence relevant fact" scenario), and the caveats (non-adversarial corpus; deterministic → no re-run) are documented rather than glossed.
- **ZERO src change** kept the gate trivially green (mypy `src` 400 unchanged, no wire/migration).

## Q4 — What to improve?

- I initially over-scoped the offline test's ambition (wanting it to show the semantic win), then correctly recognized the hash-based `DeterministicEmbeddingClient` has no semantic structure → the offline arm is machinery-only, the win is real-Azure-only. **Lesson**: for an embedding A/B, the offline test can only verify plumbing + oracle + corpus; the semantic signal is inherently a real-embedding property — scope the offline assertions accordingly from the start.
- The 100% semantic recall is almost suspiciously clean; I flagged it honestly (non-adversarial corpus) and registered the adversarial follow-on rather than presenting 100% as the final word.

## Q5 — Anti-pattern self-check

- **AP-2** (side-track): ✅ the harness is permanent eval tooling under `scripts/`, importable + CI-tested; not dead code.
- **AP-3** (scattering): ✅ Cat 3 eval tooling beside its siblings (`benchmark_*`); corpus under `tests/fixtures/memory/`.
- **AP-4** (Potemkin): ✅ the semantic arm drives the REAL `MemoryVectorIndex.search`; the real-Azure run produced a real verdict from real embeddings — the OPPOSITE of a Potemkin (this A/B exists precisely to prevent building a Potemkin on an unproven axis).
- **AP-6** (future-proofing): ✅ measures what exists; no speculative abstraction.
- **AP-8/AP-10/AP-11**: N/A / ✅ profile/keyword reproduce a 2-line SQL rule (anchored), not a divergent prompt/logic (AP-10 acceptable); ✅ no version suffixes.
- v2 lints: `python scripts/lint/run_all.py` → 11/11.

## Q6 — Carryover ADs (registered in next-phase-candidates.md)

- `AD-Memory-Vector-Recall-Adversarial-Corpus` (NEW — harder non-single-topic corpus to stress precision@k).
- The deferred 57.155 semantic-axis slices are now evidence-backed: `AD-Memory-Semantic-Axis-System-Tenant-Layers` · `AD-Memory-Vector-Incremental-Write` · `AD-Memory-Semantic-NearDup-Dedup` · `AD-Memory-Session-Summary-Semantic-Rank`.

## Q7 — Verification summary

- Offline +17 · mypy `src` 400/0 (no src change) · run_all 11/11 · black/isort/flake8 clean · LLM-SDK-leak clean.
- Real-Azure A/B (`text-embedding-3-large` + Qdrant): verdict **semantic-wins**, semantic recall@k 100% / profile 20% / keyword 10% (+80pp, MRR 1.0). Artifacts: `artifacts/memory_recall_precision_report.{md,json}`.
