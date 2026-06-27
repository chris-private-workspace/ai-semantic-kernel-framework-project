# Sprint 57.148 Retrospective — memory-formation Slice 1: user-identity write + always-on inject

**Sprint goal**: make the platform actually remember a user's stated identity across sessions — the agent proactively persists durable user facts and the PromptBuilder injects user-scope long_term facts unconditionally — proven by a 2-session real-LLM drive-through. Close `AD-Memory-Formation-Identity` Slice 1.

**Outcome**: ✅ achieved. Drive-through PASS (real chat-v2 + real Azure gpt-5.2): the exact failure the user reported live ("new session → 我不知道你是誰") is fixed — formation (proactive `memory_write`), surfacing (keyword-independent always-on inject), and per-user isolation all proven on the main flow.

---

## Q1 — What went well

- **The live drive-through DEFINED the sprint**: the user ran the broken behavior on the real chat page; that single observation surfaced the precise gap and gave a falsifiable success criterion ("S1 tell identity → S2 recall"). Best possible sprint kickoff.
- **Day-0 三-prong resolved BOTH gating risks before any code**: Risk A (ILIKE query-gating, `builder.py:581` + `user_layer.py:88-95`) was CONFIRMED real → it forced the always-on-inject design (a nudge alone would have been an AP-4 Potemkin); Risk B (user_id stability) was GREEN (`auth.py:446` dev-login get-or-create by email). The 4 content-verify D-findings (empty-query guard / write-upsert / nudge-seam / Tier2-cap) each landed a code decision before Day 1.
- **"Mirror the skills-catalog seam" + "additive `profile()`" kept the change tiny**: every building block existed; the nudge rides the proven `loop.py:1970` prepend, `profile()` is additive on `MemoryRetrieval`, and `user_id=None` keeps the whole thing byte-identical for legacy/echo callers (so existing builder tests passed unchanged with `layers={}` → profile returns []).
- **Drive-through was decisive AND clean**: the real gpt-5.2 agent proactively wrote 2 facts WITHOUT being told to remember (the nudge genuinely works), recalled them across a NEW session with a zero-keyword-overlap question (proving the always-on inject, not query-gating), and a different user saw nothing (isolation). DB + Inspector-read evidence corroborated the UI.
- **Bonus recon**: found `MemoryExtractor.extract_session_to_user` already exists (unwired) → the Option-B (deterministic extraction) building block is in place for a future slice.

## Q2 — Estimate accuracy (calibration)

- **Class**: NEW `memory-formation-identity-spike` **0.60** (1st data point). **Agent-delegated: no** (parent-direct; `agent_factor` 1.0).
- **Plan**: bottom-up ~7-9 hr → class-calibrated commit ~4.5-5 hr (mult 0.60).
- **Actual**: ~5-5.5 hr equivalent. Day 0-2 (code + 11 tests + gate) ran roughly on-budget — every piece had a precedent (nudge↔skills catalog, profile()↔search, merge↔Tier2 path). Day 3 drive-through ran slightly over its slice because of the DB-access detour (raw asyncpg password mismatch → `set_config` RLS form → backend-engine session) + the 2-identity setup, but NO connection-shape product bug surfaced.
- **Ratio ≈ 1.0-1.1** (IN band). **KEEP 0.60** — single data point; the real-code core (new `profile()` + builder merge + nudge + 11 multi-tenant tests, ~3-4 hr) held the spike multiplier per the 57.137 lesson (this is NOT a tiny-code-wrapped-in-ceremony sprint → not an 0.85 re-point). **Variance driver = the 2-session/2-identity drive-through setup + DB-evidence plumbing**; if a 2nd `memory-formation-*-spike` lands > 1.20, re-point toward 0.85.

## Q3 — What to improve

- **DB-evidence plumbing cost ~20 min**: raw asyncpg failed (the app's `database_url` password ≠ `.env` `DB_PASSWORD`) and `SET LOCAL` isn't parameterizable. The reusable lesson: for a FORCE-RLS table, query through the backend's OWN `get_session_factory()` + `SELECT set_config('app.tenant_id', :tid, true)` (the parameterizable transaction-local form). Captured for the next memory/RLS drive-through.
- **`UserLayer.write` makes dup rows** (no upsert-by-key): the drive-through wrote name + role as 2 rows; a repeated identity statement would add more. Acceptable for MVP (profile top-k by confidence) but a real `AD-Memory-User-Upsert-By-Key` follow-on.

## Q4 — Lessons / ADs

- **Lesson (reusable)**: when "the mechanism is wired but the feature doesn't work", check BOTH halves — formation (does anything WRITE?) and surfacing (is the read query-gated such that the always-relevant fact is never retrieved?). Here injection was query-gated, so even a populated store wouldn't recall identity; the fix needed an always-on, query-independent pull.
- **Lesson (drive-through)**: a memory feature's drive-through must START from a clean baseline (verified 0 rows) so the write is provably caused by the run, and use a recall question with NO keyword overlap so a pass can't be query-gating in disguise.
- Carryover ADs (next slices): `AD-Memory-Formation-Auto-Extract` (Option B, `MemoryExtractor` unwired) · `AD-Memory-User-Upsert-By-Key` · `AD-Memory-Formation-Session-Recall` (缺口 2) · CARRY-026 memory semantic axis · tenant/role/session always-on injection.

## Q5 — Anti-pattern self-check

- **AP-2** (side-track): ✅ reachable from chat main flow — drive-through ran the nudge + profile inject on the real path.
- **AP-4** (Potemkin): ✅ NOT — drive-through proved the full round-trip (proactive write → cross-session recall → isolation) with DB + Inspector-read evidence; the "我不知道你是誰" answer from a different user is the falsification a fake would fail. The always-on-inject design was specifically chosen to AVOID the write-but-never-recall Potemkin.
- **AP-6** (speculative abstraction): ✅ no new abstraction — `profile()` is additive on the existing `MemoryRetrieval`; reuses `UserLayer`/`memory_write`/the system-prompt seam.
- **AP-8** (centralized PromptBuilder): ✅ the always-on inject lives INSIDE `DefaultPromptBuilder.build()`, not scattered.
- **AP-11** (naming): ✅ `profile()` / `MEMORY_FORMATION_NUDGE` / `profile_top_k` match behavior.
- **v2 lints**: 11/11 green (incl. `check_promptbuilder_usage`, `check_tool_descriptions`, `check_llm_sdk_leak`).

## Q6 — Carryover

`AD-Memory-Formation-Auto-Extract` (Option B) · `AD-Memory-User-Upsert-By-Key` · `AD-Memory-Formation-Session-Recall` (缺口 2) · CARRY-026 (memory semantic/Qdrant axis) · tenant/role/session always-on injection. Recorded in `next-phase-candidates.md`.

## Q7 — Drive-through evidence

- User jamie@acme.com / acme-prod (`user_id=04dc4ee0-b672-4e44-a997-61c905ef2cb9`, baseline 0 rows).
- Leg 1 (formation): DB → `'User name is Chris.'` (0.90) + `'Chris is responsible for developing the Knowledge Connector feature on this platform.'` (0.85), both perm.
- Leg 2 (recall, trace `ddc56264484a496981f4d005a1a430e9`): NEW session, "你知道我是誰嗎?" → "你是 Chris。我也記得你目前負責…開發 Knowledge Connector"; 2 user-layer reads in Inspector.
- Leg 3 (isolation): priya@acme.com → "我不知道你是誰…"; `mentionsChris=false`.
- Screenshots `sprint-57-148/artifacts/sprint-57-148-{s1-formation,s2-recall,s3-isolation-priya}.png`. Full narrative: progress.md Day 3.

---

## Design Note Extract (spike sprint — §5.5)

**File**: `docs/03-implementation/agent-harness-planning/52-memory-formation-identity-design.md`
**Verified ratio (estimated)**: ~95% (every §3 invariant has file:line + a pytest verification or the real-Azure drive-through; §5 deferred items explicitly marked NOT verified)
**8-Point Quality Gate**:
- [x] 1. Section headers map to spike US (US-1..US-4 in §1)
- [x] 2. Each technical claim has file:line (§3 invariants 1-9)
- [x] 3. Decision rationale has comparison matrices (§2: formation A/B + surfacing always-on vs search vs broaden)
- [x] 4. Verification commands reproducible (§3: pytest per invariant + the drive-through reproduce)
- [x] 5. Test fixture reference (§3: the 11 new tests by name + the real 2-identity drive-through)
- [x] 6. Open invariants explicitly bounded (§5 verified-vs-deferred table + boundary statement)
- [x] 7. Rollback path (§6: user_id=None byte-identical + nudge gate + full revert < 1 hr, no migration/sentinel)
- [x] 8. 17.md cross-ref (§4: no new contract — reuses MemoryRetrieval / UserLayer / memory tools / PromptBuilder / system-prompt seam)

**Reviewer pass**: self-review (solo-dev).
