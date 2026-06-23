# Sprint 57.136 Plan — verification correction context hygiene (self-conditioning spike)

**Summary**: Close `AD-Verification-Retry-Context-SelfConditioning` (research #6, the highest-tension item from the 2026-06-22 reconciliation). The in-loop A1 verification correction (`loop.py:2620`) appends the *failed assistant answer verbatim* back into context before retrying — exactly the self-conditioning shape research §7 warns about. This is a **thin spike**: parameterize the correction-context handling (`keep` default = byte-unchanged rollback / `summarize` = drop the verbatim failed answer, keep only the distilled feedback), then **measure the effect with a real-LLM A/B** (mirror `benchmark_judge.py`) before deciding the default. Drive-through is MANDATORY (correction runs on the chat-v2 主流量). A **design note (spike sprint)** is required — its headline is the measured self-conditioning effect at the 2-turn horizon + the strategy decision.

**Status**: Draft (user said「開始規劃和設計 #6」2026-06-23; awaiting plan approval before Day-0 / code)
**Branch**: `feature/sprint-57-136-verification-correction-hygiene`
**Base**: `main` HEAD `074362c4` (PR #324 — consolidated agent-harness research + V2 mapping)
**Slice**: closes `AD-Verification-Retry-Context-SelfConditioning` (standalone; the #6 tension from `next-phase-candidates.md` §Research-Derived Candidates)
**Scope decisions**: (a) thin spike — measure BEFORE changing the default, not a blind refactor; (b) strategy via ctor param + `CHAT_VERIFICATION_CORRECTION_STRATEGY` settings, mirroring `verification_escalate_on_max`'s 3-layer wire; (c) per-tenant policy override is OUT (→ C3 follow-up); (d) `keep` stays the default unless the A/B shows `summarize` is materially better — evidence gates the flip.

---

## 0. Background

### The gap (`AD-Verification-Retry-Context-SelfConditioning`)

- When the in-loop Cat 10 verifier fails a candidate answer and budget remains, the loop appends the **failed assistant answer verbatim** then a correction message and continues the SAME loop.
- The next correction turn's context therefore carries the model's own just-failed output.
- Research §7 (arXiv 2509.09677): a model that sees its own failure in context tends to **repeat** it (self-conditioning), and this is NOT fixed by model scale.
- Confirmed code-grounded 2026-06-23 (see Root cause); the structural risk is real — the effect *magnitude* at this repo's 2-turn horizon is what the spike measures.

### Why it matters (the missing capability)

Enterprise verification/retry is supposed to *raise* answer quality. If the corrector re-reads its own failed answer and self-conditions, the second attempt can repeat the first's error — verification spends judge tokens + a turn and delivers the same defect. The remedy (retry from a clean-er context) is a known mitigation but its efficacy here is unmeasured; the spike settles whether the cost of changing is justified.

### Root cause (recon code read, file:line; ALL re-verified §checklist 0.1)

| Layer | Reality (on `main` HEAD `074362c4`) | Anchor |
|-------|-------------------------------------|--------|
| correction branch keeps the failed answer | `messages.append(Message(role="assistant", content=parsed.text))` then the correction `user` message, then `continue` | `loop.py:2620-2626` |
| self-documented as intentional | docstring: *"the conversation — including the just-failed assistant answer — is already in `messages`"* | `loop.py:299-301` (`_build_correction_block`) |
| feedback already carries the "why" | correction block = `Previous attempt failed verification: {reasons}` + `Suggested: {corrections}` + `Please retry.` | `loop.py:303-309` |
| A3 does NOT address it | trace-aware judge makes the *judge* smarter, not the *corrector's* context | `loop.py:1702-1707` |
| config wire anchor to mirror | `verification_escalate_on_max`: ctor param ← `policy.* or settings.*` ← `AgentLoopImpl(...)` | `handler.py:666-671, 683-696` |
| measurement framework to mirror | `load_cases / run_judge / build_report / main()` + golden YAML + `@pytest.mark.benchmark` | `scripts/benchmark_judge.py` |

→ The fix must (1) make the correction-context handling pluggable (default `keep` = current bytes), (2) provide a `summarize` arm that drops the verbatim failed answer while preserving the distilled feedback, and (3) produce a real-LLM A/B number that gates the default.

### The design (loop.py correction-branch parameterization + a mirror-benchmark measurement script)

```
# loop.py _run_turns, the outcome=="correct" branch (~2617-2626):
if verdict.outcome == "correct":
    if self._correction_context_strategy == "summarize":
        # drop the verbatim failed answer; keep role-pairing legal via a neutral
        # placeholder assistant turn (Day-0 confirms whether Azure accepts back-to-back
        # user msgs; if yes, the placeholder can be omitted). The distilled "why + how"
        # already lives in correction_block → the model still knows what to fix.
        messages.append(Message(role="assistant", content=_WITHHELD_PLACEHOLDER))
    else:  # "keep" (default — byte-identical to today)
        messages.append(Message(role="assistant", content=parsed.text))
    messages.append(Message(role="user", content=verdict.correction_block or ""))
    verification_attempts += 1
    turn_count += 1
    continue

# strategy wire (mirror verification_escalate_on_max, handler.py):
#   AgentLoopImpl(..., correction_context_strategy=<resolved>)
#   resolved = settings.chat_verification_correction_strategy  (per-tenant policy → C3 follow-up)

# measurement (mirror benchmark_judge.py):
#   scripts/benchmark_correction_hygiene.py — load fail-prone cases → run both arms on real
#   Azure → build_report: retry_pass_rate, repeat_error_rate (self-conditioning signal),
#   prompt_tokens delta. pytest wrapper @pytest.mark.benchmark (skipif RUN_AZURE_INTEGRATION).
```

WHY this over a blind refactor: research confirms the *risk* but not the *magnitude* at 2 turns; flipping the default without a number would violate evidence-first discipline and risk a regression (a too-aggressive context strip could *lower* retry quality). The `keep` default + env toggle = zero-risk rollback (mirrors the `chat_verification_mode` gate, proposal §1.5).

### Ground truth (recon head-start — code read on `main` HEAD `074362c4`; ALL re-verified §checklist 0.1)

- `loop.py:2617-2626` — the only correction-append site (the `outcome=="correct"` branch).
- `loop.py:295-309` — `_build_correction_block` returns reasons + suggested_correction → the `summarize` arm relies on this so the model still gets "what failed + how to fix".
- `loop.py:364` — `max_correction_attempts: int = 2` (the 2-turn horizon the spike measures at).
- `loop.py:1669-1779` — `_cat10_verify_gate` (unchanged; the gate that returns the verdict).
- `handler.py:683-696` — the `AgentLoopImpl(...)` ctor call site (where `correction_context_strategy` is threaded).
- `scripts/benchmark_judge.py` + `tests/fixtures/verification/judge_benchmark.yaml` — measurement structure + golden-fixture pattern to mirror.

**Baselines (57.135 closeout)**: pytest 2747+5skip · wire 25 · Vitest 915 · mockup 51 · mypy 0/374 · run_all 10/10. Re-verify Day-0.

### STALE / drift findings (Day-0; full detail → progress.md — placeholder, filled in §checklist 0.1)

- **D-correction-branch** — re-grep `loop.py` `outcome=="correct"` branch still appends `assistant(parsed.text)` + `user(correction_block)` at ~2620 → confirms the single edit site.
- **D-azure-role-pairing** — verify whether Azure OpenAI accepts back-to-back `user` messages (decides whether `summarize` can fully DROP the assistant turn vs needs the neutral placeholder) → shifts §3.1 + §8 Risk row.
- **D-config-anchor** — confirm `verification_escalate_on_max` 3-layer wire still at `handler.py:666-696` → the strategy mirrors it.
- **D-benchmark-anchor** — confirm `benchmark_judge.py` `load_cases/run_judge/build_report/main` + fixture path → the spike script mirrors it.
- **D-build-correction-block** — confirm `_build_correction_block` (loop.py:295-309) still carries reasons + suggested_correction → the `summarize` arm depends on it.

## 1. Sprint Goal

Settle, with a real-LLM number, whether the A1 correction loop self-conditions at the 2-turn horizon, and ship a pluggable correction-context strategy (`keep` default / `summarize`) so the remedy is one config flip away once the evidence justifies it. PROVEN by: the full gate set + a real-Azure A/B run (`benchmark_correction_hygiene` report: retry_pass_rate / repeat_error_rate / token delta per arm) + a MANDATORY chat-v2 drive-through (construct fail-then-pass; Inspector shows VerificationFailed → correction turn → VerificationPassed → answer renders, under the active strategy). Produces **CHANGE-103** + a **design note (40)** carrying the measured effect + the strategy decision.

## 2. User Stories

- **US-1** (pluggable strategy): 作為 harness 維護者，我希望 correction-context 處理可由 strategy 切換（`keep`/`summarize`），以便在不改既有行為（`keep` byte-unchanged）的前提下能測試「清失敗答案」的緩解。
- **US-2** (config wire): 作為 operator，我希望 strategy 走 `CHAT_VERIFICATION_CORRECTION_STRATEGY` settings（鏡像 `verification_escalate_on_max`），以便無需改碼即可切換 arm 做 A/B、並保留 env-gate 回滾。
- **US-3** (measurement): 作為決策者，我希望有可重跑的 real-LLM A/B harness 量測 `keep` vs `summarize` 的 retry_pass_rate / repeat_error_rate / token，以便用證據（非假設）決定預設。
- **US-4** (drive-through, MANDATORY): 作為使用者，我希望在 chat-v2 觸發 fail-then-pass 時，correction 路徑在 active strategy 下仍正常（Inspector 顯示 fail→correct→pass、修正答案正確渲染）。
- **US-5** (closeout): 設計筆記（spike 8-point gate）+ CHANGE-103 + calibration + navigators/next-phase-candidates 更新（CLOSE the AD）。

## 3. Technical Specifications

### 3.0 Architecture (backend-only — NO migration / NO new wire event / NO frontend)

```
EDIT  backend/src/agent_harness/orchestrator_loop/loop.py   — ctor param + correction-branch strategy
EDIT  backend/src/core/config/__init__.py                   — chat_verification_correction_strategy setting (default "keep")
EDIT  backend/src/api/v1/chat/handler.py                    — resolve + thread strategy into AgentLoopImpl(...)
NEW   backend/scripts/benchmark_correction_hygiene.py       — real-LLM A/B (mirror benchmark_judge.py)
NEW   backend/tests/fixtures/verification/correction_hygiene_cases.yaml — fail-prone golden cases
NEW   backend/tests/unit/scripts/test_benchmark_correction_hygiene.py   — CI-safe (MockChatClient) load/run/report
EDIT  backend/tests/unit/orchestrator_loop/test_*correction*  — keep-arm byte-unchanged + summarize-arm context assertion
UNTOUCHED  loop.py _cat10_verify_gate / _build_correction_block content / VerificationFailed wire / resume() path
```

### 3.1 Correction-context strategy (US-1) — `loop.py`

- New ctor param `correction_context_strategy: str = "keep"` (stored `self._correction_context_strategy`); a module const `_WITHHELD_PLACEHOLDER` for the neutral assistant turn.
- In the `outcome=="correct"` branch (~2620): branch on the strategy. `keep` → current bytes exactly (rollback guarantee). `summarize` → append the neutral placeholder assistant turn (or, if Day-0 D-azure-role-pairing GREEN, omit it) instead of `parsed.text`; the `user(correction_block)` append is unchanged.
- `_build_correction_block` is UNCHANGED — it already distills reasons + suggested_correction, which is what makes `summarize` viable (model still knows what to fix without re-reading the failed answer).
- Durable `verification_attempts` counter UNCHANGED (the strategy only affects what messages carry, not the count / checkpoint).

### 3.2 Config wire (US-2) — `core/config` + `handler.py`

- `chat_verification_correction_strategy: str = "keep"` in `Settings` (env `CHAT_VERIFICATION_CORRECTION_STRATEGY`); validate ∈ {`keep`,`summarize`} (fall back to `keep` on unknown — fail-safe to current behavior).
- `handler.py`: resolve the value (settings only this sprint) and pass `correction_context_strategy=...` into the `AgentLoopImpl(...)` call (mirror the `verification_escalate_on_max` 3-layer pattern at `handler.py:666-696`; per-tenant `policy.*` layer is OUT — §9).

### 3.3 Measurement harness (US-3) — `scripts/benchmark_correction_hygiene.py` + fixture

- Mirror `benchmark_judge.py`: `load_cases(path)` (schema-validate the YAML) / `run_arm(strategy, cases, ...)` (drive a fail-then-retry through the real loop or a thin loop harness per arm) / `build_report(...)` (pure: retry_pass_rate, repeat_error_rate = similarity of retry answer to the failed answer, prompt_tokens mean per arm) / `main()` (build Azure profile, run both arms, write JSON report).
- Golden fixture `correction_hygiene_cases.yaml`: fail-prone cases (e.g. a prompt + a judge config that fails attempt 1 deterministically, so the retry is measurable). Day-0 decides the trigger mechanism (judge-threshold tweak vs a contradiction-inducing prompt).
- pytest wrapper `@pytest.mark.benchmark` skipif `RUN_AZURE_INTEGRATION`; unit test covers `load_cases`/`build_report`/`run_arm` with `MockChatClient` (CI-safe, like `test_benchmark_judge.py`).

### 3.4 Decision gate (US-3→US-4) — evidence → default

- After the Day-2 real-Azure A/B: if `summarize` shows materially higher retry_pass_rate AND/OR lower repeat_error_rate without a token blow-up → recommend flipping the default to `summarize` (the flip itself is a 1-line settings change, captured in the design note + CHANGE-103). If the effect is not material → keep `keep` as default, record the negative result, mark #6 low-risk; the mechanism still ships (cheap option value, env-togglable).
- Either outcome is a valid spike result; the design note records the number + the verdict + rollback.

### 3.x What is explicitly NOT done

- **Per-tenant `correction_context_strategy`** (via `harness_policy`) — OUT this sprint; C3 already owns the per-tenant verification-override seam (→ §9). Spike uses settings/env only.
- **Removing `keep`** — the default stays `keep` unless evidence flips it; no destructive removal of the current behavior.
- **Touching `_build_correction_block` content / the verdict gate / resume() path** — UNTOUCHED; strategy is purely the append shape in one branch.
- **A new wire event / Inspector field** — none; the existing `VerificationFailed`/`VerificationPassed` stream is unchanged.

### 3.y Validation (US-1..US-5)

Gates: mypy `src` 0/374 · run_all 10/10 · pytest 2747+ (+ new unit) · Vitest 915 (unchanged — no FE) · mockup 51 (`diff` empty — no FE) · `npm run lint && npm run build` (NO `--silent`) · black/isort/flake8 clean · LLM-SDK-leak clean (the spike script's `main()` builds the Azure profile via the existing neutral path, like `benchmark_judge.py`). Plus the §3.4 real-Azure A/B report + the MANDATORY §US-4 drive-through.

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `backend/src/agent_harness/orchestrator_loop/loop.py` | EDIT (ctor param + correction-branch strategy + `_WITHHELD_PLACEHOLDER`) |
| 2 | `backend/src/core/config/__init__.py` | EDIT (`chat_verification_correction_strategy` setting) |
| 3 | `backend/src/api/v1/chat/handler.py` | EDIT (resolve + thread strategy) |
| 4 | `backend/scripts/benchmark_correction_hygiene.py` | NEW (real-LLM A/B harness) |
| 5 | `backend/tests/fixtures/verification/correction_hygiene_cases.yaml` | NEW (golden fail-prone cases) |
| 6 | `backend/tests/unit/scripts/test_benchmark_correction_hygiene.py` | NEW (CI-safe load/run/report) |
| 7 | `backend/tests/unit/orchestrator_loop/test_*correction*.py` | EDIT (keep byte-unchanged + summarize context assertion) |
| 8 | `claudedocs/4-changes/feature-changes/CHANGE-103-verification-correction-hygiene.md` | NEW |
| 9 | `docs/03-implementation/agent-harness-planning/40-verification-correction-hygiene-design.md` | NEW (spike design note) |
| — | `loop.py` `_cat10_verify_gate` / `_build_correction_block` body / `resume()` / wire schema | **UNTOUCHED** |
| — | any frontend / migration / new DB table | **UNTOUCHED** |

## 5. Acceptance Criteria

1. `correction_context_strategy` ctor param + `keep`/`summarize` branch in `loop.py`; `keep` arm produces byte-identical messages to pre-sprint (unit test asserts).
2. `summarize` arm omits the verbatim failed answer (asserted via unit test on resulting `messages`), keeps role-pairing legal, and the correction `user` message (with reasons + suggested_correction) is unchanged.
3. `CHAT_VERIFICATION_CORRECTION_STRATEGY` settings resolves + threads into `AgentLoopImpl`; unknown value falls back to `keep`.
4. `benchmark_correction_hygiene.py` runs a real-Azure A/B producing retry_pass_rate / repeat_error_rate / token-delta per arm; CI-safe unit test covers the pure logic with `MockChatClient`.
5. **Drive-through PASS (MANDATORY, real UI + backend + LLM)** — chat-v2 fail-then-pass: Inspector shows VerificationFailed(attempt=1) → correction turn → VerificationPassed → answer renders, under the active strategy; screenshot + observed-vs-intended in progress.md. (NOT gate-only.)
6. `AD-Verification-Retry-Context-SelfConditioning` CLOSED; CHANGE-103 + design note 40 (8-point gate); calibration recorded; navigators + next-phase-candidates updated.

## 6. Deliverables

- [ ] US-1 `correction_context_strategy` ctor param + correction-branch strategy in `loop.py`
- [ ] US-2 `chat_verification_correction_strategy` setting + handler thread
- [ ] US-3 `benchmark_correction_hygiene.py` + golden fixture + CI-safe unit test + real-Azure A/B report
- [ ] US-4 chat-v2 fail-then-pass drive-through (MANDATORY)
- [ ] US-5 design note 40 + CHANGE-103 + closeout

## 7. Workload Calibration

- Scope class **`verification-context-hygiene-spike` 0.60** (NEW class, 1st data point; analogous to `verification-in-loop-spike` 0.60 (57.98) + `verification-trace-and-benchmark-spike` 0.60 (57.111) — both loop.py-core verification touches paired with a measurement script; cite `.claude/rules/sprint-workflow.md` §Scope-class multiplier matrix).
- **Agent-delegated: no** (parent-direct; the spike's value is precise judgment of self-conditioning evidence + a surgical loop.py branch — not mechanical pattern reuse). `agent_factor` 1.0 → 3-segment form.
- Bottom-up est ~13 hr (Day0 三-prong ~1 · loop.py strategy + config + unit ~3 · spike script + fixture + A/B run ~4 · drive-through + decision gate ~2.5 · design note + CHANGE + closeout ~2.5) → class-calibrated commit ~7.8 hr (mult 0.60). Day-4 retro Q2 verifies.

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| **Azure rejects back-to-back `user` messages** → `summarize` can't fully drop the assistant turn | Day-0 D-azure-role-pairing decides; fallback = neutral `_WITHHELD_PLACEHOLDER` assistant turn (keeps alternation legal, still hides the failed answer) |
| `summarize` strips too much → *lower* retry quality (regression) | The A/B measures exactly this; `keep` stays default unless evidence flips it; env-gate rollback |
| Deterministic fail-then-retry hard to construct for the harness | Day-0 picks the trigger (judge-threshold tweak vs contradiction-inducing prompt); same lever the proposal §1.6 DoD anticipates |
| Stale `--reload` backend masks the strategy wire (startup-resolved) | Risk Class E: clean restart + confirm sole live worker + startup log before drive-through (the 57.97 spawn-worker trap) |
| Module-level singletons across test loops | Risk Class C: autouse reset fixture if the spike harness touches a cached factory |
| `keep` arm accidentally changes bytes | Unit test asserts byte-identical messages for `keep` (the rollback guarantee) |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- **Per-tenant `correction_context_strategy`** — → C3 follow-up (`harness_policy` already owns per-tenant verification overrides; `AD-Verification-Correction-Strategy-PerTenant-Phase58`).
- **The other 7 research opportunities** (#2 pass^k / #3 detect→restrict / #4 layered compaction / #5 OTel / #7 tool-lint / #8 key-condition) — stay registered in `next-phase-candidates.md` §Research-Derived Candidates; selection-gated.
- **Generalizing context hygiene to other loop paths** (e.g. tool-error retry) — not in scope; #6 is the verification-correction path only.
