# Sprint 57.143 Retrospective — user Stop→continue durable interrupt-resume

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-143-plan.md) · [Progress](./progress.md)

---

## Q1. What was delivered?

Closed `AD-UserStop-Resume-Context` (Scope B, full CC parity). A user who hits Stop mid-run then types "continue" now keeps the interrupted run's context:
- **US-1**: `DBMessageStore` reworked to own-session-per-call (ctor takes a session factory; `load()`/`append()` open their own tenant-scoped session + `set_config('app.tenant_id')` for FORCE-RLS `messages`; `append()` commits immediately) → the turn-0 user prompt + completed tool batches survive a mid-run Stop. `loop.py` UNTOUCHED.
- **US-2**: `cancel_session` persists a `[Request interrupted by user]` marker via that same own-session path; the chat-v2 Stop button now also `POST /cancel` (fire-and-forget).
- CHANGE-110 + design note 47 (8/8 gate).

## Q2. Estimate accuracy / calibration

- Scope class **NEW `chatv2-userstop-resume-durability` 0.60** (1st data point). Parent-direct (`agent_factor` 1.0) → 3-segment form.
- Bottom-up est ~10.5 hr → class-calibrated commit ~6.3 hr (mult 0.60).
- **Actual ≈ commit (ratio ~1.0, IN band)** → KEEP 0.60. Clean execution: all 6 Day-0 D-rows GREEN (2 were scope REDUCTIONS — US-2 dropped the `get_db_session_with_tenant` dep + synthetic tool_results); backend tests passed first try; the drive-through caught the Stop mid-run on the FIRST attempt + the "continue" rehydration was conclusive. **The ceremony risk flagged in the plan did NOT materialize** — the fiddly Stop-timing drive-through went smoothly (dev-login UI + Playwright + a long-essay prompt gave a wide mid-run window), so this did NOT become a tiny-code-0.85 ceremony-dominant sprint; it had a real-code core (own-session refactor + RLS + cancel handler + FE + durability tests), consistent with the 57.137 "≥~3 hr real implementation core holds the 0.60 spike multiplier" lesson.

## Q3. What went well?

- **Evidence-first paid off**: the upstream gap doc (created same day, drive-through-verified) was already most of the eval; the Day-0 code verification CLOSED its one open question ("loop cancelled vs commit failed" → BOTH, and not mutually exclusive) and confirmed every anchor before any code.
- **Own-session localization**: choosing own-session-per-append (over router-early-persist) kept the fix to Cat 7 + got US-1 (prompt) AND US-3 (completed tool batches) for free, with `loop.py` UNTOUCHED.
- **Day-0 scope reductions**: discovering the 57.129 atomic-batch guarantee dropped synthetic tool_results; discovering the self-contained store dropped the cancel-handler DB dep — both shrank US-2 cleanly.
- **The drive-through was decisive**: the DB ledger showed the exact intended sequence (durable prompt at seq 5 + marker at seq 6) and the agent continued the ORIGINAL task on "continue" — the gate-only verification could never have proven this.

## Q4. What was harder / surprising?

- **Test isolation for own-session commits** (Risk Class C / D-test-isolation): the new own-session `append()` REALLY commits, breaking the existing `test_message_store.py` rollback-isolation. Resolved by mirroring the api/conftest committed-test pattern (a `committed_session` fixture that commits the seed for FK visibility + cleans up via tenant CASCADE). The retention/skills "set_config on the PASSED session" pattern did NOT map directly (those don't self-open) — the memory-layer factory pattern was the right precedent.
- **The "continue" agent behavior** (orthogonal to the fix): on resume the agent spent its turn budget calling `write_todos` (the 57.140 task primitive) to plan the essay and hit `max_turns` before emitting prose — the todos explicitly named the interrupted task, so the durable-resume proof is conclusive, but the agent's plan-don't-write choice is a task-primitive/turn-budget observation, not a defect here.
- 4 E501 trims on first-draft MHist/docstrings (the recurring char-budget lesson).

## Q5. Anti-pattern self-check (AP-2/3/4/6/8/11)

- **AP-2** (no orphan): own-session store reachable from `make_chat_message_store` (production) + the cancel marker from the live `/cancel` endpoint; FE cancelSession from the Stop button. ✅
- **AP-3** (no scatter): durability fix in ONE place (`DBMessageStore`); marker in the one cancel handler. ✅
- **AP-4** (no Potemkin): drive-through proved every control real — Stop aborts + fires /cancel + persists a REAL marker row; "continue" really rehydrated + continued the correct task. ✅
- **AP-6** (no speculative abstraction): dropped synthetic tool_results (no current need under 57.129) + cancel_event-poll (deferred); no "for the future" layer. ✅
- **AP-8** (PromptBuilder): N/A. ✅
- **AP-11** (no version suffix): no `_v2`/`_new`. ✅
- v2 lint tests 15 pass incl. llm_sdk_leak 3/3 (pure str; no native import). ✅

## Q6. Carryover / follow-ons

- `AD-Loop-CancelEvent-Poll-Phase58` — make the loop poll `cancel_event` for a graceful in-process stop + in-flight LLM cancel (today the abort tears it down; the marker covers coherence).
- partial assistant-answer streaming capture on abort.
- `message_events` (57.125/126 replay ledger) disconnect durability — separate from the `messages` rehydration ledger.
- leading-assistant-marker guard for the sub-second Stop-before-turn-0 race (Azure lenient today).

## Q7. Next

- `AD-UserStop-Resume-Context` CLOSED. Per the candidate pool, the remaining canonical research item is **#7 `AD-Tool-Description-Lint-Reflection`**; Phase-58 carryover ADs + this sprint's follow-ons are the rest.
- Rolling discipline: do NOT pre-write; the next sprint opens with an evidence-first eval when the user selects the direction.

## Design Note Extract (spike sprint)

**File**: `docs/03-implementation/agent-harness-planning/47-userstop-resume-durability-design.md`
**Verified ratio (estimated)**: ≥ 95%
**8-Point Quality Gate**: [x] 1 header→US [x] 2 file:line [x] 3 decision matrix [x] 4 verify command [x] 5 test fixture [x] 6 open-invariant boundary [x] 7 rollback [x] 8 17.md cross-ref (N/A justified — reuses Cat 7 MessageStore ABC, no new contract)
**Reviewer pass**: self-review (parent-direct)
