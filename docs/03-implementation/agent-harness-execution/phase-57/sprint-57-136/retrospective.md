# Sprint 57.136 Retrospective — verification correction context hygiene (self-conditioning spike)

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-136-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-136-checklist.md) · [Progress](./progress.md)

**Closed**: 2026-06-23 · **Branch**: `feature/sprint-57-136-verification-correction-hygiene` · **Base**: main `074362c4`

---

## Q1. What was delivered?

A thin evidence-first spike closing `AD-Verification-Retry-Context-SelfConditioning` (research #6). The in-loop verification correction branch (`loop.py:2645`) was parameterized via `correction_context_strategy` ∈ {`keep` (default, byte-identical) / `summarize` (drop the failed answer to break self-conditioning)}, wired through `CHAT_VERIFICATION_CORRECTION_STRATEGY` settings (config:142 → handler.py:673-676/705), and a permanent real-LLM A/B harness (`benchmark_correction_hygiene.py` + 10-case golden fixture + 15 CI-safe tests) measured the effect before deciding the default. **Verdict: keep stays default** — self-conditioning is directionally real (repeat −4.3pp, tokens −17.2) but immaterial at the 2-turn horizon (< 5% threshold; both arms 100% retry-pass); `summarize` ships as an env opt-in lever. Backend-only, NO migration / NO new wire event / NO frontend. CHANGE-103 + design note 40.

## Q2. Calibration — estimate vs actual

- **Scope class**: `verification-context-hygiene-spike` **0.60** (NEW, 1st data point). Analogous to `verification-in-loop-spike` 0.60 (57.98) + `verification-trace-and-benchmark-spike` 0.60 (57.111) — both loop.py-core verification touches paired with a measurement script.
- **Agent-delegated: no** (parent-direct; the value is precise judgment of self-conditioning evidence + a surgical loop.py branch, not mechanical pattern reuse). `agent_factor` 1.0 → 3-segment form.
- **Estimate**: bottom-up ~13 hr → class-calibrated commit ~7.8 hr (mult 0.60).
- **Actual**: ~7–8 hr (Day 0 三-prong ~1 · Day 1 strategy+config+unit ~2.5 · Day 2 harness+fixture+CI test+A/B ~3 · Day 3 drive-through+decision ~1.5 · Day 4 closeout ~1.5, overlapping same-day). **Ratio actual/committed ≈ 1.0 — IN band.** Single data point → KEEP 0.60 pending 2–3 sprint validation. If a 2nd `verification-context-hygiene-spike` diverges > 30%, re-point.
- The Day-0 三-prong NET-reduced scope (D-azure-role-pairing RESOLVED → drop-only, no placeholder path; ~−5%) while D-benchmark-anchor nuance ADDED ~+5% (drive a correction cycle vs single verifier scoring) → net wash, the 0.60 held cleanly.

## Q3. What went well?

- **Evidence-first discipline held**: measured the effect with a real-LLM A/B BEFORE touching the default. A blind flip to `summarize` would have shipped a sub-threshold behavior change with regression risk; the number gated the decision (negative-ish result is a valid spike outcome).
- **Day-0 三-prong paid off**: D-azure-role-pairing (grep `tool_converter.py` + the 57.101 injection precedent) resolved the biggest scope lever at Day 0 — `summarize` = clean DROP, no `_WITHHELD_PLACEHOLDER` path → less code, no dead code (AP-2 / Karpathy §3).
- **keep-as-default = zero rollback risk**: the default arm is byte-identical to pre-sprint; the unit test asserts it, and both the handler fallback + the loop guard degrade any misconfiguration to safe behavior (defense-in-depth, ~1 line each).
- **Mechanism reuse**: composed existing machinery (the 2645 correction append + the `verification_escalate_on_max` config wire + the `benchmark_judge.py` measurement scaffold) — no new primitive, schema, or wire event.
- **Drive-through "兩者結合" was honest**: backend runtime (deterministic, real Azure, full real handler→loop) proved the correction loop + drop; UI proved main-flow/gate/no-regression. We did NOT claim the UI drove the correction path (real judge passes good answers — the 57.99 limitation); we said so plainly.

## Q4. What to improve next sprint?

- **Partial-gate scope** (the key process lesson — see Q6): a changed src file's FULL test surface belongs in the partial gate, not just the new tests. Day 1's partial gate ran only the 2 files I authored; it missed `test_handler.py` (which exercises the handler I edited) → 2 regressions surfaced only at the Day-2 full gate.
- **Real-fail-on-demand for verification drive-through** remains unsolved (57.99 carryover): the strict real judge passes good answers, so a UI correction loop can't be forced cleanly. The deterministic backend-runtime drive-through is the honest substitute, but a reusable "force one real verification fail in the UI" lever would make future verification-path drive-throughs first-class.

## Q5. Anti-pattern self-check (04-anti-patterns / 11-point)

- **AP-1** (pipeline-as-loop): N/A — the correction path is the existing `while`/`continue` loop; unchanged.
- **AP-2** (orphan/dead code): ✅ `_WITHHELD_PLACEHOLDER` deliberately NOT defined (would be dead) — demoted to an inline comment fallback note. The `keep` arm is the live default; `summarize` is reachable via env + tested.
- **AP-3** (cross-dir scatter): ✅ Cat 1 change in `loop.py`; Cat 4 setting in `core/config`; Cat 10 eval in `scripts/` + `tests/`. Each in its home.
- **AP-4** (Potemkin): ✅ both arms drive-through-verified at runtime (not just gate); the harness produces a real number; the strategy actually changes the message shape (assistant_count 1 vs 0, proven).
- **AP-6** (future-proofing): ✅ per-tenant strategy explicitly OUT (→ C3); settings-only this sprint — no speculative policy layer.
- **AP-8** (no centralized PromptBuilder): N/A — no prompt assembly added; the correction block uses the existing `_build_correction_block`.
- **AP-11** (version suffix / misnaming): ✅ no `_v2`/`_old`; `correction_context_strategy` names exactly what it does.
- **v2 lints**: 10/10 (incl. check_llm_sdk_leak — the harness builds the Azure profile via the neutral path, like `benchmark_judge.py`).

## Q6. Process lesson (for the matrix / future plans)

**A changed src file's FULL existing test surface belongs in the partial gate.** Day 1's partial gate ran only `test_loop_verification_gate.py` + `test_config_verification.py` (the 2 files I authored) and reported green — but I had also edited `handler.py`, whose tests (`test_handler.py`) monkeypatch `get_settings()` to a `SimpleNamespace` stub. My new unconditional `settings.chat_verification_correction_strategy` read hit `AttributeError` on that stub → 2 regressions that only surfaced at the Day-2 full gate. Fix was trivial (add the field to the stub, the same pattern as the 57.99 A2 `escalate_on_max` addition), but the lesson is: **when you edit src file X, the partial gate must include X's existing tests, not just the tests you wrote.** (Recorded; not yet a formal rule promotion — single occurrence.)

## Q7. Carryover / open items

- `AD-Verification-Correction-Strategy-PerTenant-Phase58` — per-tenant `correction_context_strategy` via the C3 `harness_policy` seam (registered in next-phase-candidates).
- Self-conditioning at >2 correction turns + production-distribution magnitude — the harness is permanent + re-runnable on a larger/adversarial fixture if a future sprint wants a tighter number (design note §4).
- `AD-Verification-Retry-Context-SelfConditioning` itself — **CLOSED** (mechanism shipped + measured; #6 low-risk at 2 turns).

---

## Design Note Extract (spike sprint)

**File**: `docs/03-implementation/agent-harness-planning/40-verification-correction-hygiene-design.md`
**Verified ratio (estimated)**: ≥ 95% (every claim file:line-anchored; the A/B is a reproducible real-Azure run)
**8-Point Quality Gate**:
- [x] 1. Section header maps to US
- [x] 2. file:line references
- [x] 3. Decision matrix (the keep-vs-summarize A/B)
- [x] 4. Verification command (per invariant + A/B rerun)
- [x] 5. Test fixture (`correction_hygiene_cases.yaml` + real-LLM cost note)
- [x] 6. Open-invariant boundary
- [x] 7. Rollback path (env-gate + revert; keep IS the pre-sprint path)
- [x] 8. 17.md cross-ref (NO new contract — justified N/A)

**Reviewer pass**: self-review (solo-dev)
