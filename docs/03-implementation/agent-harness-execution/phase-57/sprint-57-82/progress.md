# Sprint 57.82 Progress — B-8 leg-1: verification judge token → cost ledger + quota

**Branch**: `feature/sprint-57-82-verification-cost-ledger` (from `main` `7086c48c`)
**Closes**: B-8 **blocker A** (`AD-Cat10-Judge-Cost-Ledger`) — billing leg of 完整 B-8 epic. No flag flip.

---

## Day 0 — 2026-06-05 — Plan-vs-Repo Verify + Branch + Decisions

### Accomplishments
- User selected **完整 B-8 (clear 3 blockers + flip default)** after the A/B/C inventory review. Recognized it's a 2-3 sprint epic; split into leg 1 (blocker A, this sprint) + leg 2 (blocker B+C + flip, 57.83, plan written only at 57.82 closeout — rolling discipline).
- Read source analysis `cat10-verification-default-enable-analysis-20260601.md` (8 sprints old) + re-verified its 3-blocker claims against current main `7086c48c` (57.79 touched cost ledger, 57.81 touched budget).
- Day-0 verify (Prong 1 path + Prong 2 content; Prong 3 N/A — no schema) + Explore-agent data-structure sweep.
- AskUserQuestion ×2: (1) scope = 完整 B-8; (2) judge accounting design = Option 1.
- Plan + checklist drafted (mirror 57.81 9-section / Day 0-4 format). Branch created.

### Day-0 verify
- **Prong 1 (path)** ✅ — llm_judge.py / correction_loop.py / _contracts{verification,events,chat}.py / cost_ledger.py / quota.py / router.py / sse.py / templates/*.txt all confirmed.
- **Prong 2 (content)** ✅:
  - **Blocker A STILL HOLDS**: `llm_judge.py:84-89` keeps only `response.content`, discards `response.usage` (TokenUsage prompt/completion/cached/total) + `response.model`. Cost ledger recorded only at router `LoopCompleted` observer (`router.py:435` record_llm_call from loop metrics_acc); quota reconcile reads `event.total_tokens` (`router.py:392`). Judge flows through neither. 57.79 changed pricing-key only.
  - **Verification runs in WRAPPER, after LoopCompleted** (`correction_loop.py:121-209`): inner loop already emitted LoopCompleted (captured, not yet yielded) before judge runs → loop metrics_acc frozen → **wrapper must accumulate judge tokens** (corrects Explore's "loop accumulator" suggestion).
  - VerificationResult (`_contracts/verification.py:31-42`) = passed/verifier_name/verifier_type/score/reason/suggested_correction/metadata — **no token fields**.
  - LoopCompleted (`events.py:127-166`) already has input/output_tokens + provider + model + cached_input_tokens + cache_hit_rate.
  - ChatResponse.usage = TokenUsage(prompt_tokens, completion_tokens, cached_input_tokens, total_tokens).
  - record_llm_call (`cost_ledger.py:106-184`) writes 2 entries `{provider}_{model}_input/_output`; sub_type is a string column → no schema change for a judge variant.
  - QuotaEnforcer.record_usage (`quota.py:171-192`) = (*, tenant_id, actual_tokens, reserved_tokens).
  - default `chat_verification_mode = disabled` (config:112); disabled → wrapper passthrough (`correction_loop.py:110-117`) → no verification, token fields stay 0.
- **Prong 3 (schema)** N/A — sub_type is an existing string column; no DB/migration/ORM change.

### Drift findings
- **D1 (Explore suggestion corrected)**: Explore proposed calling `metrics_acc.on_event(verification_event)` in loop.py — but verification runs in the wrapper AFTER LoopCompleted, when the loop accumulator is frozen. Design uses wrapper-level accumulation + `dataclasses.replace` on the captured LoopCompleted instead. No scope shift.
- **D2 (3 yield points)**: wrapper yields LoopCompleted at 3 points (all-pass :194 / exhausted :200 builds a new one / non-end_turn :146). Judge-token fill must cover :194 + :200; :146 + passthrough stay 0. Captured in plan §3.2 + test (c)/(d)/(e).
- No scope shift (≤20%). GO for Day 1.

### Decisions locked
- **Option 1** (AskUserQuestion): wrapper accumulates judge tokens → LoopCompleted `verification_input/output_tokens` + `verification_model` → router records a **separate** judge ledger entry (`_verification` sub_type suffix) at the same LoopCompleted observer + adds judge tokens to quota `actual_tokens`. Single observer point; transparent attribution; loop token semantics not polluted.
- **parent-direct** (NOT agent-delegated) — cross-category design + 3 wrapper exit points + 17.md contract change; careful coordination (like 57.81). `agent_factor` 1.0.
- Aggregate all judge tokens into ONE `_verification` sub_type (per-verifier breakdown = out of scope, leg 1).
- `dataclasses.replace` to fill frozen LoopCompleted.
- Judge shares loop adapter → `event.provider` correct for the judge entry.
- **Default unchanged** — `chat_verification_mode` stays disabled; this sprint is pure correctness fix that activates only on the enabled path (mock-verified).

### Blockers / dependencies
- None. cost ledger / quota / verification infra all live (56.3 / 56.2 / 54.1). gpt-5.2 priced since 57.79.

### Remaining for Day 1+
- Day 1: VerificationResult+llm_judge capture / LoopCompleted fields / wrapper accumulate+fill.
- Day 2: record_llm_call sub_type_suffix / router judge record + quota / sse / 17.md.
- Day 3: unit (llm_judge + correction_loop 5 paths) + integration (billing + quota).
- Day 4: sweep + closeout.

### Notes
- Bottom-up est ~5.3 hr → calibrated ~4.2 hr (medium-backend 0.80, parent-direct agent_factor 1.0).
- Epic roadmap: leg 1 (this) = blocker A; leg 2 (57.83) = blocker B (general judge template) + blocker C (real-LLM e2e) + flip default. B+C bundled because B's false-positive eval needs real-LLM.
