# Sprint 57.129 — Checklist (chat-v2 ledger intra-turn tool round-trips — persist the per-turn `assistant tool_use` + its `tool` results to the `messages` Cat-3 ledger. **Option A** (user-picked): incremental per-turn-batch persist in `_run_turns`'s `TOOL_USE` branch — mark `_tool_batch_start = len(messages)` before the assistant append, persist `messages[_tool_batch_start:]` after the post-tool checkpoint (the complete `[assistant tool_use, *tool results]` round-trip, atomic, only when well-formed → dangling-free). Reuses `_persist_to_ledger` + `DBMessageStore.append` + `message_serde`. **Pure backend** — 1 src EDIT (`loop.py`) + 1 test EDIT; ZERO frontend/CSS/Vitest/wire/codegen/migration; `message_serde`/`message_store` untouched; the final answer still end_turn-only (57.127). resume() pending-tool persist DEFERRED (sub-carryover). **Drive-through MANDATORY** — turn 1 a tool whose result is NOT in the final answer → turn 2 recovers it. CHANGE-096; continuation (NO design note).)

[Plan](./sprint-57-129-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `858bd3af`)
- [x] **Prong 1 — path verify**: `loop.py` / `message_store.py` / `message_serde.py` / the unit test exist; `CHANGE-096` free (Glob → none) ✅
- [x] **Prong 2 — content verify** (drift → progress.md):
  - [x] **D-toolbatch-marker-placement** — `# output_type == TOOL_USE` at `:2774`; assistant tool_use append `:2777`; post-tool checkpoint `yield post_tool_event` `:3072`; `finally:` `:3073` ✅
  - [x] **D-no-other-appends-in-window** — window `:2774-:3057` has ONLY `:2777` / `:2826` / `:3051`; `:2124` (injected) + `:2614/2615` (verification) are earlier → excluded ✅
  - [x] **D-early-return-paths** — cat9 (`:2819`), cancel (`:2900`), cat8 hard (`:2926`), cat8 soft (`:2995`) all `return` before the persist ✅
  - [x] **D-serde-toolcalls** — `message_serde.py:47-112` round-trips `tool_calls` + `tool_call_id` + `name` → NO serde edit ✅
  - [x] **D-persist-helper-docstring** — `_persist_to_ledger` `:1906-1913` says "never ... intra-turn tool round-trips" → updated this sprint (US-4) ✅
  - [x] **D-resume-pretool-append** — resume() appends pending-tool at `:3347`/`:3423` BEFORE `_run_turns` → DEFERRED sub-carryover ✅
- [x] **Prong 3 — schema verify**: `Message` ORM (`sessions.py:163-217`) has `sequence_num`/`turn_num`/`content_type`/`content`; reuses `DBMessageStore.append` → NO migration ✅
- [x] **D-baselines** — re-asserted: pytest **2724+5skip** · wire **24** · Vitest **904** · mockup **51** · mypy `src` **0/372** · run_all **10/10** ✅
- [x] **Catalog drift** — progress.md Day-0 table (6 D-IDs) ✅
- [x] **Go/no-go** — scope shift 0%; dangling-protection gate (marker-placement + early-return) GREEN → proceed ✅

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-129-chatv2-ledger-tool-roundtrips` (from `main` `858bd3af`) ✅

---

## Day 1 — Backend: `_run_turns` `TOOL_USE` persist + docstring (US-1..4)

### 1.1 `TOOL_USE` round-trip persist (US-1/2/3)
- [x] **`loop.py` (EDIT)**: `_tool_batch_start = len(messages)` before the `:2777` assistant tool_use append + `await self._persist_to_ledger(messages[_tool_batch_start:], turn_num=turn_count)` after the post-tool checkpoint (`:3072`), before `finally:` — with WHY-comments + MHist + Last Modified ✅
  - DoD: tool turn persists the complete round-trip batch; early-return mid-batch persists nothing; `message_store=None` → no-op; best-effort ✅
  - Verify: `mypy src` 0/372 ✅; the new `_persist_to_ledger` call site is in the `TOOL_USE` branch (3 sites: user@run-start / TOOL_USE-batch / final-answer@end_turn×2)
- [x] **batch correctness**: `messages[_tool_batch_start:]` == `[assistant tool_use, *tool results]` (D-no-other-appends-in-window confirms no stray append) ✅
  - DoD: the Day-2 atomicity test asserts the single-call batch shape ✅ (test_tool_round_trip_persisted_atomically)

### 1.2 `_persist_to_ledger` docstring (US-4)
- [x] **`loop.py` (EDIT)**: docstring updated — intra-turn tool round-trips ARE now passed (complete batch from the `TOOL_USE` branch), alongside user prompt + final answer; still never system / prior; no behaviour change. MHist ✅
  - DoD: docstring matches behaviour (Karpathy §3 stale-docstring); `mypy src` 0 ✅

### 1.3 Backend gate (partial)
- [x] black ✅ (reformatted) + isort ✅ + flake8 ✅ clean · mypy `src` **0/372** ✅ · run_all **10/10** ✅ (check_llm_sdk_leak clean — no provider import; check_event_schema_sync ✅ → wire 24)

---

## Day 2 — Backend test (US-5) + full gate

### 2.1 Tool-round-trip persist unit tests (US-5)
- [x] **`test_loop_multiturn_rehydration.py` (EDIT)**: extended `FakeMessageStore` with `append_calls`; added `_build_tool_loop` + `_tool_then_final_chat` (`calc_tool` returns `_TOOL_RESULT` not echoed in the answer); 3 new tests + 3 existing still pass (6/6) ✅
  - **test_run_persists_tool_round_trip** — `store.appended` roles == `[user, assistant, tool, assistant]`; the assistant carries `tool_calls`; the `tool` result has `tool_call_id` + the result text; the final answer never contains the result ✅
  - **test_tool_round_trip_persisted_atomically** — exactly ONE `append_calls` entry carries a tool_use, and it is `[assistant, tool]` (atomic → dangling-free evidence; chosen over a cat8/cat9-terminate test — the docstring documents the design property) ✅
  - **test_prior_tool_round_trip_rehydrated** — seeded prior `[user, assistant tool_use, tool result, assistant answer]` → run → the `tool` result + the assistant tool_use rehydrate into LLM request[0]; new user turn last ✅
  - Verify: `pytest ...test_loop_multiturn_rehydration.py -q` → **6 passed** ✅
- [x] **store integration unchanged**: `test_message_store.py` (already covers store-layer "round-trip incl. tool_calls") re-run green within the full suite (no edit needed) ✅

### 2.2 Backend gate (full)
- [x] mypy `src` **0/372** · run_all **10/10** (24) · full pytest **2727 passed / 5 skipped** (2724 baseline +3 new) · black/isort/flake8 clean · LLM-SDK-leak clean · NO frontend change (`git status --short frontend/` empty; Vitest 904 / mockup 51 UNCHANGED) ✅ — billing flake did NOT surface this run

---

## Day 3 — Drive-through (US-6) — real UI + real backend + real LLM (MANDATORY, tool-result-recovery)

### 3.1 Clean restart (Risk Class E — `loop.py` changed)
- [x] Fresh no-`--reload` `api.main:app` on :8000 (PID 40596, sole owner; startup log "pricing loader wired" + "startup complete"; `MAIN_TRANSCRIPT_OBSERVER` on); Vite :3007 untouched ✅
  - DoD: fresh sole :8000 owner; startup log confirms ✅

### 3.2 Drive-through (MANDATORY — NOT gate-only) — **PASS** (session `9150a32f`, real Azure gpt-5.2)
- [x] Tenant/policy where the tool **auto-approves (NO HITL pause)**: set acme-prod HITL `auto_approve_max_risk=MEDIUM` / `require_approval_min_risk=HIGH` (admin PUT) → python_sandbox (MEDIUM) auto-runs in-loop (avoids the resume() deferred path) ✅
- [x] turn 1 (real Azure): "Use the python sandbox to run `random.randint(100000,999999)`, reply with just EVEN or ODD." → python_sandbox AUTO-RAN, `stdout=333221`, answer **"ODD"** (number NOT in the answer); tool block + answer rendered live ✅
- [x] **THE fix**: same session, turn 2 (innocent) "Please add 7 to that number and tell me the sum." → answer **"333228"** (= 333221+7). 333221 is ONLY in the rehydrated tool result (turn-2 POST = {message, session_id}, no history) → the round-trip rehydrated + the LLM used it ✅
- [x] `messages` ledger (`verify_ledger.py 9150a32f`): **6 rows** — seq=2 assistant tool_calls=python_sandbox + seq=3 tool `{"stdout":"333221..."}` (the new persist) + seq=5/6 turn-2 user/answer "333228"; monotonic seq ✅
- [x] per-control AP-4 walk + screenshots (`drivethrough-PASS-toolcontext.jpeg` + d5d59c39 corroboration shots) + observed-vs-intended → progress.md Day 3; **PASS** — turn 2 used the rehydrated tool result on real LLM ✅
  - Note: a FALSE-ALARM "regression" (empty follow-up answers on a first session) was root-caused to Azure content-filter `jailbreak` 400 on adversarial recall prompts ("disregard/do-not-reveal/recall-don't-run-tool"), NOT my code — a no-tool follow-up (Paris→population) worked; innocent prompts work. Lesson logged in progress.md.

---

## Day 4 — CHANGE-096 + closeout

### 4.1 CHANGE-096
- [x] **`CHANGE-096-chatv2-ledger-tool-roundtrips.md`** (root cause + Option A per-turn-batch fix + dangling protection + drive-through PASS + AD closed + resume sub-carryover deferred) ✅

### 4.2 Closeout
- [x] retrospective.md Q1-Q7 + calibration (`chatv2-ledger-tool-roundtrips-wiring` 0.55 **→ re-pointed 0.85**, 1st data point; parent-direct, agent_factor 1.0; ratio ~1.9 over — ceremony/drive-through-dominated) + progress.md final ✅
- [x] Final gate sweep: mypy `src` **0/372** · run_all **10/10** (24) · pytest **2727+5skip** (+3, Day 2) · Vitest **904** UNCHANGED · mockup **51** · black/isort/flake8 clean · LLM-SDK-leak clean · frontend `git status` empty ✅
- [x] Navigators: CLAUDE.md Current-Sprint + Last-Updated (minimal-touch; 57.128 flipped MERGED) · MEMORY.md pointer + subfile `project_phase57_129_*` · next-phase-candidates (CLOSED `AD-ChatV2-Ledger-Tool-RoundTrips` + logged `AD-ChatV2-Resume-Tool-RoundTrips` sub-carryover) · sprint-workflow matrix `chatv2-ledger-tool-roundtrips-wiring` 0.85 row ✅
- [x] **Anti-pattern self-check** (retro Q5): AP-2/3/4/6/8/11 → 0 violations; v2 lints 10/10 ✅
- [x] **Local commit done** (10 files, 657+); ⏳ **PR push + open → CI → merge: PENDING USER CONFIRMATION** (push is outward-facing per Developer Preferences) → post-merge status flip after gh-verified MERGED
