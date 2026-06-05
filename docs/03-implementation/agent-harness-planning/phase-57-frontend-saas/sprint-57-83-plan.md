# Sprint 57.83 Plan — B-8 leg-2: general judge template + real-LLM e2e + (data-gated) flip default (closes B-8 / AD-Cat10-Wire-1-Production)

**Branch**: `feature/sprint-57-83-verification-enable` (from `main` `ee8d4cc9`)
**Closes**: B-8 **blocker B + C + flip** — the final leg of the 完整 B-8 epic. Flipping the default is **conditional** on the real-LLM data (Q2 = data-driven gate).

---

## 0. Background

Leg 1 (57.82) closed B-8 blocker A (judge token → cost ledger + quota). This leg closes the remaining 3 launch-blockers from `cat10-verification-default-enable-analysis-20260601.md`:
- **Blocker B**: the default `safety_review` template is Cat 9-fitted ("borderline lean unsafe") → high false-positive as a general final-output judge. Need a general quality judge.
- **Blocker C**: the enabled path has zero real-LLM test → false-positive rate / latency / cost unknown.
- **The flip**: `chat_verification_mode` default `disabled` → `enabled` (the B-8 end goal).

**Design locked (user AskUserQuestion 2026-06-05)**:
- **Q1 = general quality judge**: a NEW `output_quality` template judging helpful / complete / accurate / on-topic, failing if it falls short on ANY dimension. Becomes the new default `chat_verification_judge_template`.
- **Q2 = data-driven gate**: run a real-Azure e2e to measure false-positive rate / p95 latency / per-chat cost; **flip the default only if the data is acceptable**. If the data is poor → keep `disabled` + carryover template tuning (the flip is NOT an unconditional deliverable).

### Day-0 ground-truth (parent grep + code read, main `ee8d4cc9`)
- 4 existing templates are all special-purpose (re-read): `safety_review` (Cat 9 fallback, lean-unsafe), `factual_consistency` (wants conversation context but the judge prompt only gets `{output}`), `format_compliance`, `pii_leak_check` (Cat 9 fallback, lean-flag). **No general final-output quality judge exists** → blocker B must create one.
- `chat_verification_judge_template` default = `"safety_review"` (config:117); `chat_verification_mode` default = `"disabled"` (config:112). `make_chat_verifier_registry(chat_client, judge_template)` registers ONE `LLMJudgeVerifier`. Template resolved by name from `verification/templates/<name>.txt` (`llm_judge.py:_build_prompt`).
- `real_llm` is a chat MODE (`POST /chat` body `{"mode":"real_llm"}`), NOT a pytest marker (absent in pyproject/conftest). Real-LLM verification e2e = run a local backend with real Azure (the 57.79/57.80 pattern: `python -m uvicorn api.main:app --app-dir backend/src ...` + dev-login + POST /chat) — needs Azure secrets in `.env` + user authorization (real cost). Only the `real_llm` handler builds the verifier registry (echo_demo always registry=None).
- `test_config_verification.py:37` asserts `Settings().chat_verification_mode == "disabled"` — flipping the default requires updating this test. echo_demo tests are unaffected (no registry regardless of mode).
- Leg 1 (57.82) already wired judge cost → ledger + quota, so an enabled real-LLM run will write `_verification` ledger entries (cost measurement is "free" — already instrumented).

---

## 1. Sprint Goal

Ship a general final-output quality judge (blocker B), measure its false-positive rate / latency / cost against real Azure (blocker C), and — **if the data is acceptable** — flip `chat_verification_mode` default to `enabled` (the B-8 end goal); otherwise keep `disabled` + carryover template tuning with the measured data recorded.

## 2. User Stories

- **US-1**: As a platform operator, I want a general final-output quality judge template (not the Cat 9 safety template) so verification on the main chat path judges answer quality, not just safety. (blocker B)
- **US-2**: As a platform operator, I want the default judge template to be the general one, so enabling verification uses the right judge. (blocker B — default swap)
- **US-3**: As finance/SRE, I want the enabled path's false-positive rate / p95 latency / per-chat cost measured against real Azure, so the flip decision is evidence-based. (blocker C)
- **US-4**: As a platform operator, I want the default `chat_verification_mode` flipped to `enabled` **iff** the measured data is acceptable, so production gets verification without a false-positive storm. (the flip — data-gated)
- **US-5**: As a maintainer, I want unit tests for the new template + the config-default change, so the contract is pinned. (tests)

## 3. Technical Specifications

### 3.0 Architecture

Blocker B is a new prompt template + a one-line default swap (pure code, mock-verifiable). Blocker C is a measurement protocol run against a local backend + real Azure (no production change). The flip is a one-line config-default change gated on C's data. LLM neutrality unaffected (template is a text file; the judge call already goes through ChatClient).

### 3.1 General quality judge template (US-1) — NEW `verification/templates/output_quality.txt`

- New template judging helpful / complete / accurate / on-topic, fail if it falls short on ANY dimension (per Q1 selected preview). JSON output shape identical to the other 4 templates (`passed` / `score` / `reason` / `suggested_correction`). Contains the literal `{output}` placeholder.
- Phrasing aims to be a fair quality bar (not a safety lean) — the false-positive rate is what blocker C measures.

### 3.2 Default judge template swap (US-2) — `core/config/__init__.py`

- `chat_verification_judge_template` default `"safety_review"` → `"output_quality"`. (mode stays `disabled` here — that flip is §3.4.)
- Update the config docstring example references.

### 3.3 Real-LLM e2e measurement (US-3) — local backend + real Azure (user-authorized)

- Protocol (recorded in a measurement artifact under `claudedocs/5-status/`): set `CHAT_VERIFICATION_MODE=enabled` + `CHAT_VERIFICATION_JUDGE_TEMPLATE=output_quality`, start a local no-reload backend with real Azure, dev-login, run K≈8-10 "normal" prompts (mode=real_llm) that a reasonable user would accept, plus 2-3 deliberately bad/empty asks.
- Collect per chat: verification_passed/failed verdict, judge p95 latency (loop_end tail), `_verification` cost-ledger entry (leg 1 instrumentation).
- Compute: **false-positive rate** (normal prompts judged failed / total normal), p95 judge latency, mean per-chat judge cost.
- Acceptance threshold (proposed): false-positive rate ≤ ~15%, p95 judge latency < 5s (the §範疇10 SLO). Record actuals.

### 3.4 Data-gated flip (US-4) — `core/config/__init__.py` + `test_config_verification.py`

- **IF** §3.3 data acceptable: `chat_verification_mode` default `"disabled"` → `"enabled"`; update `test_config_verification.py` default assertion; B-8 fully closed.
- **ELSE**: keep `disabled`; record the measured data + the gap; carryover "tune output_quality template + re-measure" (B-8 stays partially open). NOT a failure — the gate did its job.
- Decision + data recorded in progress.md Day-3 + retrospective.

### 3.5 Tests (US-5)

- `test_judge_templates.py` (extend): `output_quality` loads by name; contains `{output}`; mock judge with the template returns a parseable verdict.
- `test_config_verification.py`: update default template assertion (→ output_quality); update mode default assertion ONLY if §3.4 flips.
- No new real-LLM pytest (real-LLM is a manual measurement run, not CI — consistent with the repo's real_llm-as-chat-mode pattern).

### 3.6 Lint / validation

`black + isort + flake8 + mypy src/` + `run_all.py` 10/10. Full format chain pre-commit.

## 4. File Change List

**Code (2-3)**:
1. `backend/src/agent_harness/verification/templates/output_quality.txt` — NEW general quality judge template
2. `backend/src/core/config/__init__.py` — default judge template → output_quality (+ mode → enabled IF gated)
3. `backend/tests/unit/core/test_config_verification.py` — default assertions (template; mode iff flipped)

**Tests (1 extend)**:
4. `backend/tests/unit/agent_harness/verification/test_judge_templates.py` — output_quality load + shape

**Docs (1)**:
5. `claudedocs/5-status/cat10-verification-real-llm-measurement-20260605.md` — NEW measurement artifact (protocol + data + flip decision)

## 5. Acceptance Criteria

1. `output_quality.txt` exists, contains `{output}`, judges the 4 quality dimensions, loads by name via `load_template`.
2. Default `chat_verification_judge_template` == `"output_quality"`; test updated.
3. Real-Azure measurement run completed: false-positive rate + p95 latency + per-chat cost recorded in the artifact.
4. Flip decision made on the data: EITHER default `chat_verification_mode` == `"enabled"` + test updated + B-8 closed, OR default stays `"disabled"` + carryover logged with the data (gate exercised).
5. `mypy src/` 0; full pytest green; `run_all.py` 10/10.

## 6. Deliverables

- [ ] US-1: output_quality.txt template
- [ ] US-2: default judge template → output_quality + config docstring
- [ ] US-3: real-Azure measurement (FP rate / p95 latency / per-chat cost) → artifact
- [ ] US-4: data-gated flip decision (flip enabled + test, OR keep disabled + carryover)
- [ ] US-5: unit tests (template load + config default)
- [ ] Closeout: CHANGE-050 + progress + retrospective + checklist + MEMORY + CLAUDE lean + next-phase-candidates

## 7. Workload Calibration

- **Agent-delegated: no** (parent-direct — real-Azure measurement + the data-gated flip decision are judgment-sensitive). `agent_factor` 1.0 → 3-segment form.
- Bottom-up est ~5.5 hr → class-calibrated commit ~4.4 hr (`medium-backend` 0.80).
- **Wall-clock caveat**: §3.3 real-LLM measurement has inherent variance (Azure latency, prompt iterations to estimate FP). The measurement is research-shaped; the calibration ratio will be noisier than a pure-code sprint — noted in retro Q2.

## 8. Dependencies & Risks

| # | Risk | Mitigation |
|---|------|-----------|
| 1 | Real Azure needed for blocker C (cost + secrets) | user authorized data-driven gate (Q2); confirm `.env` Azure secrets live (57.79/57.80 ran real Azure); 1 measurement run, ~10-13 prompts — bounded cost |
| 2 | `output_quality` FP rate too high → can't flip | that's exactly what the data-gate catches — keep disabled + carryover tune; not a sprint failure |
| 3 | Flipping default may break tests assuming disabled | Day-0 found only `test_config_verification.py:37`; grep again before flip; echo_demo unaffected (no registry regardless of mode) |
| 4 | Correction full-loop re-run cost (analysis §2: 3× loop) on enabled | the FP measurement surfaces how often correction triggers; a low-FP judge keeps re-runs rare; recorded in artifact |
| 5 | LLM neutrality | template is a text file; judge call already via ChatClient — no SDK import. `check_llm_sdk_leak` green |
| 6 | Risk Class E (stale --reload backend masks template/config change) | clean restart for the measurement run; confirm startup picks up CHAT_VERIFICATION_* env |

## 9. Out of Scope (this sprint; carryover)

- **Per-verifier cost attribution** (leg 1 carryover) — still one `_verification` sub_type.
- **Multi-judge registry** (safety + quality together) — this sprint ships ONE general quality judge (Q1 chose the single general judge, not the combine option).
- **factual_consistency context injection** — not pursued (Q1 chose general quality, not the factual-consistency rework).
- **C-15 DevOps/data-platform billing** — separate billing-bundle leg.
- **If flip is gated OFF**: "tune output_quality + re-measure + flip" becomes a follow-up.
