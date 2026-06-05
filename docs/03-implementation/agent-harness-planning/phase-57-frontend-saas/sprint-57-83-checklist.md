# Sprint 57.83 — Checklist (B-8 leg-2: general judge template + real-LLM e2e + data-gated flip)

**Plan**: `sprint-57-83-plan.md`
**Branch**: `feature/sprint-57-83-verification-enable` (from `main` `ee8d4cc9`)
**Closes**: B-8 **blocker B + C + flip** (final leg; flip is data-gated per Q2). Closes `AD-Cat10-Wire-1-Production` IF flipped.

---

## Day 0 — Plan-vs-Repo Verify + Branch + Decisions

### 0.1 Day-0 verify (parent grep + code read, main `ee8d4cc9`)
- [x] **Prong 1 (path)** — confirm: `verification/templates/*.txt` (4 existing), `verification/llm_judge.py` (_build_prompt load_template), `core/config/__init__.py` (both defaults), `_category_factories.py` (make_chat_verifier_registry), `tests/unit/core/test_config_verification.py`, `tests/unit/agent_harness/verification/test_judge_templates.py`.
- [x] **Prong 2 (content)** — 4 templates all special-purpose (safety/factual/format/pii) → NO general quality judge; `chat_verification_judge_template`="safety_review", `chat_verification_mode`="disabled"; real_llm is a chat MODE not a pytest marker (real-LLM e2e = manual local backend + real Azure); `test_config_verification.py:37` asserts mode=disabled (must update iff flip); echo_demo unaffected (no registry regardless of mode); leg-1 judge→ledger wiring means enabled run writes `_verification` entries (cost measurement free).
- [x] **Prong 3 (schema)** — N/A (no DB / migration / ORM change).
- [x] **Design locked** (AskUserQuestion 2026-06-05): Q1 = general quality judge (helpful/complete/accurate/on-topic, fail on any); Q2 = data-driven gate (flip only if FP rate / latency / cost acceptable).
- [x] **go/no-go** — GO; leg 2 = blocker B + C + (gated) flip.

### 0.2 Branch + decisions
- [x] **Branch created** `feature/sprint-57-83-verification-enable`
- [x] **Decisions locked**: NEW `output_quality.txt` general judge (single judge, NOT combine-with-safety, NOT factual-rework); default template swap → output_quality; real-LLM measurement = manual local-backend run with real Azure (user-authorized Q2); flip is conditional on measured data (FP ≤ ~15%, p95 < 5s); parent-direct.
- [x] **Day-0 commit** plan + checklist + progress.md Day 0 (`6d82af71`)

---

## Day 1 — Blocker B: general quality judge template (US-1/US-2)

### 1.1 output_quality template
- [x] **NEW `verification/templates/output_quality.txt`** — general quality judge (helpful/complete/accurate/on-topic, fail on any dimension); JSON shape `passed`/`score`/`reason`/`suggested_correction`; contains literal `{output}`; "normal answer should pass / lean pass when uncertain" (low-FP intent)
  - DoD: loads via `load_template("output_quality")` (auto-read by glob, no registration); not a safety-lean phrasing ✅

### 1.2 default judge template swap
- [x] **`core/config/__init__.py`** — `chat_verification_judge_template` default `"safety_review"` → `"output_quality"` + update docstring example (+ templates/__init__.py docstring list)
  - DoD: mypy clean; mode stays `disabled` (flip is Day 3) ✅

### 1.3 unit tests + gate
- [x] **`test_judge_templates.py`** (extend) — output_quality in parametrize (5 templates) + dedicated test (4 dimensions + `{output}` + lean-pass guard)
- [x] **`test_config_verification.py`** — `TestChatVerificationJudgeTemplate` default == output_quality (mode default test unchanged — flip is Day 3)
- [x] **black + isort + flake8 + mypy src/** — clean (4 files unchanged / flake8 0 / mypy 0 in 332 / pytest 12 passed)

---

## Day 2 — Blocker C: real-LLM e2e measurement (US-3) — real Azure, user-authorized

### 2.1 measurement setup
- [ ] **Confirm `.env` Azure secrets** live (57.79/57.80 ran real Azure) + confirm with user before spending
- [ ] **Clean local backend** (Risk Class E): no-reload, `CHAT_VERIFICATION_MODE=enabled` + `CHAT_VERIFICATION_JUDGE_TEMPLATE=output_quality`; confirm startup picks up env

### 2.2 run measurement
- [ ] **K≈8-10 normal prompts** (mode=real_llm, a reasonable user would accept) + 2-3 deliberately bad/empty → collect verdict + judge p95 latency + `_verification` cost-ledger entry per chat
- [ ] **Compute**: false-positive rate (normal judged failed / total normal), p95 judge latency, mean per-chat judge cost
- [ ] **Record** in `claudedocs/5-status/cat10-verification-real-llm-measurement-20260605.md` (protocol + raw verdicts + computed metrics)

---

## Day 3 — Data-gated flip decision (US-4) + tests

### 3.1 flip decision
- [ ] **Evaluate** against threshold (FP ≤ ~15%, p95 < 5s) — record verdict in progress.md Day 3
- [ ] **IF acceptable**: `core/config/__init__.py` `chat_verification_mode` default `"disabled"` → `"enabled"`; grep-confirm no other test assumes disabled; update `test_config_verification.py` mode default → enabled; B-8 fully closed
- [ ] **ELSE**: keep `disabled`; log carryover "tune output_quality + re-measure + flip" with the data; B-8 partially open (gate exercised, not a failure)

### 3.2 regression
- [ ] **targeted pytest** (verification + config + chat) no regression; full sweep Day 4

---

## Day 4 — Sweep + Closeout

### 4.1 Full sweep
- [ ] **Backend gates** — black/isort/flake8 src/ tests/ 0 + `mypy src/` 0 + `pytest` green + `run_all.py` 10/10 (check_llm_sdk_leak green)
- [ ] **No frontend** — backend + docs only
- [ ] **Read all changed code** — final pass

### 4.2 Closeout docs
- [ ] **CHANGE-050** in `claudedocs/4-changes/feature-changes/`
- [ ] **progress.md** Day 0-4 + **retrospective.md** Q1-Q7 (incl. flip decision + measured data)
- [ ] **Checklist** all `[x]` (no 🚧 carryover)
- [ ] **Calibration** record (medium-backend 0.80; agent_factor 1.0 parent-direct; real-LLM measurement wall-clock variance noted)
- [ ] **AD status**: B-8 blocker B+C CLOSED; `AD-Cat10-Wire-1-Production` CLOSED iff flipped (else carryover); next-phase-candidates.md updated
- [ ] **MEMORY subfile + pointer** + **CLAUDE.md lean** (Current Sprint + Last Updated)
- [ ] **Design note?** — likely NO (template + config + measurement; no new contract). Reconsider if the measurement surfaces a design-worthy invariant.

### 4.3 Ship
- [ ] **Commit mapping** Day-0 / Day1 template+default / Day2-3 measurement+flip / Day-4 closeout
- [ ] **Push + PR** (user-gated — explicit authorization required)
