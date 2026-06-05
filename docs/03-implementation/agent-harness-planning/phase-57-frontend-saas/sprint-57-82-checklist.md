# Sprint 57.82 — Checklist (B-8 leg-1: verification judge token → cost ledger + quota)

**Plan**: `sprint-57-82-plan.md`
**Branch**: `feature/sprint-57-82-verification-cost-ledger` (from `main` `7086c48c`)
**Closes**: B-8 **blocker A** (`AD-Cat10-Judge-Cost-Ledger`) — billing leg of 完整 B-8 epic. Does NOT flip default.

---

## Day 0 — Plan-vs-Repo Verify + Branch + Decisions

### 0.1 Day-0 verify (parent grep + code read + Explore, main `7086c48c`; analysis 8 sprints old → re-verified)
- [x] **Prong 1 (path)** — confirm: `verification/llm_judge.py`, `verification/correction_loop.py`, `_contracts/verification.py`, `_contracts/events.py`, `_contracts/chat.py`, `platform_layer/billing/cost_ledger.py`, `platform_layer/tenant/quota.py`, `api/v1/chat/router.py`, `api/v1/chat/sse.py`, `verification/templates/*.txt` all exist.
- [x] **Prong 2 (content)** — D-DAY0-1..6 in plan §0: blocker A still holds (judge `response.usage` discarded; ledger only at LoopCompleted router observer); verification runs in WRAPPER after LoopCompleted (loop metrics_acc frozen → wrapper must accumulate); VerificationResult has no token fields; LoopCompleted already has loop token fields; record_llm_call sub_type is a string col; default `chat_verification_mode` = disabled (passthrough → 0).
- [x] **Prong 3 (schema)** — N/A (no DB table / migration / ORM change; cost ledger sub_type is an existing string column — judge variant adds no column).
- [x] **Design locked** (AskUserQuestion 2026-06-05) — Option 1 (LoopCompleted +verification token fields → router separate judge ledger entry + quota actual includes judge).
- [x] **go/no-go** — GO; leg 1 = blocker A only (B + C → leg 2, bundled because B's false-positive eval needs real-LLM). No flag flip this sprint.

### 0.2 Branch + decisions
- [x] **Branch created** `feature/sprint-57-82-verification-cost-ledger`
- [x] **Decisions locked**: parent-direct (NOT agent-delegated — cross-category + 3 wrapper exit points + 17.md change); `agent_factor` 1.0; aggregate judge tokens into ONE `_verification` sub_type (per-verifier breakdown = out of scope); `dataclasses.replace` to fill frozen LoopCompleted; judge shares loop adapter → `event.provider` correct for judge.
- [x] **Day-0 commit** plan + checklist + progress.md Day 0 (`e9a015f4`)

---

## Day 1 — Capture + bubble (US-1/US-2)

### 1.1 VerificationResult token fields (US-1)
- [x] **`_contracts/verification.py`** — add `input_tokens: int = 0`, `output_tokens: int = 0`, `model: str | None = None` to VerificationResult
  - DoD: mypy clean; rules_based / external verifiers untouched (defaults); MHist 1-line

### 1.2 llm_judge capture (US-1)
- [x] **`verification/llm_judge.py`** — capture `response.usage` (prompt→input, completion→output) + `response.model` into the returned VerificationResult (pass + parse-fail paths; thrown/fail-closed path keeps 0)
  - DoD: no openai/anthropic import (neutral TokenUsage); mypy clean

### 1.3 LoopCompleted token fields (US-2)
- [x] **`_contracts/events.py`** — add `verification_input_tokens: int = 0`, `verification_output_tokens: int = 0`, `verification_model: str | None = None` to LoopCompleted
  - DoD: confirm LoopCompleted frozen=True; mypy clean

### 1.4 wrapper accumulate + fill (US-2)
- [x] **`verification/correction_loop.py`** — accumulate `result.input_tokens/output_tokens` across all verifiers + all correction attempts (running `vin/vout` + last model); fill via `dataclasses.replace` on the 3 judge-running yield points (all-pass :194 / exhausted :200 new LoopCompleted); non-end_turn :146 + passthrough → stay 0
  - DoD: all 3 paths filled correctly; mypy clean

### 1.5 read changed code + format/type gate
- [x] **re-read** — category boundary intact (no platform_layer import in agent_harness); neutral types only
- [x] **black + isort + flake8 + mypy src/** on changed files — clean (black 4 unchanged / isort clean / flake8 0 / mypy src/ 0 in 332 files) (57.80 lesson: full chain)

---

## Day 2 — Record cost + quota + SSE + contract (US-3/US-4)

### 2.1 record_llm_call sub_type variant (US-3)
- [ ] **`platform_layer/billing/cost_ledger.py`** — add optional `sub_type_suffix: str = ""` → `{provider}_{model}{suffix}_input/_output` (default "" keeps loop sub_types byte-identical)
  - DoD: existing loop entries unchanged; mypy clean

### 2.2 router judge record + quota (US-3)
- [ ] **`api/v1/chat/router.py`** — after the loop record_llm_call: if `event.verification_input_tokens>0 or verification_output_tokens>0` → record_llm_call(judge tokens, `sub_type_suffix="_verification"`, model=verification_model or event.model) best-effort; quota `actual_tokens` += verification tokens
  - DoD: judge entry distinct from loop entry; quota includes judge; best-effort try/except mirrors existing

### 2.3 SSE serialize (US-4)
- [ ] **`api/v1/chat/sse.py`** — LoopCompleted serializer emits the 3 verification token fields
  - DoD: verification_passed/failed serializers unchanged

### 2.4 17.md contract sync (US-4)
- [ ] **`17-cross-category-interfaces.md`** — §1.1 VerificationResult +3 token fields; §4.1 LoopCompleted row note verification token fields (filled by Cat 10 wrapper, consumed by chat router billing observer)

---

## Day 3 — Tests (US-5)

### 3.1 unit — llm_judge capture
- [ ] **`test_llm_judge.py`** (extend) — MockChatClient returns ChatResponse with usage+model → VerificationResult.input_tokens/output_tokens/model populated; fail-closed path keeps 0

### 3.2 unit — wrapper accumulation (5 paths)
- [ ] **`test_correction_loop.py`** (extend) — (a) all-pass → captured LoopCompleted sums judge tokens; (b) 1-correction-then-pass → summed across 2 judge runs; (c) exhausted → verification_failed LoopCompleted carries tokens; (d) non-end_turn → 0; (e) passthrough → 0

### 3.3 integration — billing + quota
- [ ] **`tests/integration/api/`** — enabled registry + mock judge → distinct `_verification_input/_output` ledger entry written + quota actual_tokens includes judge tokens; default-disabled path asserts zero extra entry (AP-10: structural invariant on billing path via mock)
- [ ] **regression** — targeted pytest (verification + billing + chat router) no regression

---

## Day 4 — Sweep + Closeout

### 4.1 Full sweep
- [ ] **Backend gates** — black/isort/flake8 src/ tests/ 0 + `mypy src/` 0 + `pytest` green (+N) + `python scripts/lint/run_all.py` 10/10 (check_llm_sdk_leak + check_cross_category_import green)
- [ ] **No frontend** — backend + docs only (sse field is additive; frontend may ignore)
- [ ] **Read all changed code** — final pass

### 4.2 Closeout docs
- [ ] **CHANGE-049** in `claudedocs/4-changes/feature-changes/`
- [ ] **progress.md** Day 0-4 + **retrospective.md** Q1-Q7
- [ ] **Checklist** all `[x]` (no 🚧 carryover)
- [ ] **Calibration** record (medium-backend 0.80; agent_factor 1.0 parent-direct; ratio in retro Q2)
- [ ] **AD status**: B-8 blocker A / `AD-Cat10-Judge-Cost-Ledger` CLOSED; next-phase-candidates.md updated (leg 2 = 57.83: blocker B+C + flip default)
- [ ] **MEMORY subfile + pointer** + **CLAUDE.md lean** (Current Sprint + Last Updated)
- [ ] **Design note?** — NO (wiring + contract extension of existing Cat 10; 17.md §1.1/§4.1 updated in-place, not a new domain spike)

### 4.3 Ship
- [ ] **Commit mapping** Day-0 / Day1-3 code+tests / Day-4 closeout
- [ ] **Push + PR** (user-gated — explicit authorization required)
