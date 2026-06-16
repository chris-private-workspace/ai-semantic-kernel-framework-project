# Sprint 57.127 Retrospective — chat-v2 live multi-turn context

**Closed**: 2026-06-16
**Branch**: `feature/sprint-57-127-chatv2-live-multiturn-context` (from `main` `c1d3d1be`)
**AD closed**: `AD-ChatV2-Live-MultiTurn-Context`
**Class**: `chatv2-multiturn-rehydration-spike` 0.60 (NEW, 1st data point) · parent-direct · `agent_factor` 1.0

---

## Q1 — What shipped?

A durable per-session Cat-3 `Message` ledger for the live chat-v2 loop, fixing the 57.126-surfaced bug where a follow-up send lost the prior conversation. New provider-neutral `MessageStore` ABC + `DBMessageStore` (tenant-scoped, seq-from-MAX, best-effort SAVEPOINT); serde relocated to `_contracts/message_serde.py` (circular-import safety); loop self-loads prior at `run()` start + persists user prompt (start) + final answer (2 end_turn sites); `make_chat_message_store` factory + `build_handler` injection (main loop only). `loop.run()` ABC signature UNCHANGED. Pure backend.

**Files**: 5 EDIT (`loop.py`, `state_mgmt/_abc.py`, `state_mgmt/__init__.py`, `_category_factories.py`, `handler.py`) + 2 NEW src (`_contracts/message_serde.py`, `state_mgmt/message_store.py`) + 2 NEW tests + CHANGE-094 + design note 38.

## Q2 — Calibration

- **Class**: `chatv2-multiturn-rehydration-spike` **0.60** (NEW). Closest precedents: `subagent-child-loop-spike` 0.60 + `verification-in-loop-spike` 0.60 — both new-domain `loop.py`-core touches reusing a proven injected-ABC pattern. The new ABC + the persist-point precision (don't re-persist prior/system, seq-from-MAX) + the mandatory drive-through put it at 0.60, not a pure-wiring 0.55.
- **Agent-delegated: no** (parent-direct). The persist-point dedup, the self-load-vs-param seam, the tenant-scoped best-effort writer, and the FINAL-branch answer-capture refinement are correctness-critical and were hand-authored + self-verified. `agent_factor` 1.0 → 3-segment form.
- **Bottom-up est ~11 hr → class-calibrated commit ~6.6 hr (mult 0.60)**.
- **Actual ~6.5 hr** → ratio vs committed **~0.98 IN band**. Breakdown: Day-0 三-prong + 2 Explore sweeps ~1.5 · serde move + ABC + `DBMessageStore` ~1.5 · loop self-load + persist points (incl. the FINAL-branch refinement) ~2.0 · factory + wiring ~0.5 · 2 test files ~1.5 · drive-through + clean restart ~1.0 · closeout (CHANGE-094 + design note 38 + retro + navigators) ~1.5. (Day-0's scope NET-REDUCTION — dropping the migration + the side-list — offset the extra serde-relocation + factory work.)
- **Verdict**: KEEP 0.60 (1st data point, ratio ~0.98 IN band). If a 2nd `chatv2-multiturn-rehydration-spike` diverges > 30%, re-point.

## Q3 — What went well?

1. **Day-0 三-prong caught the de-risk early** — reading `run()` revealed the FINAL branch yields end_turn WITHOUT appending the answer to `messages`. Catching this at Day-0/Day-1 (not the drive-through) let us drop the plan's side-list mechanism for a simpler, correct 2-point persist (user-at-start + answer-at-end) — no dangling-tool_call risk, no `_record_new` plumbing.
2. **Self-load seam kept the blast radius tiny** — `loop.run()`'s ABC signature unchanged → zero ripple to the router, subagent fork/teammate callers, or their tests. Only an optional ctor param + a factory + 1 injection line.
3. **The drive-through was decisive and layered** — the `messages_count` 4→6 delta is a clean mechanical proof of the full DB round-trip (the +2 can only come from the persisted ledger), independent of the LLM's semantic answer. Both agreed.
4. **Pure-backend discipline held** — zero frontend/CSS/Vitest/wire/codegen change; the frontend already continues the session (57.126 groundwork paid off).

## Q4 — What to improve?

1. **Plan over-specified the mechanism** — the plan committed to a `new_this_run` side-list + `_record_new` helper before reading the exact append sites; the FINAL-branch reality forced a simpler design Day-1. Lesson: for loop-lifecycle touches, Day-0 should read the ACTUAL yield/append sites before the plan commits to an instrumentation shape (Prong-2 "read the producer body", already a rule — apply it to control-flow sites, not just data shapes).
2. **Direct asyncpg verification tripped on creds** — the naive asyncpg connect failed auth; the app's own `get_session_factory()` was the reliable path. Lesson: for one-off DB verification, use the app's session factory (single-source DATABASE_URL), not a hand-built connection.

## Q5 — Anti-pattern self-check (0 violations)

- **AP-2** (no side-track): the store is on the 主流量, wired from `build_handler`, exercised by the drive-through. ✅
- **AP-3** (one home): all persistence in `state_mgmt/`; serde in `_contracts/` leaf. ✅
- **AP-4** (no Potemkin): real multi-turn context proven LIVE on real Azure (not gate-only). ✅
- **AP-6** (no speculation): `model`/`tokens_*`/backfill/tool-roundtrips deferred (YAGNI / explicit ADs), not pre-built. ✅
- **AP-8** (no bare message assembly): reuses `_message_to_dict`/`_message_from_dict`. ✅
- **AP-11** (no version suffix): `MessageStore`/`DBMessageStore`, no `_v2`. ✅

## Q6 — Drive-through (MANDATORY — PASS)

Real chat-v2 UI + clean-restart backend (PID 45768, pricing wired) + real Azure gpt-5.2, session `9e89775d`:
- turn 1 "capital of France?" → "Paris." (`messages_count=4`, verification 0.99)
- turn 2 "its population?" → "Paris has about 2.1 million residents…" (`messages_count=6` = 4 +2 rehydrated, verification 0.99) — **resolved "its"→Paris**, the exact 57.126 failure now fixed.
- DB ledger: 4 rows, `sequence_num` 1→4 monotonic (`verify_ledger.py`). Screenshots + log in `artifacts/`.

## Q7 — Carryover (→ next-phase-candidates.md)

- **NEW** `AD-ChatV2-Ledger-Tool-RoundTrips` (🟡) — persist intra-turn assistant/tool messages (this slice persists only user + final answer). Avoids the dangling-tool_call risk; needed for full tool-context multi-turn.
- **Pre-existing** `AD-ChatV2-Resume-Transcript-Persistence` (57.125 resume-path gap) — unchanged.
- **Deferred infra** — `message_events`/`messages` consolidation (canonical-ledger AD); pg_partman partition automation; `turn_num` cross-send counter (cosmetic).

---

## Design Note Extract (spike sprint)

**File**: `docs/03-implementation/agent-harness-planning/38-chatv2-multiturn-rehydration-spike.md`
**Verified ratio (estimated)**: ~95% (every claim carries a file:line + a reproduce command)
**8-Point Quality Gate**:
- [x] 1. Section header maps to spike US (§1 Spike Summary → US-1..8)
- [x] 2. file:line on each claim (§3 Verified Invariants — `loop.py:1932`, `message_store.py:115`, etc.)
- [x] 3. Decision matrix (§2 — A vs B vs C with reject reasons)
- [x] 4. Verification command (pytest paths + drive-through reproduce)
- [x] 5. Test fixture (`test_message_store.py` / `test_loop_multiturn_rehydration.py`)
- [x] 6. Open-invariant boundary (§5 — tool-roundtrips / resume / metadata / backfill / consolidation explicitly deferred)
- [x] 7. Rollback path (§6 — drop the 1-line injection; <30 min; no migration)
- [x] 8. 17.md cross-ref (§4 — `MessageStore` ABC registered)

**Reviewer pass**: self-review (parent-direct sprint).
