# Sprint 57.83 Progress — B-8 leg-2: general judge template + real-LLM e2e + data-gated flip

**Branch**: `feature/sprint-57-83-verification-enable` (from `main` `ee8d4cc9`)
**Closes**: B-8 **blocker B + C + flip** (final leg; flip data-gated per Q2).

---

## Day 0 — 2026-06-05 — Plan-vs-Repo Verify + Branch + Decisions

### Accomplishments
- User merged 57.82 (PR #248, leg 1) → selected leg 2. main synced (ee8d4cc9), branch created.
- Day-0 research: read all 4 existing judge templates + verified the default template/mode + the real_llm test mechanism.
- AskUserQuestion ×2 (Q1 judge-template standard, Q2 real-LLM + flip approach).
- Plan + checklist drafted (mirror 57.82 9-section / Day 0-4).

### Day-0 verify (Prong 1 path + Prong 2 content; Prong 3 N/A — no schema)
- **Prong 1** ✅ — 4 templates, llm_judge.py, config, _category_factories.py, test_config_verification.py, test_judge_templates.py confirmed.
- **Prong 2** ✅:
  - **4 templates all special-purpose** (re-read): `safety_review` (Cat 9 fallback, "borderline lean unsafe"), `factual_consistency` (wants conversation context but the judge prompt only substitutes `{output}` — can't get history), `format_compliance`, `pii_leak_check` (Cat 9 fallback, "when in doubt flag it"). **NO general final-output quality judge** → blocker B must create one.
  - default `chat_verification_judge_template`="safety_review" (config:117), `chat_verification_mode`="disabled" (config:112). `make_chat_verifier_registry` registers ONE LLMJudgeVerifier; template loaded by name from `templates/<name>.txt`.
  - **`real_llm` is a chat MODE, NOT a pytest marker** (absent in pyproject/conftest) → real-LLM verification e2e = manual local backend + real Azure (57.79/57.80 pattern: uvicorn --app-dir backend/src + dev-login + POST /chat mode=real_llm). Needs Azure secrets + user authorization (cost).
  - `test_config_verification.py:37` asserts mode=disabled → must update iff flip. echo_demo tests unaffected (no registry regardless of mode).
  - leg-1 (57.82) judge→ledger wiring → an enabled real-LLM run writes `_verification` cost entries → cost measurement is free (already instrumented).
- **Prong 3** N/A — no DB/migration/ORM.

### Drift findings
- No drift (leg 1's own work is fresh main; the analysis claims re-confirmed). The only refinement: real_llm being a chat mode (not a marker) means blocker C is a manual measurement run, not a CI test — reflected in plan §3.5 (no new real-LLM pytest).

### Decisions locked (AskUserQuestion)
- **Q1 = general quality judge**: NEW `output_quality.txt` judging helpful / complete / accurate / on-topic, fail if short on ANY dimension. NOT the combine-with-safety option, NOT the factual-consistency rework. Becomes the new default template.
- **Q2 = data-driven gate**: run real-Azure e2e → measure false-positive rate / p95 latency / per-chat cost → flip `chat_verification_mode` default to `enabled` ONLY if acceptable (proposed FP ≤ ~15%, p95 < 5s); else keep disabled + carryover tune (gate exercised, not a failure).
- **parent-direct** (NOT agent-delegated) — real-Azure measurement + the gated flip decision are judgment-sensitive.

### Blockers / dependencies
- **Day 2 needs real Azure** (cost + secrets) — user authorized via Q2; will confirm `.env` secrets + flag the spend before running.

### Remaining for Day 1+
- Day 1: output_quality template + default template swap + unit tests (mock).
- Day 2: real-LLM measurement (FP rate / latency / cost) → artifact. **(real Azure — confirm with user before running)**
- Day 3: data-gated flip decision (flip enabled + test, OR keep disabled + carryover).
- Day 4: sweep + closeout.

### Notes
- Bottom-up est ~5.5 hr → calibrated ~4.4 hr (medium-backend 0.80, parent-direct). Real-LLM measurement (§3.3) is research-shaped → wall-clock variance noted (retro Q2).
- Q1 chose the STRICTER "fail on any dimension" general judge → blocker C's FP measurement is the more important gate (a strict judge may have higher FP → data-gate decides).
