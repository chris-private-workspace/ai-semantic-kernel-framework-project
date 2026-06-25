# Sprint 57.143 Progress — user Stop→continue durable interrupt-resume

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-143-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-143-checklist.md)

---

## Day 0 — 2026-06-25 — Plan-vs-Repo Verify (三-prong) + Branch

### Three-prong verify (against `main` HEAD `d7d97039`)

**Prong 1 — path verify** ✅
- EDIT present: `agent_harness/state_mgmt/message_store.py` · `api/v1/chat/_category_factories.py` · `api/v1/chat/router.py` · `frontend/src/features/chat_v2/services/chatService.ts` · `frontend/src/features/chat_v2/hooks/useLoopEventStream.ts`
- CHANGE-110 free (highest = CHANGE-109); design note 47 free (highest = 46)

**Prong 2 — content verify (drift findings)**

| ID | Finding | Implication |
|----|---------|-------------|
| **D-rls-own-session** | `messages` is FORCE ROW LEVEL SECURITY (`0009_rls_policies.py:97`) + policies `tenant_id = current_setting('app.tenant_id', true)::uuid` (L101-107). `retention.py:91-93` writes the SAME table from a fresh session via `SELECT set_config('app.tenant_id', :tid, true)`. | GREEN — US-1 own-session append must `set_config` before INSERT/SELECT; retention.py is the exact same-table precedent |
| **D-get-db-tenant-commit** | `get_db_session_with_tenant` (`tenant_context.py:264-277`) opens its own factory session + set_config + yield→`commit()`/rollback. | GREEN **+ simplification**: US-2 does NOT need this dep — the US-1-refactored `DBMessageStore` already self-manages its own session+set_config+commit, so `cancel_session` just constructs `DBMessageStore(get_session_factory(), …).append([marker])`. Plan §3.2 "Depends(get_db_session_with_tenant)" → dropped in favor of the self-contained store (cleaner, consistent with US-1). |
| **D-atomic-batch** | `_persist_to_ledger` docstring + 57.129: the tool batch `[assistant tool_use, *tool results]` is appended as ONE well-formed unit → the ledger never holds a `tool_use` without its result. | GREEN — US-2 synthetic tool_results DROPPED (moot, YAGNI per plan §3.x) |
| **D-factory-ctor** | `DBMessageStore(` constructed at exactly 2 src/test sites: `_category_factories.py:394` (factory) + `tests/integration/agent_harness/state_mgmt/test_message_store.py` (5 sites). No other src caller; subagent child loops pass None via the factory guard. | GREEN with action — the ctor→factory change must UPDATE `test_message_store.py` (5 construction sites). In-scope under US-1 tests. |
| **D-test-paths** | `DBMessageStore` test = **integration** (`tests/integration/agent_harness/state_mgmt/test_message_store.py`, real DB + db_session fixture). chat cancel = `tests/unit/api/v1/chat/test_router.py`. | GREEN with path correction — the durability test needs a REAL DB (own-session commit survives request-rollback) → it belongs in `tests/integration/agent_harness/state_mgmt/` (NOT a unit test as plan §4 #6 first wrote). Frontend Vitest path located Day 2. |
| **D-marker-role** | marker = `assistant` role → [user(orig), assistant("[Request interrupted by user]"), user(continue)] clean alternation. | GREEN — provider-validity proven by the Day-3 real_llm "continue" send |
| **D-test-isolation** (NEW, Risk Class C) | own-session `append()` now REALLY commits → the existing `test_message_store.py` rollback-based fixture isolation no longer rolls those rows back. | YELLOW — Day-1: migrate `test_message_store.py` + the new durability test to the retention/skills own-session test pattern (real-factory + dedicated test tenant + cleanup, NOT request-txn rollback). Within US-1 test scope. |

**Prong 3 — schema verify**: N/A for new schema (the marker is a new ROW in the existing `messages` table — no table/migration/column). Confirmed `messages` RLS policy shape in `0009` for the test's RLS assertion (D-rls-own-session).

**D-baselines** (57.142 closeout, re-verify Day-2 gate): pytest 2877+5skip · wire 26 · Vitest 920 · mockup 51 · mypy 0/381 · run_all (v2 lints) 21.

### Go/no-go: **GO**
All 6 planned D-rows GREEN; 1 NEW (D-test-isolation) YELLOW but within US-1 test scope. Two findings REDUCE scope (US-2 drops `get_db_session_with_tenant` dep + synthetic tool_results). Scope shift well under 20% (slightly reduced). Path corrections: durability test → integration dir; existing `test_message_store.py` updated for the factory ctor.

### Key design (locked)
- **US-1** own-session-per-append: `DBMessageStore` holds a `session_factory`; load/append open their own session + `set_config('app.tenant_id', tid, true)`; append commits → turn-0 user prompt + tool batches + final answer all immediately durable (loop.py UNTOUCHED). Mirrors `retention.py`.
- **US-2** Stop → abort (immediate) + `POST /cancel`; `cancel_session` persists an `assistant` `[Request interrupted by user]` marker via a self-contained `DBMessageStore` (best-effort, after `registry.cancel` True). cancel_event left unpolled (B-2; graceful-stop = Phase-58).
- **US-3** drive-through MANDATORY (real UI + backend + Azure gpt-5.2): Stop mid-run → continue → agent continues original task + DB shows the marker.

### Branch
`feature/sprint-57-143-userstop-resume-context` created from `main` `d7d97039`.

---

## Day 1 — 2026-06-25 — Durable own-session ledger (US-1)

- **`message_store.py`** (EDIT, Cat 7): `DBMessageStore` ctor `db_session` → `session_factory`; `load()`/`append()` each `async with self._factory() as db:` + `_set_tenant(db)` (`set_config('app.tenant_id', tid, true)` for FORCE-RLS `messages`); `append()` `await db.commit()` → each write immediately durable, independent of the SSE request txn. `_next_sequence_num(db)` runs in the same own session (MAX+1 monotonic across per-append commits). loop.py UNTOUCHED — turn-0/tool/final persist become durable for free. Header MHist + Description + WHY-section updated.
- **`_category_factories.py`** (EDIT): `make_chat_message_store` passes `get_session_factory()` (kept `db` only as the all-three-present signal; mirrors the memory-layer `del db` precedent).
- **`test_message_store.py`** (REWRITE): ctor → factory; NEW `committed_session` fixture (seed COMMITTED so the store's own session sees the session FK; cleanup deletes the tenant → FK CASCADE drops user/session/messages, mirrors api/conftest committed-test sweep) + NEW `test_append_survives_request_session_rollback` (the AD proof — append survives `db_session.rollback()`, a fresh store still loads the row).
- **Gate**: black/isort clean · flake8 0 (3 MHist/docstring E501 trimmed) · mypy `src` 0/381 · **6/6 integration tests pass** (was 5 + 1 durability).

## Day 2 — 2026-06-25 — Interrupt marker on Stop (US-2) + frontend wire

- **`router.py`** (EDIT): `INTERRUPT_MARKER = "[Request interrupted by user]"` module const (mirrors CC's INTERRUPT_MESSAGE); `cancel_session` after `registry.cancel` True persists `Message(role="assistant", content=INTERRUPT_MARKER)` via a self-contained `DBMessageStore(get_session_factory(), …)` (best-effort try/except — a marker-persist failure never fails the 204). Day-0 simplification confirmed: NO `get_db_session_with_tenant` dep needed (the store self-manages its tenant-scoped committed session). Header MHist updated.
- **`chatService.ts`** (EDIT): `cancelSession(sessionId)` → `POST /api/v1/chat/sessions/{id}/cancel` (mirrors `injectMessage`; throws on non-2xx).
- **`useLoopEventStream.ts`** (EDIT): `cancel()` → `abort()` + `setStatus("cancelled")` + `void cancelSession(sid).catch(() => {})` (fire-and-forget; a cancel API failure must NOT change the UI cancelled state). Stop button `InputBar.tsx` unchanged.
- **`test_cancel_marker.py`** (NEW, integration): marker persisted (assistant role + text) · cross-tenant cancel → 404 + NO marker. 2/2 pass.
- **`chatService.cancelSession.test.ts`** (NEW, Vitest): POST path + throw-on-non-2xx. 2/2 pass.
- **Full gate**: mypy `src` **0/381** · v2 lint tests **15 pass** (llm_sdk_leak 3/3) · flake8/black/isort clean · chat unit + state_mgmt + chat integration **177 pass** (no regression) · frontend **lint + build clean** · new Vitest 2/2. mockup UNTOUCHED (no CSS change).

### US-2 scope confirmations (vs plan)
- synthetic tool_results DROPPED (57.129 atomic-batch → no dangling tool_use; YAGNI).
- marker role = `assistant` (clean alternation in the normal [user, assistant, user] case); Day-3 real_llm "continue" send validates provider-acceptance.
- known edge (out of scope): if Stop fires before the loop's turn-0 persist (sub-second race), the ledger leads with the assistant marker — Azure (the real provider) is lenient on a leading assistant after system; noted for the design note.

## Day 3 — 2026-06-25 — Drive-through (US-3) — real UI + real backend + real Azure gpt-5.2

### Setup (Risk Class E)
- Clean backend restart via `dev.py restart backend` — the prior PID 19352 (`uvicorn ... --app-dir src`, NO `--reload`) ran stale pre-57.143 code; killed + fresh PID 3700 loads the new code. Frontend (port 3007, node) left untouched. dev-login (jamie@acme.com / acme-prod / Dev Tenant) via the real `/auth/dev` UI.

### Drive-through (real Azure gpt-5.2, session `35789e63-0f43-4957-944c-79cc845abf40`)
1. Sent prompt #0 ("Remember ZEBRA-7741…") → **completed** (memory_write + "Acknowledged…" + verification 0.99). Establishes prior context.
2. Sent a long-generation prompt ("…extremely long 1500-word essay on the complete history of computing…") → status **● running**.
3. **Hit Stop mid-run** (the `Stop` button, while `agent_loop.llm_call` was in flight) → UI flips to **● cancelled**.
4. Sent **"continue"** → status **● running** then **● completed**.

### THE verdict (observed vs intended) — PASS
DB `messages` ledger (artifacts/drivethrough-ledger-dump.txt), the exact intended durable sequence:

| seq | turn | role | content | proves |
|-----|------|------|---------|--------|
| 1 | 0 | user | "Remember … ZEBRA-7741 …" | prior turn |
| 2 | 0 | assistant | tool_calls (memory_write) | prior tool batch (57.129 atomic) |
| 3 | 0 | tool | memory_write result | — |
| 4 | 1 | assistant | "Acknowledged—I'll remember the code ZEBRA-7741." | prior answer |
| **5** | 0 | **user** | **"Now write … 1500-word essay … history of computing …"** | **US-1: the interrupted run's prompt SURVIVED the Stop (pre-57.143 this row would NOT exist)** |
| **6** | 0 | **assistant** | **"[Request interrupted by user]"** | **US-2: the /cancel marker persisted** |
| 7 | 0 | user | "continue" | the resume turn |
| 8-15 | 1-4 | assistant/tool | `write_todos`: "Outline … **computing history (abacus to AI)**" + "Draft a **~1500-word** detailed chronological essay …" | **end-to-end: rehydrated 19 messages (prompt_built messages_count:19) + continued the ORIGINAL task — NOT "continue from what?"** |

- **AP-4 check (not Potemkin)**: every control real — Stop button aborts + fires `POST /cancel` (the marker row 6 appeared) + status flips to cancelled; the durable rows (5) + marker (6) are REAL DB rows (real OTel SDK / real Azure run); "continue" really rehydrated + continued the correct task. Not a shell.
- **Honest observation (orthogonal to the fix)**: on "continue" the agent spent its turn budget calling `write_todos` (the 57.140 task primitive) to PLAN the essay (todos explicitly name the interrupted task) and hit `max_turns` before emitting the final prose — a task-primitive / turn-budget behavior, NOT a durable-resume defect. The durable-resume proof (the agent KNEW the interrupted task = the computing essay, from the rehydrated rows 5+6) is conclusive.
- Status transitions observed live: idle → running → **cancelled** (after Stop) → running → completed (after continue). The pre-57.143 symptom ("Continue from what, exactly?") did NOT occur.
- Evidence: `artifacts/drivethrough-continue.png` (full-page screenshot) + `artifacts/drivethrough-ledger-dump.txt` (15-row DB dump).
