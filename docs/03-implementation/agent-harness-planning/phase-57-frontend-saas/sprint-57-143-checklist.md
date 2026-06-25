# Sprint 57.143 — Checklist (user Stop→continue durable interrupt-resume)

[Plan](./sprint-57-143-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `d7d97039`)
- [x] **Prong 1 — path verify**: EDIT files present (`message_store.py` / `_category_factories.py` / `router.py` / `chatService.ts` / `useLoopEventStream.ts`); NEW test free; `CHANGE-110` + design note `47` free
- [x] **Prong 2 — content verify** (drift → progress.md):
  - [x] **D-rls-own-session** — `retention.py:91-93` confirms `SELECT set_config('app.tenant_id', :tid, true)` per own session enables INSERT/SELECT on FORCE-RLS `messages`; this is the US-1 append pattern
  - [x] **D-get-db-tenant-commit** — read `tenant_context.py:243` `get_db_session_with_tenant`: does it `commit()` on success (like `session.py:54`)? → US-2 marker commit path
  - [x] **D-atomic-batch** — `loop.py` `_persist_to_ledger` / 57.129: confirm tool batch `[assistant tool_use, *tool results]` is one atomic append → ledger never holds a dangling tool_use → drop synthetic tool_results
  - [x] **D-factory-ctor** — grep `DBMessageStore(` across backend: only `make_chat_message_store` constructs it (child loops pass None) → ctor signature change safe
  - [x] **D-test-paths** — locate the 57.127 `DBMessageStore` test + the chat-router cancel test + the `chatService`/`useLoopEventStream` Vitest paths
  - [x] **D-marker-role** — decide `assistant`-role marker; note the next real_llm "continue" send (drive-through) proves provider-validity of [user, assistant, user]
- [x] **Prong 3 — schema verify**: N/A (no new table / migration / column — the marker is a new ROW in the existing `messages` table); BUT confirm `messages` RLS policy names in `0009` for the test's RLS assertion
- [x] **D-baselines** — pytest 2877+5skip · wire 26 · Vitest 920 · mockup 51 · mypy 0/381 · run_all 21
- [x] **Catalog drift** — progress.md Day-0 table (all D-rows)
- [x] **Go/no-go** — proceed if scope shift ≤ 20%

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-143-userstop-resume-context` (from `main` `d7d97039`)

---

## Day 1 — Durable own-session ledger (US-1)

### 1.1 `DBMessageStore` → own-session + RLS set_config
- [x] **ctor takes `session_factory` (was bound session); `load()`/`append()` open their own session + `set_config('app.tenant_id', tid, true)`; `append()` commits**
  - DoD: `append` survives a request-txn rollback (own commit); `load()` reads committed rows; `_next_sequence_num` MAX+1 monotonic across per-append commits; best-effort swallow+log preserved; header MHist updated (Cat 7 behavioral change)
  - Verify: `pytest tests/unit/agent_harness/state_mgmt/test_message_store_durability.py`

### 1.2 `make_chat_message_store` factory wiring
- [x] **`make_chat_message_store` passes `get_session_factory()` (`del db`, mirror memory-layer precedent `_category_factories.py:297`)**
  - DoD: subagent-child None-guard intact; existing chat path still rehydrates (no behavior change on natural completion); no other `DBMessageStore(db,…)` caller (D-factory-ctor)
  - Verify: `pytest tests/unit/.../test_*message_store* tests/.../chat -q`

### 1.3 Durability + multi-tenant tests
- [x] **`test_message_store_durability.py`**: own-session commit persists despite request-rollback · cross-tenant load → [] · RLS set_config required (without it, INSERT blocked) · sequence monotonic
  - DoD: tests fail against the OLD `begin_nested()` impl, pass against the new; mirror retention/skills RLS test pattern (Risk Class C — use session fixtures + autouse reset)
  - Verify: `pytest tests/unit/agent_harness/state_mgmt/ -q`

### 1.x partial gate
- [x] black/isort/flake8 clean · mypy `src` 0/381 · LLM-SDK-leak clean

---

## Day 2 — Interrupt marker on Stop (US-2) + frontend wire

### 2.1 `cancel_session` persists the marker (backend)
- [x] **`router.cancel_session` + `Depends(get_db_session_with_tenant)` → persist `assistant` `[Request interrupted by user]` via `DBMessageStore` (best-effort, after `registry.cancel` True)**
  - DoD: cross-tenant cancel → 404 + no marker; marker-persist failure does NOT fail the 204; marker `sequence_num` = MAX+1 (after the durable turn-0); header MHist updated
  - Verify: `pytest tests/.../test_chat_cancel_marker.py`

### 2.2 Frontend Stop → `/cancel`
- [x] **`chatService.cancelSession(id)` (POST /sessions/{id}/cancel, mirror `injectMessage`) + `useLoopEventStream.cancel` → `abort()` + `void cancelSession(sid)`**
  - DoD: Stop still aborts immediately (today's feel); cancel API failure leaves UI `cancelled` (no throw); Stop button `InputBar.tsx:288` unchanged
  - Verify: `npm run test -- chatService useLoopEventStream` (cancel path)

### 2.x Full gate
- [x] mypy `src` 0/381 · run_all 21/21 (incl. llm_sdk_leak) · backend pytest 2877+new · Vitest 920+new · `npm run lint && npm run build` clean (NO `--silent`) · mockup 51 (`diff` empty — UNTOUCHED) · black/isort/flake8 clean · LLM-SDK-leak clean

---

## Day 3 — Drive-through (US-3) — real UI + real backend + real Azure gpt-5.2

### 3.1 Clean restart (Risk Class E)
- [x] Kill stale `--reload` reloader + orphan spawn-workers (the own-session factory is wired at startup); confirm fresh sole port owner + startup log; rebuild Vite (FE changed)

### 3.2 Drive-through (MANDATORY — NOT gate-only)
- [x] Send a quick completing turn (establish prior) → send a long-generation turn → **hit Stop mid-run** → send "continue"
- [x] **THE fix (real UI)**: agent continues the ORIGINAL task (NOT "continue from what?"); the Stop fired `/cancel` (network tab); DB `messages` shows `[user(orig), assistant("[Request interrupted by user]"), user(continue)]`; per-control AP-4 walk (Stop clickable / aborts / persists marker / continue rehydrates)
- [x] Screenshot + observed-vs-intended + DB ledger dump → progress.md Day 3 + artifacts/

---

## Day 4 — CHANGE-110 + design note 47 + closeout

### 4.1 CHANGE-110 + design note
- [x] **`CHANGE-110-userstop-resume-context.md`** (gap + root cause + own-session+marker fix + drive-through PASS + AD closed)
- [x] **Spike design note `47-userstop-resume-durability-design.md`** (8-point gate; the durable-ledger own-session contract + interrupt-marker + cancel-flow; §3 cross-category — reuses Cat 7 MessageStore ABC, justify if N/A; reference the gap doc for the analysis)

### 4.2 Closeout
- [x] retrospective.md Q1-Q7 + calibration (`chatv2-userstop-resume-durability` 0.60, 1st data point; flag if ratio > 1.20 → re-point 0.85 per ceremony pattern)
- [x] Final gate sweep: mypy · run_all · pytest · Vitest · mockup · build · lint · LLM-SDK-leak
- [x] Navigators: CLAUDE.md Current-Sprint + Last-Updated · MEMORY.md pointer + subfile · next-phase-candidates (CLOSE `AD-UserStop-Resume-Context`; log `AD-Loop-CancelEvent-Poll-Phase58`) · sprint-workflow matrix (`chatv2-userstop-resume-durability` row)
- [x] Anti-pattern self-check (retro Q5): AP-2/3/4/6/8/11 → violations; v2 lints 21/21
- [x] **Commit** (local DONE) → ⏳ PR push + open → CI → merge: PENDING USER CONFIRMATION (push is outward-facing per Developer Preferences) → post-merge status flip after gh-verified MERGED
