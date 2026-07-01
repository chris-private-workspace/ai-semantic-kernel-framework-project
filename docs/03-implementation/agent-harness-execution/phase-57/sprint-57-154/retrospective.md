# Sprint 57.154 Retrospective — Combined-vs-separate formation quality A/B

**Sprint**: 57.154 · **AD**: `AD-Memory-Combined-Formation-AB-Quality` (57.152 carryover) · **Closed**: 2026-07-01
**Branch**: `feature/sprint-57-154-combined-formation-quality-ab` (from `main` `a0cf503a`)

## Q1 — What was delivered?

A real-Azure A/B harness (backend-only, ZERO src change) settling whether `MemoryFormationWorker`'s combined single-call formation degrades either half's quality vs two focused calls:
- `benchmark_combined_formation_quality.py` — drives the REAL `form()` under both arms via capturing sinks (AP-10 safe), Hybrid oracle (deterministic facts coverage + LLM-judge summary faithfulness), two-sided verdict.
- 10-case difficulty-graded golden corpus + 24 CI-safe unit tests (spy formation + judge clients; efficiency invariant combined=1/separate=2 chat/case asserted offline).
- **Verdict (3 real-Azure runs): KEEP combined default ON** — combined ≈ separate quality-equivalent within LLM noise (the Run-1 −5pp facts was a single-case single-keyword-group boundary artifact that did NOT reproduce; summary + spurious tied-to-better for combined). 57.152 default validated. NO src change.
- CHANGE-121 + design note 57 + 3-run artifact.

## Q2 — Estimate accuracy (calibration)

- Plan §7: bottom-up ~6.5 hr → class-calibrated commit ~3.9 hr (NEW class `memory-formation-combine-ab-spike` 0.60), agent_factor 1.0 (parent-direct).
- Actual ≈ 3.7–4.0 hr equivalent (clean harness/corpus/tests in ~1 pass each + minor lint fixes; the extra wall-clock was the `.env`-at-root discovery for the Azure run + the 3× re-run to settle the borderline first result + the honest-finding interpretation).
- **Ratio ≈ actual/committed ≈ 0.95–1.03 → IN band** → **KEEP `memory-formation-combine-ab-spike` 0.60** (1st data point). Anchors held: `verification-context-hygiene-spike` 0.60 (57.136) + `verification-keycondition-spike` 0.60 (57.138) + the sibling `memory-formation-combine-spike` 0.60 (57.152) — same measurement-harness spike shape with a real-code core (~370-line harness + capturing doubles + Hybrid oracle + 10-case corpus + 24 tests ≥~3.5 hr) that held the 0.60 per the 57.137 lesson (NOT a tiny-code 0.85 re-point).

## Q3 — What went well?

- **Day-0 三-prong clean** (scope-shift ~0%): the only drift was the anticipated NEW `tests/fixtures/memory/` category dir; the capture-signature reads made the doubles byte-faithful first try; the AP-8-scope + cheap-profile + importlib-shadow facts were all confirmed pre-code (no mid-sprint surprise).
- **Capturing-sink design** drove the REAL worker end-to-end with zero src change + zero AP-10 divergence — the cleanest possible faithful A/B.
- **Honest-finding discipline paid off**: the mechanical single-run verdict FLIPPED on Run 1; instead of taking it at face value (a default flip) OR tuning the threshold to force a KEEP, re-ran 2× → the −5pp did NOT reproduce → correctly settled as LLM noise. The 3-run majority + understanding the −5pp mechanism (one keyword-group, one case, exact boundary, float epsilon) is the defensible, non-outcome-engineered call.

## Q4 — What to improve?

- **Single-run verdict variance**: a 10-case corpus swings ±5pp on facts from one case. The plan mirrored the single-run sibling harnesses; the borderline first run forced a manual 3× repeat. A `--runs N` averaging flag (`AD-Memory-Formation-AB-Robustness-MultiRun`) would make the verdict robust upfront — a small harness follow-on.
- **`.env` location**: the harness needed the root `.env` (not `backend/.env`); the first real run failed on missing Azure env until loaded via python-dotenv + runpy. A one-line note in the harness docstring on how to supply env for the on-demand run would save the rediscovery (the sibling harnesses have the same implicit dependency).

## Q5 — Anti-pattern self-check

- **AP-2** (side-track): the harness is reachable via its `main()` + the CI unit test; not orphan. ✅
- **AP-3** (scattering): formation-eval tooling lives in `backend/scripts/` with the benchmark family; the corpus under `tests/fixtures/memory/` (Cat 3). ✅
- **AP-4** (Potemkin): the harness runs the REAL production formation path (not a stub); the 24 tests + the real-Azure run prove it works. ✅
- **AP-6** (future-proofing abstraction): no speculative abstraction; consumes existing ABCs/workers as-is. ✅
- **AP-8** (naked prompt): the self-contained summary-judge ChatRequest is in `backend/scripts/` (outside the AP-8 lint root `backend/src/agent_harness`); confirmed Day-0. ✅
- **AP-10** (mock-vs-real divergence): the ONLY doubles are the terminal DB sinks; the prompt/chat/parse/dispatch path is production code. ✅
- **AP-11** (version suffix): none. ✅
- v2 lints: **run_all 11/11**. ✅

## Q6 — Carryover / open items

- `AD-Memory-Formation-AB-Robustness-MultiRun` — a `--runs N` averaging flag to remove the single-run ±5pp variance.
- `AD-Memory-Combined-Formation-PerTenant-Phase58` — C3 per-tenant combined/separate override.
- Extend the A/B to weaker models / harder corpora if a future strong-model verdict is inconclusive.
- (Pre-existing, not this sprint) `AD-Verification-Judge-Memory-Inject-Blind` was closed 57.153; `AD-Memory-Combined-Formation-AB-Quality` is closed here.

## Q7 — Design Note Extract (spike sprint — 8-point gate)

**File**: `docs/03-implementation/agent-harness-planning/57-memory-combined-formation-quality-ab-design.md`
**Verified ratio (estimated)**: ~95% (every technical claim carries a file:line or a verification command; the only unverified items are explicitly in §5 Open Invariants).
**8-Point Quality Gate**:
- [x] 1. Section header maps to the spike US (§1 "measure combined-vs-separate formation quality")
- [x] 2. file:line per technical claim (`formation.py:151/176/193`, `user_layer.py:124`, `session_summary_store.py:117`, test names)
- [x] 3. Decision matrix (§2.1 oracle 3-way + §2.2 driving 3-way + §2.3 judge 2-way)
- [x] 4. Verification command (`pytest …` + `RUN_AZURE_INTEGRATION=1 python scripts/…`)
- [x] 5. Test fixture reference (`memory_formation_quality_cases.yaml` + the 24-test file)
- [x] 6. Open-invariant split (§5 verified vs deferred — single-run variance / weaker models / per-tenant)
- [x] 7. Rollback path (§6 — 1-line config default flip; the fallback IS the battle-tested 57.149/151 path)
- [x] 8. 17.md cross-ref (§4 — no new contract; consumes ChatClient ABC §2.1)
**Reviewer pass**: self-review.
