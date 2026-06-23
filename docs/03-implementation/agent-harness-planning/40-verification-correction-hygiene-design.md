---
title: 40-verification-correction-hygiene design note
purpose: Spike-extract design note from Sprint 57.136; documents the measured self-conditioning effect at the 2-turn verification-correction horizon + the pluggable correction-context strategy
category: V2 extension docs (post-22-sprint era)
created: 2026-06-23 (Sprint 57.136 Day 4 closeout)
sprint_source: 57.136
verified_ratio: ≥ 95% (per 8-Point Quality Gate)
status: Active
---

# 40 — Verification Correction-Context Hygiene Design Note (Sprint 57.136 extract)

## 8-Point Quality Gate (self-check)

- [x] **1. Section headers map to spike user stories** (§2.1 US-1 / §2.2 US-2 / §2.3 US-3 / §2.4 US-4)
- [x] **2. Every technical claim has file:line** (loop.py:385/452/2645 · config:142 · handler.py:673-676/705 · script + fixture + test paths)
- [x] **3. Decision rationale includes a comparison matrix** (§1 the keep-vs-summarize A/B + the materiality-threshold decision)
- [x] **4. Reproducible verification command** (§2.x per invariant + §3 A/B rerun command)
- [x] **5. Test fixture reference** (`correction_hygiene_cases.yaml` + the real-LLM cost note)
- [x] **6. Open-invariant boundary explicit** (§4 — what this spike did NOT verify)
- [x] **7. Rollback / fallback path** (§5 — env-gate + revert; keep IS the pre-sprint path)
- [x] **8. 17.md single-source cross-ref** (§3 — NO new cross-category contract; justified N/A)

---

## 0. Spike Summary

- **Sprint scope**: US-1 pluggable correction-context strategy · US-2 config/env wire · US-3 real-LLM A/B measurement · US-4 mandatory chat-v2 drive-through · US-5 closeout. Closes `AD-Verification-Retry-Context-SelfConditioning` (research #6).
- **Verified period**: 2026-06-23 (Day 0–3).
- **Calibration**: bottom-up ~13 hr → class-calibrated commit ~7.8 hr (`verification-context-hygiene-spike` 0.60, agent_factor 1.0). Day-4 retro Q2 ratio.
- **Verification**: pytest +18 (3 loop-gate correction tests + 15 hygiene-harness tests) → 2765 passed + 5 skip; mypy 0/374; v2 lints 10/10; 1 real-Azure A/B (40 calls); drive-through PASS (backend runtime + UI).
- **Headline**: at the 2-turn correction horizon the self-conditioning effect is **directionally real but immaterial** (repeat −4.3pp, below the 5% threshold; both arms 100% retry-pass). `keep` stays default; `summarize` ships as an env opt-in lever. #6 = low-risk.

## 1. Decision Matrix — `keep` vs `summarize` (the spike's core evidence)

Real Azure, 10 fail-prone cases × 2 arms = 40 LLM calls (action-tier retry + cheap-tier `output_quality` judge):

| metric | keep (re-show failed answer) | summarize (drop failed answer) | delta (summ−keep) | materiality |
|--------|------------------------------|--------------------------------|-------------------|-------------|
| `retry_pass_rate` | 100% (10/10) | 100% (10/10) | +0.00% | — |
| `repeat_error_rate` (token-Jaccard retry↔failed) | 0.207 | 0.165 | **−0.043** | < 5% threshold → immaterial |
| `mean_prompt_tokens` | 80.0 | 62.8 | −17.2 | secondary benefit |

**Chosen: `keep` default.** Reason (not "best practice"): the self-conditioning hypothesis is directionally confirmed (summarize lowers the failed-answer repeat AND cuts tokens), but the repeat delta is **below the pre-registered 5% materiality threshold** and both arms retry to a passing answer 100% of the time. Flipping the default would change behavior for a sub-threshold gain and risk an unmeasured regression on harder distributions. **Rejected `summarize`-as-default**: effect immaterial at 2 turns; keeping `keep` preserves byte-identical behavior and zero rollback risk. The mechanism still ships (cheap option value, env-togglable).

**Honesty caveat**: 10 controlled-first-fail cases where `suggested_correction` already names the right answer → both arms anchor on the correct vocabulary → the measured effect is compressed. This is a spike directional read, not a production-distribution statistic. The harness is permanent and re-runnable on a larger / harder fixture (§3 command).

## 2. Verified Invariants

### 2.1 US-1 — Pluggable correction-context strategy (`keep` byte-identical / `summarize` drops)

- **Implementation**: ctor param `correction_context_strategy: str = "keep"` at `backend/src/agent_harness/orchestrator_loop/loop.py:385`; stored `self._correction_context_strategy` at `:452`; branch guard at `:2645` — `if self._correction_context_strategy != "summarize": messages.append(Message(role="assistant", content=parsed.text))`.
- **Behavior**: `keep` (and any non-`summarize` value) re-appends the failed answer (pre-57.136 bytes); `summarize` drops it, leaving only the `user(correction_block)` feedback to continue. `verification_attempts` counter + checkpoint untouched (strategy affects message shape only, not the count).
- **Verification**: `cd backend && pytest tests/unit/agent_harness/orchestrator_loop/test_loop_verification_gate.py -k correction -q` → 3 passed.
- **Test fixture**: `_BadWordVerifier` + `FakeChatClient` + `_build_loop` helper in the same test file (no external fixture; the 5 pre-existing gate tests = the keep byte-identical regression guard).

### 2.2 US-2 — Config/env wire (settings-only, per-tenant OUT)

- **Implementation**: `chat_verification_correction_strategy: str = "keep"` at `backend/src/core/config/__init__.py:142` (env `CHAT_VERIFICATION_CORRECTION_STRATEGY`); resolved + validated in `backend/src/api/v1/chat/handler.py:673-676` (`not in ("keep","summarize") → "keep"`); threaded `correction_context_strategy=` into `AgentLoopImpl(...)` at `handler.py:705`.
- **Behavior**: mirrors the `verification_escalate_on_max` 3-layer wire (config→handler→loop) minus the per-tenant `policy.*` layer (OUT — anti-AP-6). `str` (not `Literal`) + handler fallback so an unknown env value degrades to `keep` rather than crashing startup. Defense-in-depth: the loop's own `!= "summarize"` guard makes a direct `AgentLoopImpl` caller (bypassing the handler) safe too.
- **Verification**: `cd backend && pytest tests/unit/api/v1/chat/test_handler.py -q` → 10 passed (incl. the `_force_verification_enabled` stub now mirroring the new settings field).

### 2.3 US-3 — Real-LLM A/B measurement harness

- **Implementation**: `backend/scripts/benchmark_correction_hygiene.py` (NEW; mirrors `benchmark_judge.py` scaffold: `load_cases` / `build_correction_messages` / `token_jaccard` / `run_arm` / `build_report` / `report_to_markdown` / `_amain` / `main` + frozen `HygieneCase`/`ArmRun`/`HygieneReport` dataclasses + lazy Azure import). Reproduces the loop's `:2645` two-construction WITHOUT the full loop (isolates the failed-answer-in-context as the only variable); both arms import the real `_build_correction_block` from `loop.py`.
- **Behavior**: `repeat_error_rate = token-Jaccard(retry_answer, failed_answer)` (LOWER = less self-conditioning); a negative repeat-delta OR positive pass-delta beyond the 5% threshold flips the default.
- **Verification (CI-safe)**: `cd backend && pytest tests/unit/scripts/test_benchmark_correction_hygiene.py -q` → 15 passed (importlib-load idiom avoids the `tests.unit.scripts` shadow; MockChatClient + spy judge; covers load/build/jaccard/run_arm/build_report).
- **Verification (real Azure)**: `cd backend && RUN_AZURE_INTEGRATION=1 AZURE_OPENAI_*=... python scripts/benchmark_correction_hygiene.py` → writes `benchmark_reports/` (gitignored; copied to `artifacts/correction_hygiene_report.{md,json}`). **Cost**: ~40 Azure calls per run (10 cases × 2 arms × [retry + judge]).
- **Test fixture**: `backend/tests/fixtures/verification/correction_hygiene_cases.yaml` (10 plausible-but-wrong cases: RGB↔RYB, O(n)↔O(log n), H2O↔NaCl, Saturn↔Jupiter, 0°C↔32°F, items[0]↔items[-1], 1959↔1969, …; each with verifier reason + suggested_correction).

### 2.4 US-4 — Drive-through (real UI + backend + LLM)

- **Backend runtime** (real `build_real_llm_handler()` loop + real Azure + controlled fail-once verifier, `checkpointer/message_store/reducer=None` → no DB): wiring env→loop (`keep`/`summarize`/`banana`→`keep`); both arms emit `VerificationFailed → retry → VerificationPassed → LoopCompleted`; keep retry context `roles=[system×3, user, assistant, user]` (assistant_count=1) vs summarize `[system×3, user, user]` (assistant_count=0, dropped; real Azure accepts consecutive user). This is the strongest evidence — the ACTUAL `loop.run()` via the real handler builder, not a reproduced construction.
- **UI** (chat-v2, real Azure gpt-5.2, jamie@acme.com·operator·acme-prod): main flow end-to-end (send→answer render) + verification gate on the main flow (Inspector "claim verified · llm_judge" 0.93 + Loop visualizer `verification_passed`) + the `:2645` change did NOT break the verification pass path (no-regression). Both real-Azure turns passed the strict judge → no UI correction triggered (the 57.99-documented "real fail can't be forced cleanly"); the correction loop + drop is proven by the deterministic backend runtime drive-through + the 57.98/99 prior UI correction-render drive-throughs.
- **Evidence**: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-136/artifacts/dt-57136-keep-verification-passed.jpeg` + progress.md Day 3 (UI + runtime tables).

## 3. Cross-Category Contracts

**No new cross-category contract** — nothing to register in `17-cross-category-interfaces.md`. The strategy is a **Cat 1 internal ctor param** on `AgentLoopImpl`, threaded via the EXISTING config→handler→loop wire pattern (the same seam `verification_escalate_on_max` already uses; that pattern is the established convention, not a new contract). No new ABC, no new wire event (`WIRE_SCHEMA` stays 25), no new DB table. The existing `VerificationFailed`/`VerificationPassed` SSE stream is unchanged. Per the single-source rule, adding a row to 17.md would be noise — this is correctly N/A.

## 4. Open Invariants (deferred / NOT verified in this spike)

- [ ] **Per-tenant `correction_context_strategy`** — OUT this sprint (anti-AP-6); the C3 `harness_policy` seam owns per-tenant verification overrides. → `AD-Verification-Correction-Strategy-PerTenant-Phase58`.
- [ ] **Self-conditioning at >2 correction turns** — `max_correction_attempts = 2` is the only horizon measured. A deeper retry budget could compound self-conditioning; not measured here.
- [ ] **Production-distribution magnitude** — the 10-case controlled-first-fail fixture compresses the effect (both arms anchor on the suggested correct answer). The harness is re-runnable on a larger / adversarial fixture if a future sprint wants a tighter number.
- [ ] **Generalizing context hygiene to other loop paths** (e.g. tool-error retry) — NOT in scope; #6 is the verification-correction path only.
- [ ] **`summarize` as default** — deferred pending a material A/B signal; current evidence keeps `keep`.

## 5. Rollback / Fallback

- **If `summarize` ever proves harmful**: it is NOT the default — leave/set `CHAT_VERIFICATION_CORRECTION_STRATEGY=keep` (the pre-57.136 byte-identical path). Zero code change needed.
- **If the whole mechanism must be reverted**: revert the 3 src edits (`loop.py:385/452/2645`, `config:142`, `handler.py:673-676/705`) — the `keep` arm IS the original code, so a revert restores exact prior behavior. Estimated effort ~30 min.
- **Sentinel already in place**: the handler's `not in ("keep","summarize") → "keep"` fallback + the loop's `!= "summarize"` guard mean any misconfiguration degrades to the safe pre-sprint behavior automatically.

## 6. References

- Sprint plan: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-136-plan.md`
- Sprint checklist: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-136-checklist.md`
- Sprint progress + retrospective: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-136/{progress,retrospective}.md`
- Change record: `claudedocs/4-changes/feature-changes/CHANGE-103-verification-correction-hygiene.md`
- AD source: `claudedocs/1-planning/next-phase-candidates.md` §Research-Derived Candidates (`AD-Verification-Retry-Context-SelfConditioning`)
- Mirrored scaffold: `backend/scripts/benchmark_judge.py` (Sprint 57.111 A3)
- Related design: `docs/03-implementation/agent-harness-planning/01-eleven-categories-spec.md` §範疇10 (Verification Loops) + §範疇1 (Orchestrator Loop)
- Research: arXiv 2509.09677 §7 (self-conditioning)

## Modification History

- 2026-06-23: Initial extract from Sprint 57.136 closeout (Day 4) — measured self-conditioning effect (immaterial at 2 turns) + pluggable strategy + keep-default verdict
