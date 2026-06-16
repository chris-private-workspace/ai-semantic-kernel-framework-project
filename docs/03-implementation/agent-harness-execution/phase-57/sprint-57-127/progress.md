# Sprint 57.127 Progress — chat-v2 live multi-turn context (rehydrate prior conversation into the live loop)

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-127-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-127-checklist.md)

**Branch**: `feature/sprint-57-127-chatv2-live-multiturn-context` (from `main` `c1d3d1be`)
**AD**: `AD-ChatV2-Live-MultiTurn-Context` (the real product bug the 57.126 drive-through surfaced)
**Approach**: A (messages-table writer) — user-picked via AskUserQuestion 2026-06-16.

---

## Day 0 — Plan-vs-Repo Verify (三-prong) — YYYY-MM-DD (2026-06-16)

Investigation: 2 Explore sweeps (root-cause + Approach-A plumbing) + direct grep/read on `main` HEAD `c1d3d1be`.

### Drift findings

| D-ID | Finding | Implication |
|------|---------|-------------|
| **D-messagestore-wiring-site** ✅ FEASIBLE | `build_handler(db, session_id, tenant_id)` (`handler.py:732`) + `make_chat_state_deps(db, session_id, tenant_id)` (`_category_factories.py:309`, returns `(reducer, checkpointer)`, `(None,None)` when any missing). Main chat loop built at `handler.py:677` with `checkpointer=checkpointer` (`:720`). | The self-load seam is feasible. ADD a parallel `make_chat_message_store(db, session_id, tenant_id) -> MessageStore \| None` in `_category_factories.py`; wire `message_store=` onto the `:677` loop ONLY. Subagent loops (`:373`/`:410`) + the `:260` loop get NONE. |
| **D-abc-home** ✅ | `Checkpointer(ABC)` at `state_mgmt/_abc.py:30`. | `MessageStore` ABC → add to `state_mgmt/_abc.py` (match convention); `DBMessageStore` impl → new `state_mgmt/message_store.py`. |
| **D-checkpointer-binding** ✅ | loop ctor `checkpointer: Checkpointer \| None = None` (`loop.py:400`) → `self._checkpointer = checkpointer` (`:478`). `DBCheckpointer` bound to (db, session, tenant) at construction. | Mirror exactly: ctor `message_store: MessageStore \| None = None` + `self._message_store`. `DBMessageStore(db, session_id, tenant_id)` bound at construction. |
| **D-message-helpers-roundtrip** ⚠️ | `_message_to_dict` (`loop.py:258`) / `_message_from_dict` (`:296`) / `_content_block_to_dict` (`:282`) round-trip `role`/`content`/`tool_calls`/`tool_call_id`/`name` — **but NOT `metadata`** (the dataclass's local-bookkeeping flags `{"hitl"}`/`{"compacted_summary"}`). Same limitation the proven HITL-resume path has (`messages_from_metadata` uses the same serde). | metadata is "NOT sent to the LLM provider" (Message docstring) → losing it on rehydration does NOT affect the LLM's context/answer, only local compaction/prompt-builder tagging. **Acceptable** for the spike; disclose in design note 38 §open-invariants. **MOVE the 3 serde helpers to a neutral `_contracts/message_serde.py`** (leaf module) so `state_mgmt/message_store.py` can import them WITHOUT importing the heavy `orchestrator_loop/loop.py` (circular-import + weight risk); update `loop.py` to import them (+ `messages_from_metadata` keeps reading `_message_from_dict` from the new home). |
| **D-partition-coverage** 🟢 SCOPE-REDUCED | `0002` created `messages_2026_04/05/06` (+ `message_events_*`) only — BUT `0028_sidechain_sessions.py:75-76` created `messages_default` AND `message_events_default` DEFAULT partitions. | **NO cliff** — any row not matching an explicit monthly partition lands in `*_default`. **US-6 conditional forward-partition migration is DROPPED** (file-change item #8 removed). Note the pg_partman automation is still the long-term fix (tracked infra AD), but writes never fail. |
| **D-message-orm-shape** ✅ | `Message` ORM (`sessions.py:163-217`): `role` String(32), `content_type` String(32), `content` JSONB, `sequence_num` Int, `turn_num` Int, nullable `model`/`tokens_*`, `is_compacted`; composite PK `(id, created_at)`; UNIQUE `(session_id, sequence_num, created_at)`. | Writer: `content = _message_to_dict(m)` (full payload), `content_type = "text"\|"blocks"`, `role = m.role`, seq from MAX, turn_num from state. UNIQUE → seq must be monotonic per session (seed from MAX, like 57.126's main_seq). |
| **D-loop-append-sites** ⏳ (Day-1) | run()/_run_turns append the user message (run start), the assistant response (per turn), and tool-result messages. Exact sites to be read during implementation. | Capture the run's NEW messages via a compaction-immune `new_this_run` side-list (instrument each real-message append) OR a slice-at-completion; pick at implementation after reading run() (the side-list is compaction-immune; the slice is simpler but vulnerable if compaction edits `messages` mid-run). Append once at the LoopCompleted exit. |
| **D-baselines** ✅ | full pytest **2712+5skip** · wire **24** · Vitest **904** · mockup **51** · mypy `src` **0/370** · run_all **10/10** (57.126 + #302 closeout). | Re-assert at the gate. |

### Scope deltas from Day-0 (vs plan as drafted)

1. **DROP** the conditional forward-partition migration (US-6 / file #8) — DEFAULT partitions already exist (`0028`). US-6 becomes "verified, no migration".
2. **ADD** `backend/src/agent_harness/_contracts/message_serde.py` (NEW) — relocate the 3 serde helpers from `loop.py` (avoids `state_mgmt → loop.py` heavy/circular import). `loop.py` imports them.
3. **ADD** `backend/src/api/v1/chat/_category_factories.py` (EDIT) — `make_chat_message_store(db, session_id, tenant_id)` factory (mirror `make_chat_state_deps`).

Net: a small REDUCTION (drop migration) + 2 small additions; well under the 20% threshold → **go/no-go: CONTINUE Day 1**. (Findings catalogued here per sprint-workflow §Step 2.5; the plan's §Risks already anticipated D-partition-coverage as conditional + D-message-helpers exposure — both now resolved.)

### Go / No-Go
✅ **GO** — Approach-A self-load seam confirmed feasible (wiring site has db/session/tenant); partitions safe; serde relocatable. Scope net-reduced.

---

## Day 1-2 — Backend implementation + tests — 2026-06-16

### Implemented (Approach A — MessageStore ABC, loop self-load + persist)
- **`_contracts/message_serde.py`** (NEW): relocated `_message_to_dict`/`_message_from_dict`/`_content_block_to_dict` from `loop.py` to the `_contracts` leaf (so `state_mgmt` imports them WITHOUT importing the heavy loop — circular-import safety). `loop.py` imports them; `messages_from_metadata` stays in loop.py.
- **`state_mgmt/_abc.py`** (EDIT): `MessageStore` ABC (`load()` + `append(messages, *, turn_num)`, bound to session+tenant) — sibling to `Checkpointer`.
- **`state_mgmt/message_store.py`** (NEW): `DBMessageStore` — `load()` (SELECT WHERE session&tenant ORDER BY sequence_num → `_message_from_dict`), `append()` (seq from MAX, best-effort `begin_nested()` SAVEPOINT). load + append both best-effort (degrade, never break the send).
- **`state_mgmt/__init__.py`** (EDIT): export `MessageStore` + `DBMessageStore`.
- **`loop.py`** (EDIT): ctor `+message_store`; `run()` self-loads prior + seeds (system reconstructed fresh, NEVER persisted; prior NOT re-persisted) + persists the user prompt at send start; the 2 end_turn sites (stop_reason terminator + FINAL branch) persist the final answer (NOT in `messages` — the loop ends without appending it). `loop.run()` ABC signature UNCHANGED. Covers run() + resume().
- **`_category_factories.py`** (EDIT): `make_chat_message_store` (None-guard mirrors `make_chat_state_deps`).
- **`handler.py`** (EDIT): `build_handler` injects `DBMessageStore` onto the MAIN chat loop only (subagent child loops get none).

### Day-1 design refinement (caught reading the loop)
The FINAL branch yields end_turn WITHOUT appending the answer to `messages` → instrumenting `messages.append` sites would MISS the answer. **De-risked decision**: persist **user prompt (send start) + final answer (2 end_turn sites)** — NO tool-site instrumentation, NO dangling-tool_call risk, NO compaction/side-list complexity. V1 cross-send history = user + final-answer (verbatim Cat-3 Messages); **intra-turn tool round-trips are a documented follow-on** (`AD-ChatV2-Ledger-Tool-RoundTrips`). NOT lossy Approach-B reconstruction — verbatim Message objects. Bug (text multi-turn) fully covered; drive-through is the proof.
- Noted: `metadata` (Message local flags) NOT round-tripped by the shared serde (same as the proven HITL-resume path) — not sent to the LLM → no context impact; disclosed in design note 38.

### Tests (US-7)
- **`test_message_store.py`** (integration, 5 passed): append/load round-trip incl. tool_calls fidelity · seq from MAX (2-send, no collision) · cross-tenant load → [] (鐵律) · append([]) no-op · factory None-guard.
- **`test_loop_multiturn_rehydration.py`** (unit, 3 passed): run() persists user+final-answer (system never) · **prior rehydrated INTO the LLM request** (the fix, asserted on `CapturingChatClient.requests[0]`) · no-store single-turn baseline.
- Separate handler-integration test COVERED by the loop unit test (same run()-self-load mechanism) + wiring mypy-checked (1 line) + Day-3 drive-through end-to-end → not authored separately (avoids heavy build_handler harness; rationale recorded).

### Gate (Day 1-2 full)
mypy `src` **0/372** · flake8 src+tests clean · run_all **10/10** (wire **24**) · full pytest **2720 passed / 5 skipped** (+8) · frontend UNCHANGED (Vitest 904 / mockup 51). NO migration (Day-0: `messages_default`+`message_events_default` partitions exist → no cliff).

---

## Day 3 — Drive-through (real UI + real backend + real LLM) — 2026-06-16

**MANDATORY** per US-8 + the Drive-Through Acceptance hard constraint. The exact 57.126 failing case re-driven.

### Setup (Risk Class E — clean restart)
- Pre-check: `Win32_Process` python sweep → only an unrelated `http.server 8090`; :8000 FREE (no orphan spawn-worker). Frontend :3007 up (PID 31616, node — NOT stopped).
- Started a clean no-`--reload` `uvicorn api.main:app` (PYTHONPATH=backend/src) → sole :8000 owner **PID 45768**; startup log confirms `pricing loader wired` + `startup complete` (Risk Class E satisfied — fresh process serves the post-edit `loop.py`/`handler.py`).
- Log: `artifacts/backend-drivethrough.log`.

### Driven flow (real chat-v2 UI via Playwright, dev-login jamie@acme.com / acme-prod, mode `real_llm` = Azure gpt-5.2)
| Step | Action | Observed | Verdict |
|------|--------|----------|---------|
| 1 | Send turn 1 "What is the capital of France?" | Agent: **"Paris."** · verification passed 0.99 · `prompt_built messages_count=4` | ✅ |
| 2 | Send turn 2 (SAME session `9e89775d`) "What is its population?" | Agent: **"Paris has about 2.1 million residents in the city proper (as of the most recent official estimates)."** · verification passed 0.99 · `prompt_built messages_count=6` | ✅ **THE FIX** |

### Three-layer proof (gate / probe / drive-through — all PASS)
1. **Writer (DB ledger)** — `artifacts/verify_ledger.py` via the app's own session factory: 4 rows for session `9e89775d`, `sequence_num` 1→4 monotonic — `user`/`assistant` × 2 sends, content verbatim (incl. the `Message` JSONB payload). The writer half works end-to-end.
2. **Reader (rehydration)** — turn 1 `messages_count=4` → turn 2 `messages_count=6` (**+2** = the prior user "capital of France?" + assistant "Paris." prepended). The +2 can ONLY come from the persisted ledger round-trip (turn-1 persist → turn-2 load). Before the fix turn 2 would also be 4.
3. **Semantic end-to-end** — turn 2 resolved "**its**" → Paris and answered ~2.1M (NOT "what does 'it' refer to" — the 57.126 failure). Bug FIXED on real LLM.

### AP-4 per-control walk
- Composer: typeable, Enter sends, Send button enables/disables correctly. ✅ (no dead control)
- Agent answer block: real LLM content rendered (not fixture/echo). ✅
- Verification badge: real `llm_judge` score 0.99 rendered per turn. ✅
- Inspector Turn tab: real `tokens.in=2,425 / out=6`, real `trace_id`, `active_skill —`. ✅
- Isolation: a fresh "New session" starts at `messages_count` base (no prior inherited) — confirmed by the turn-1 `messages_count=4` on the fresh session. ✅

### Evidence
- `artifacts/sprint-57-127-drivethrough-turn1.png` (turn 1 → "Paris.")
- `artifacts/sprint-57-127-drivethrough-turn2.png` (turn 2 → "Paris has about 2.1 million…", both turns + verification badges rendered)
- `artifacts/backend-drivethrough.log` (clean startup), `artifacts/verify_ledger.py` (ledger dump script + output in progress).

### Minor (cosmetic, not a defect)
- All 4 rows show `turn_num=0` — each send is its own `run()` starting at turn 0; cross-send ordering is via `sequence_num` (1-4 monotonic, seeded from MAX), which is correct. `turn_num` is intra-run only. Noted for the design note; no fix needed this slice.

### Verdict
✅ **DRIVE-THROUGH PASS** — the 57.126 live-multi-turn-context bug is fixed end-to-end on real Azure gpt-5.2 through the real chat-v2 UI. `AD-ChatV2-Live-MultiTurn-Context` behavior satisfied.

---

## Day 4 — Closeout — 2026-06-16

- Drive-through PASS recorded (Day 3 above) + screenshots/log/ledger in `artifacts/`.
- CHANGE-094 (`claudedocs/4-changes/feature-changes/CHANGE-094-chatv2-live-multiturn-context.md`).
- Design note 38 (`docs/03-implementation/agent-harness-planning/38-chatv2-multiturn-rehydration-spike.md`, spike-extract 8-pt gate).
- 17.md: registered the new `MessageStore` ABC contract (§ Cat 7 / Checkpointer sibling).
- retrospective.md: Q1-Q7 + calibration (`chatv2-multiturn-rehydration-spike` 0.60, 1st data point).
- Navigators: CLAUDE.md Current Sprint row + Last Updated; MEMORY.md pointer; memory subfile `project_phase57_127_*.md`.
- `AD-ChatV2-Live-MultiTurn-Context` CLOSED; new carryover `AD-ChatV2-Ledger-Tool-RoundTrips` (intra-turn tool round-trips not yet persisted) + the pre-existing `AD-ChatV2-Resume-Transcript-Persistence` (57.125 resume gap) recorded in next-phase-candidates.

### Plan deviations (documented, honest)
1. **Persistence mechanism simplified vs plan §3.2** — plan envisioned a compaction-immune `new_this_run` side-list recording EVERY message-append site (incl. tool results). Day-1 reading of `run()` found the FINAL branch yields end_turn WITHOUT appending the answer to `messages`, so instrumenting `messages.append` would MISS the answer. **De-risked decision**: persist the **user prompt (send start) + the final answer (2 end_turn sites)** directly — no side-list, no tool-site instrumentation, no dangling-tool_call risk. V1 cross-send history = user + final-answer (verbatim Cat-3 Messages). **Intra-turn tool round-trips deferred → `AD-ChatV2-Ledger-Tool-RoundTrips`.** Fully covers the reported text-multi-turn bug (drive-through proof). NOT lossy reconstruction.
2. **Serde relocation** — `_message_to_dict`/`_message_from_dict`/`_content_block_to_dict` moved from `loop.py` to a new `_contracts/message_serde.py` leaf (so `state_mgmt` imports them without importing the heavy `loop.py` — circular-import safety). `messages_from_metadata` stays in `loop.py`.
3. **Integration test substitution** — plan #7 `test_chat_multiturn_context.py` (chat-POST harness) → realized as `test_message_store.py` (real-PG integration, 5 cases incl. cross-tenant []) + the loop unit `test_loop_multiturn_rehydration.py` (3 cases incl. prior-reaches-LLM-request). The 2-send rehydration is proven by the loop unit (same `run()` self-load mechanism) + the Day-3 drive-through; a separate heavy `build_handler` harness was not authored (rationale: redundant with the drive-through + loop unit).
4. **No partition migration** (plan #8 conditional) — Day-0 confirmed `messages_default` + `message_events_default` partitions exist (`0028`) → no 2026-07 cliff → migration DROPPED.

### Final gate (Day 4)
- black/isort/flake8 clean · mypy `src` **0/372** · run_all **10/10** (wire **24**, LLM-SDK-leak clean) · frontend UNCHANGED (`diff styles-mockup.css` empty; Vitest 904 / mockup 51).
- **Full pytest**: 1st run **2719 passed / 1 failed / 5 skipped** — the failure was `tests/integration/billing/test_billing_outbox_drain.py::test_drain_materializes_cost_ledger_parity`, an **intermittent pre-existing Risk Class C flake** (billing/cost_ledger is UNTOUCHED by 57.127). Investigated (Failure Investigation rule): passes in isolation (0.32s), passes adjacent to the new `test_message_store.py` (10 passed), and the **full re-run was clean 2720 passed / 5 skipped**. Root cause = a latent cross-test isolation flake (the billing parity test depends on cost_ledger/outbox-drainer singleton state that some other TestClient-based integration test pollutes non-deterministically); 57.127's 2 new test files merely shifted collection order (the FIX-032 pattern) — NOT a regression. Authoritative gate = the clean re-run **2720 passed / 5 skipped (+8 vs the 2712 baseline)**.
- **Carryover logged** (not silently ignored): `AD-Billing-Outbox-Drain-Test-Flake` (🟢) → next-phase-candidates. If CI hits this intermittent flake → re-run CI (do NOT skip the test); a proper fix = an autouse cost_ledger/outbox singleton reset per the FIX-032 / Risk Class C precedent.
