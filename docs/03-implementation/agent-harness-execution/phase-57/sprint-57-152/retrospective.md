# Sprint 57.152 Retrospective — combine post-send extract + summarize into one LLM call

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-152-plan.md) · [Progress](./progress.md)

**Closed**: 2026-06-30 · **AD**: `AD-Memory-Formation-Combine-Extract-Summarize` CLOSED · **CHANGE**: 119 · **Design note**: 55

## Q1 — What shipped

A `MemoryFormationWorker` (`agent_harness/memory/formation.py`) that COMPOSES the 57.149 `MemoryExtractor` + 57.151 `SessionSummarizer` and (default) makes ONE combined cheap-tier LLM call returning both the durable user facts AND the rolling session summary, then dispatches each half to the SAME write code (extracted behavior-preserving `write_facts` / `store_summary` dispatch halves). `chat_memory_combined_formation` flag (default ON) gates combined-vs-separate; the `combined=False` fallback delegates to the two full single-call methods (keeps both live on the chat path → no orphaning). Backend-only, NO migration / wire / frontend. Halves the post-send background formation LLM cost when both formation features are on (the default).

## Q2 — Calibration (NEW class `memory-formation-combine-spike` 0.60)

- Bottom-up est ~6 hr (worker ~1.5 · 2 dispatch extractions ~1 · wiring ~1 · tests ~1.5 · drive-through ~1) → class-calibrated commit ~3.6 hr (mult 0.60). Agent-delegated: **no** (parent-direct, `agent_factor` 1.0 → 3-segment).
- Actual ~3.5-3.8 hr (code + tests landed near bottom-up haircut; Day-0 三-prong clean caught all 4 drifts pre-code; the drive-through ran on-budget — Leg 1 formed both halves first try; the only extra wall-clock was the DB-inspector column-name iteration (tenants `slug` → users lookup; sessions `created_at` → JOIN) + the Leg-2 carryover analysis).
- **Ratio ~1.0-1.05 IN band** → KEEP 0.60. Anchored to the arc's `memory-formation-identity-spike` 0.60 (57.148) / `memory-session-recall-spike` 0.60 (57.151) — same Cat-3 + main-flow-wiring shape, LIGHTER (no migration/table/recall) but offset by the combined-prompt design + the both-halves drive-through. The 57.137 lesson held: the real-code core (worker + 2 extractions + combined parse + 10 tests, ≥~3 hr) held the 0.60, NOT a tiny-code 0.85. If a 2nd `memory-formation-combine-spike` diverges > 30% from 0.60, re-point.

## Q3 — What went well

- **Compose-not-replace** cleanly avoided AP-2/AP-4: extracting `write_facts` / `store_summary` let the worker reuse the write logic while the `combined=False` path keeps the full single-call methods reachable. Both `MemoryExtractor` + `SessionSummarizer` stay live + their tests green untouched.
- **Day-0 三-prong** caught all 4 drifts (write-facts session-id unused / ctx-field-rename sites / allowlist precedent / profile-gate) pre-code → 0% scope shift, no mid-sprint rework.
- **Leg-1 drive-through STRONG PASS first try**: both halves at the SAME `15:20:30` timestamp = one combined call, dovetailing with 57.150 dedup (the in-loop `memory_write` of the same fact was upserted by the auto_extract).

## Q4 — What to improve

- The DB-inspector took 3 iterations (column-name guesses: `tenants.slug` → users lookup; `sessions.created_at` → JOIN via `memory_session_summary`). A reusable per-tenant/user memory-inspector helper in scratchpad would save this each memory sprint.
- The Leg-2 recall demo was confounded by the cross-sprint `dan` identity conflict (Chris vs Marcus). Future memory drive-throughs should use a FRESH dev identity (or a unique persona) to avoid accumulated-fact conflicts muddying the recall demonstration.

## Q5 — Anti-pattern self-check

- **AP-2** (no orphan): ✅ both single-call methods live on the chat path via the `combined=False` fallback + reused dispatch halves.
- **AP-3** (scattering): ✅ formation logic in 範疇 3 (`formation.py`), not the router.
- **AP-4** (Potemkin): ✅ drive-through proves both halves form from one real call (not a dead control / fixture).
- **AP-6** (speculative flexibility): ✅ the `chat_memory_combined_formation` flag is a safety valve to a PROVEN existing path (the 57.149+151 two-call path), not a future-proofing abstraction — analogous to `chat_verification_correction_strategy` (57.136).
- **AP-8** (PromptBuilder): ✅ `formation.py` allowlisted (background utility-LLM, same category as extraction.py).
- **AP-11** (naming): ✅ `MemoryFormationWorker` / `write_facts` / `store_summary` / `_form_combined` / `_form_separate` / `wants_user_facts` match behavior. (The dataclass name `ChatMemoryExtractContext` kept — internal, renaming churns router + tests for no behavior gain; field is now `former`.)
- v2 lints: **11/11** green.

## Q6 — Carryover (→ next-phase-candidates, NOT pre-written sprints)

- `AD-Memory-Combined-Formation-AB-Quality` (NEW) — a real-Azure A/B harness measuring whether the combined prompt degrades either half's quality vs two focused calls (mirrors 57.136/137/138; the flag + drive-through sufficed this sprint).
- `AD-Verification-Judge-Memory-Inject-Blind` (57.149 carryover, RE-CONFIRMED at Leg-2) — the in-loop judge sees only the conversation trace, not injected memory → rejects memory-injected recall as fabrication.
- `AD-Memory-Session-Summary-Extract-Coordination` · `AD-Memory-Session-Summary-Incremental` · `AD-Memory-Session-Summary-Inspector-Phase58` (57.151 carryovers, unchanged).

## Q7 — Design Note Extract (spike sprint)

**File**: `docs/03-implementation/agent-harness-planning/55-memory-combined-formation-design.md`
**Verified ratio (estimated)**: ~96%
**8-Point Quality Gate**: 1.✅ headers→US · 2.✅ file:line · 3.✅ decision matrix (5) · 4.✅ verify cmds · 5.✅ test fixture · 6.✅ open invariants bounded · 7.✅ rollback · 8.✅ 17.md cross-ref
**Reviewer pass**: self-review
