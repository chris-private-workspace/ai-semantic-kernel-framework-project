# Sprint 57.129 Plan — chat-v2 ledger intra-turn tool round-trips (persist the per-turn `assistant tool_use` + its `tool` results to the `messages` Cat-3 ledger). Closes `AD-ChatV2-Ledger-Tool-RoundTrips` — the 57.127 carryover: 57.127's `messages` ledger persists ONLY the user prompt (at send start) + the final answer (at end_turn), so a follow-up send rehydrates `[user, final-answer]` but NOT the intra-turn tool interactions. Symptom: a multi-turn follow-up that references a prior tool result (e.g. "re-run that search", "what was the exact number?") loses the tool context — the prior turn's `assistant tool_use` message + its `tool` result messages were never in the ledger, only the summarized final answer. **User decision (2026-06-16 AskUserQuestion): Option A — incremental per-turn-batch persist** (over Option B end-of-run full-slice persist) + **defer the resume() pending-tool path** as a sub-carryover. **Pure backend**: in `_run_turns`'s `TOOL_USE` branch, mark `_tool_batch_start = len(messages)` before the `assistant tool_use` append, then persist `messages[_tool_batch_start:]` (the complete `[assistant tool_use, *tool results]` batch) via the EXISTING `_persist_to_ledger` after all results are appended (the post-tool checkpoint) — one atomic `append()` only when the round-trip is well-formed, so an early-return mid-batch (cat9/cat8 terminate) never leaves a dangling `assistant tool_use` in the ledger. NO new helper / ABC / table / event type / wire / codegen / frontend / CSS / migration; reuses `DBMessageStore.append` + `message_serde` (already round-trips `tool_calls` / `tool_call_id`). **Drive-through MANDATORY** (a tool turn whose result is NOT echoed in the final answer → a follow-up send recovers the tool result → proves the round-trip rehydrated). CHANGE-096; continuation (NOT a spike — extends the validated 57.127 `messages` ledger), so NO design note.

**Status**: Approved-to-execute (user 2026-06-16: "現在繼續執行 AD-ChatV2-Ledger-Tool-RoundTrips" → Day-0 code read confirmed the surgical gap → AskUserQuestion picked **Option A** (incremental per-turn-batch persist) + **defer resume()**).
**Branch**: `feature/sprint-57-129-chatv2-ledger-tool-roundtrips`
**Base**: `main` HEAD `858bd3af` (post-#304 — the 57.128 chat-v2 resume transcript persistence merge).
**Slice**: closes `AD-ChatV2-Ledger-Tool-RoundTrips` (carried from 57.127). A standalone backend persist-site addition (no arc).
**Scope decisions**: (a) **Option A — incremental per-turn-batch persist** in the `TOOL_USE` branch (over **Option B** end-of-run full-slice persist) — most surgical (changes confined to the `TOOL_USE` branch; no marker threading into `_run_turns`; no end_turn-site change), dangling-free, resilient (a tool-heavy run that crashes before the final answer keeps its completed tool context), and naturally EXCLUDES the verification self-correction noise (Option B would persist the failed-answer + correction-feedback messages too). (b) **Reuse the EXISTING `_persist_to_ledger` + `DBMessageStore.append` + `message_serde`** — no new helper / contract (the serde already round-trips `tool_calls` / `tool_call_id` / `name`, verified Day-0). (c) **Persist the complete batch atomically** after all tool results are appended (after the post-tool checkpoint) — never the bare `assistant tool_use` alone → no dangling-tool_call row on a partial/failed turn (the exact reason 57.127 chose the 2-point persist this far). (d) **Pure backend** — ZERO frontend / CSS / Vitest / wire / codegen / migration change (the adapter + prompt-builder already accept these Message shapes; the loop sends the same shapes WITHIN a run today). (e) The final answer is STILL persisted separately at the end_turn sites (57.127, untouched) — it is NOT in `messages` when the loop ends, so no double-persist. (f) **Defer the resume() pending-tool path** (the observation resume() appends BEFORE driving `_run_turns` is not captured by the `TOOL_USE`-branch marker) → a sub-carryover AD (niche HITL path; distinct from the SHIPPED `AD-ChatV2-Resume-Transcript-Persistence` which was the `message_events` ledger). (g) User-facing behaviour change (a follow-up now sees prior tool context) → a real UI + real backend + real LLM **drive-through is MANDATORY**.

---

## 0. Background

### The gap (the 57.127 carryover)

Sprint 57.127 built the `messages` Cat-3 ledger (`MessageStore` ABC + `DBMessageStore`) + the loop self-load on `run()`. But to de-risk dangling-tool_call rows, 57.127 persisted ONLY two points per run:
1. the **user prompt** at send start (`run()`, `loop.py:1941`, `turn_num=0`), and
2. the **final answer** at end_turn (the stop_reason terminator `loop.py:2689-2692` + the FINAL branch `loop.py:2721-2724`) — explicitly because the final answer is NOT appended to `messages` (the loop ends without it).

The **intra-turn tool round-trips** — the `assistant` message carrying `tool_calls` (`loop.py:2777`) + the `tool` result messages (`loop.py:2826` cat9-blocked / `loop.py:3051` normal) — are appended to the in-memory `messages` DURING a turn but are NEVER written to the ledger. So `load()` on a follow-up send returns `[user, final-answer, user, final-answer, ...]` with the tool interactions stripped.

### Why it matters (the missing capability)

A multi-turn follow-up that references a prior turn's tool interaction loses context: e.g. turn 1 "use the sandbox to compute the factorial of 8 but only tell me even/odd" → tool result `40320`, final answer "even"; turn 2 "what was the exact number?" → the ledger has only the user prompt + "even", NOT the tool result `40320`, so the LLM cannot recover it (it would re-compute or say it doesn't know). The tool result lives ONLY in the (unpersisted) `tool` message.

### Root cause (Day-0 code read, grep-confirmed — re-verified §checklist 0.1)

| Layer | Reality (on `main` HEAD `858bd3af`) | Anchor |
|-------|-------------------------------------|--------|
| `run()` persists the user prompt only | `await self._persist_to_ledger([messages[-1]], turn_num=0)` right after the user append | `loop.py:1937-1941` |
| end_turn persists the final answer only | both terminators persist `[Message(role="assistant", content=parsed.text)]` (NOT in `messages`) | `loop.py:2689-2692` / `:2721-2724` |
| `TOOL_USE` appends the round-trip to `messages` but NOT the ledger | `messages.append(assistant tool_use)` then per-`tool_call` `messages.append(tool result)`; NO `_persist_to_ledger` | `loop.py:2774-2783` (assistant) / `:2826-2832` (cat9-blocked) / `:3051-3057` (normal) |
| The post-tool checkpoint is the well-formed boundary | after all results are appended for the turn (the round-trip is complete) — the natural atomic-persist point | `loop.py:3059-3072` |
| `_persist_to_ledger` is the shared best-effort helper | `if self._message_store is not None and msgs: await self._message_store.append(msgs, turn_num=turn_num)` | `loop.py:1906-1913` |
| `DBMessageStore.append` already batches + is dangling-safe | one `begin_nested()` SAVEPOINT; serializes `tool_calls` / `tool_call_id` via `message_serde` | `state_mgmt/message_store.py:115-140` + `_contracts/message_serde.py:47-112` |
| The adapter + builder already accept these shapes | the loop sends `[assistant tool_use, tool result]` to `chat()` WITHIN a run every tool turn → rehydrating them is symmetric (no adapter/builder change) | `loop.py:2414-2422` (ChatRequest) |

→ The fix must **persist the complete `[assistant tool_use, *tool results]` batch** at the end of the `TOOL_USE` branch (after all results are appended), reusing `_persist_to_ledger`.

### The design (Option A — incremental per-turn-batch persist in `_run_turns`)

```
# _run_turns, TOOL_USE branch (loop.py ~2774)
# output_type == TOOL_USE
_tool_batch_start = len(messages)                 # NEW — mark before the assistant append
messages.append(Message(role="assistant", content=parsed.text, tool_calls=parsed.tool_calls))  # :2777 (existing)
for tc in parsed.tool_calls:
    ... cat9 check / execute / retry ...
    messages.append(Message(role="tool", content=..., tool_call_id=tc.id))   # :2826 / :3051 (existing)

# === Cat 7 post-tool checkpoint (existing, :3059-3072) ===
post_tool_event = await self._emit_state_checkpoint(...)
if post_tool_event is not None:
    yield post_tool_event
# NEW — persist the complete round-trip batch (atomic; only reached when well-formed)
await self._persist_to_ledger(messages[_tool_batch_start:], turn_num=turn_count)
```

**Why Option A (per-turn-batch), not Option B (end-of-run slice)**: A is the most surgical change (one marker line + one persist call, both inside the `TOOL_USE` branch — no marker threading into `_run_turns`, no end_turn-site edit). The persist point is reached ONLY after the full round-trip is appended, so every early-return path (cat9 tool-guardrail terminate `loop.py:2819-2820`, cat8 error terminate `:2926-2935` / `:2995-3004`, cancellation `:2900-2906`) skips it → the dangling `assistant tool_use` never lands in the ledger. A also persists incrementally (a tool-heavy run that crashes before the final answer keeps its completed tool turns) and EXCLUDES the verification self-correction messages (the in-loop "correct" outcome appends a failed answer + correction-feedback then `continue`s, `loop.py:2611-2620` — these are noise for cross-send rehydration; Option B's `messages[new_start:]` slice would sweep them in).

**Why no dangling rows**: the batch is persisted as ONE `append()` call (itself a `begin_nested()` SAVEPOINT in `DBMessageStore`) and only when `messages[_tool_batch_start:] == [assistant tool_use, tool_result_1, ..., tool_result_N]` is complete (every `tool_call` got a result — real, cat9-blocked, or error-synthesized; the for-loop never skips a result). On `load()`, every `assistant tool_use` therefore has its matching `tool` results → the provider never sees a `tool_use` without a `tool_result`.

**Why no double-persist of the final answer**: the final answer is persisted at the end_turn sites (57.127) and is NOT in `messages` (the loop ends without appending it) → the `TOOL_USE`-branch batch (which fires on TOOL_USE turns, before any end_turn) and the final-answer persist (which fires on the terminating turn) never overlap.

### Ground truth (Day-0 head-start — code read on `main` HEAD `858bd3af`; ALL re-verified in §checklist 0.1)

- `agent_harness/orchestrator_loop/loop.py:1906-1913` — `_persist_to_ledger(msgs, *, turn_num)` (the helper to reuse; its docstring says "never ... intra-turn tool round-trips" → MUST be updated this sprint).
- `agent_harness/orchestrator_loop/loop.py:2774-2783` — `# output_type == TOOL_USE` + the `assistant tool_use` append (where `_tool_batch_start` is set, before the append).
- `agent_harness/orchestrator_loop/loop.py:2826-2832` (cat9-blocked) / `:3051-3057` (normal) — the `tool` result appends (every `tool_call` gets exactly one).
- `agent_harness/orchestrator_loop/loop.py:3059-3072` — the post-tool checkpoint (the persist goes right AFTER `yield post_tool_event`, BEFORE the `finally:` that closes the TURN span at `:3073`).
- `agent_harness/orchestrator_loop/loop.py:2611-2620` — the verification in-loop "correct" append + `continue` (NOT in the `TOOL_USE` branch → excluded by Option A; documents why the verification noise is not persisted).
- `agent_harness/orchestrator_loop/loop.py:2819-2820` / `:2900-2906` / `:2926-2935` / `:2995-3004` — the early-return paths that skip the persist (dangling protection).
- `state_mgmt/message_store.py:115-149` — `DBMessageStore.append` (batch + SAVEPOINT + seq-from-MAX) — reused as-is.
- `_contracts/message_serde.py:47-112` — `_message_to_dict` / `_message_from_dict` round-trip `tool_calls` / `tool_call_id` / `name` — reused as-is (NO edit).
- `tests/unit/agent_harness/orchestrator_loop/test_loop_multiturn_rehydration.py` — the existing harness (`CapturingChatClient` returns canned `(text, tool_calls, stop)` triples; `FakeMessageStore` records `append`s) — EXTEND it (add an `append_calls` recorder for the atomicity assertion).
- `tests/integration/agent_harness/state_mgmt/test_message_store.py` — the 57.127 integration test ALREADY covers "round-trip incl. `tool_calls`" at the store layer → the DB serialization of a tool round-trip is proven; this sprint's NEW behaviour (the LOOP persists the batch) is unit-level.

**Baselines (57.128 closeout + #304)**: full pytest **2724+5skip** · wire **24** · Vitest **904** · mockup **51** · mypy `src` **0/372** · run_all **10/10**. Re-verify Day-0. (Note: the intermittent `test_drain_materializes_cost_ledger_parity` Risk Class C billing flake — `AD-Billing-Outbox-Drain-Test-Flake`, pre-existing, untouched — may surface once in a full run; re-run confirms.)

### STALE / drift findings (Day-0; full detail → progress.md — placeholder, filled in §checklist 0.1)

- **D-toolbatch-marker-placement** — confirm the exact lines: the `_tool_batch_start = len(messages)` goes immediately before `loop.py:2777` (the `assistant tool_use` append, under `# output_type == TOOL_USE`); the persist goes immediately after `loop.py:3072` (`yield post_tool_event`) and BEFORE the `finally:` at `:3073`.
- **D-no-other-appends-in-window** — grep `messages.append` between `:2774` and `:3057`: confirm the ONLY appends are the `assistant tool_use` (:2777) + the cat9-blocked result (:2826) + the normal result (:3051) → `messages[_tool_batch_start:]` is exactly the round-trip (no stray append).
- **D-early-return-paths** — confirm the early-return paths inside the for-loop (cat9 terminate `:2819`, cat8 terminate `:2926`/`:2995`, cancellation `:2900`) `return` BEFORE the persist → dangling protection holds.
- **D-serde-toolcalls** — re-confirm `message_serde` round-trips `tool_calls` + `tool_call_id` (so the persisted batch reloads as well-formed Messages) — verified Day-0, re-assert.
- **D-persist-helper-docstring** — `_persist_to_ledger`'s docstring currently states it is "never ... intra-turn tool round-trips" → update it (no behaviour change to the helper itself).
- **D-resume-pretool-append** — confirm resume()'s pending-tool observation is appended BEFORE driving `_run_turns` (so it is NOT captured by the `TOOL_USE`-branch marker) → documents the deferred sub-carryover scope.
- **D-baselines** — re-assert the 6 gate baselines.

## 1. Sprint Goal

Close `AD-ChatV2-Ledger-Tool-RoundTrips`: the loop now persists each turn's complete intra-turn tool round-trip (the `assistant tool_use` message + its `tool` result messages) to the `messages` Cat-3 ledger, so a follow-up send rehydrates the FULL tool context (not just `[user, final-answer]`). The fix adds ONE marker + ONE `_persist_to_ledger` call to `_run_turns`'s `TOOL_USE` branch: `_tool_batch_start = len(messages)` before the `assistant tool_use` append, then `await self._persist_to_ledger(messages[_tool_batch_start:], turn_num=turn_count)` after the post-tool checkpoint (after all results are appended) — one atomic batch, reached only when the round-trip is well-formed, so an early-return mid-batch never leaves a dangling `assistant tool_use` in the ledger. Reuses `_persist_to_ledger` + `DBMessageStore.append` + `message_serde` (no new helper / event / wire / codegen / migration). The final answer is still persisted separately at end_turn (57.127, untouched); the verification self-correction messages are intentionally excluded; the resume() pending-tool path is a deferred sub-carryover. Pure backend; ZERO frontend / CSS / Vitest / wire / codegen / migration change. Proven by unit tests (the loop persists the tool round-trip atomically as one batch; a prior tool round-trip rehydrates into the LLM request; no-tool baseline unchanged) **and a MANDATORY real UI + real backend + real LLM drive-through** (a tool turn whose result is NOT in the final answer → a follow-up send recovers the tool result). CHANGE-096; continuation (NO design note).

## 2. User Stories

- **US-1** (persist the tool round-trip): 作為 chat-v2 multi-turn，我希望 `_run_turns` 的 `TOOL_USE` 分支在 round-trip 完整後（所有 tool result append 完、post-tool checkpoint 後）把 `[assistant tool_use, *tool results]` 整批寫進 `messages` ledger，以便後續 send 看得到先前的 tool 互動。
- **US-2** (atomic + dangling-free): 作為 ledger 完整性，我希望該 batch 以單一 `_persist_to_ledger`／`append()` 原子寫入、且只在 round-trip 完整時才到達 persist 點，以便早返回（cat9/cat8 terminate、cancellation）的 partial turn 不在 ledger 留下 dangling `assistant tool_use`（無對應 `tool_result`）。
- **US-3** (no double-persist / parity): 作為持久化邏輯，我希望 final answer 仍只在 end_turn 站點持久化（57.127，不動）、verification 自我修正訊息不被寫入（Option A 自然排除），以便 ledger 是乾淨的已交付對話。
- **US-4** (docstring honesty): 作為 `_persist_to_ledger`，我希望更新其 docstring（移除「never ... intra-turn tool round-trips」），以便文件與行為一致（Karpathy §3 stale-docstring）。
- **US-5** (tests): unit 測試（擴充 `test_loop_multiturn_rehydration.py`）— (a) tool 回合後 ledger 收到 `[assistant tool_use, tool result]` + final answer；(b) 該 batch 以**單一 append call** 抵達（atomicity → dangling 防護的單元證據）；(c) 種一個含 tool round-trip 的 prior → run → 該 round-trip 出現在 LLM request[0]（rehydrate）；(d) 無 tool 的單回合 baseline 不變。
- **US-6** (drive-through — MANDATORY): 真 UI + 真後端 + 真 Azure：turn 1 用一個工具、且其結果**不在** final answer 文字裡（例如「用 sandbox 算 8! 但只告訴我奇偶」）→ turn 2（同 session）問該 tool 結果（「剛剛那個確切數字是多少？」）→ 模型答得出 `40320`（證明 tool round-trip 已 rehydrate；本 sprint 前只有「even」在 ledger，答不出數字）；逐控件 AP-4 walk + 截圖 + 實際-vs-預期 → progress.md。
- **US-7** (closeout): CHANGE-096 + 收尾（retro + calibration + navigators + **CLOSE the AD** + 記 deferred resume sub-carryover）；continuation → NO design note。

## 3. Technical Specifications

### 3.0 Architecture (1 src file EDIT: `loop.py` `_run_turns` `TOOL_USE` persist + `_persist_to_ledger` docstring; 1 test file EDIT; NO new helper / event / frontend / wire / codegen / migration)

```
# EDIT
backend/src/agent_harness/orchestrator_loop/loop.py   (EDIT): _run_turns TOOL_USE branch — set
                                            _tool_batch_start before the assistant tool_use append +
                                            persist messages[_tool_batch_start:] after the post-tool
                                            checkpoint; update _persist_to_ledger docstring
# tests
backend/tests/unit/agent_harness/orchestrator_loop/test_loop_multiturn_rehydration.py  (EDIT): add
                                            tool-round-trip persist + atomicity + rehydration tests;
                                            extend FakeMessageStore with an append_calls recorder
# docs
claudedocs/4-changes/feature-changes/CHANGE-096-chatv2-ledger-tool-roundtrips.md  (NEW)
# UNTOUCHED: message_store.py / message_serde.py (reused as-is) · end_turn final-answer persist (57.127) ·
#            frontend/** · styles-mockup.css · events.py/sse.py/codegen (wire 24) · no migration · resume() path
```

### 3.1 `_run_turns` `TOOL_USE` persist (US-1/2/3) — `loop.py`

- Under `# output_type == TOOL_USE` (`~:2774`), BEFORE the `messages.append(Message(role="assistant", ...tool_calls...))` at `:2777`: add `_tool_batch_start = len(messages)` + a WHY-comment (mark the round-trip start so the complete batch persists atomically at the branch end; AD ref).
- After the post-tool checkpoint `yield post_tool_event` (`:3072`) and BEFORE the `finally:` at `:3073`: add `await self._persist_to_ledger(messages[_tool_batch_start:], turn_num=turn_count)` + a WHY-comment (persist the complete `[assistant tool_use, *tool results]` round-trip; only reached when well-formed → dangling-free; final answer persisted separately at end_turn).
- The batch is exactly `[assistant tool_use, tool_result_1, ..., tool_result_N]` (every `tool_call` got a result; no stray append in the window — D-no-other-appends-in-window).
- Best-effort: `_persist_to_ledger` → `DBMessageStore.append` already wraps a SAVEPOINT + swallows/logs → a persist failure never breaks the turn (same guarantee as the 57.127 persists). `message_store=None` → no-op (the helper guards it).

### 3.2 `_persist_to_ledger` docstring (US-4) — `loop.py`

- Update the `:1906-1911` docstring: it currently asserts "ONLY new messages are passed (never system / prior / intra-turn tool round-trips — the final answer is the cross-send unit)". Reword to reflect that intra-turn tool round-trips ARE now passed (from the `TOOL_USE` branch, as a complete batch), alongside the user prompt (run start) + the final answer (end_turn); still never system / prior. No behaviour change to the helper.

### 3.3 Tests (US-5) — `test_loop_multiturn_rehydration.py` (EDIT)

- Extend `FakeMessageStore`: add `self.append_calls: list[list[Message]] = []` + `self.append_calls.append(list(messages))` in `append()` (additive — existing tests unaffected).
- Add a `CapturingChatClient` helper that returns a TOOL_USE response (a `ToolCall`) then a FINAL response (`StopReason.END_TURN`); register a trivial tool handler on the `ToolRegistryImpl`/`ToolExecutorImpl` so the tool executes and yields a result.
- **test_run_persists_tool_round_trip**: run a tool-then-final conversation → `store.appended` (flattened) contains the user prompt + an `assistant` message WITH `tool_calls` + a `tool` result message (`tool_call_id` set) + the final `assistant` answer; the persisted `assistant tool_use` preserves its `tool_calls`.
- **test_tool_round_trip_persisted_atomically**: assert one `store.append_calls` entry is EXACTLY `[assistant tool_use, tool result]` (the complete batch in a single call → no separate/dangling persist of the bare `assistant tool_use`).
- **test_prior_tool_round_trip_rehydrated**: seed `FakeMessageStore(prior=[user, assistant tool_use, tool result, assistant answer])` → run a new send → the LLM request[0] contains the tool round-trip messages (the `tool` result text is rehydrated alongside the new user turn).
- **test_no_tool_single_turn_unchanged** (baseline guard): the existing no-tool tests still pass (no tool round-trip persisted when the turn has no tools).
- (Dangling-on-early-return is covered by the design — the persist is after the complete batch; the atomicity test is the unit-level evidence. If a minimal cat8/cat9-terminate wiring is cheap on Day 1, add a `test_partial_tool_turn_not_persisted`; else document the design property in the module docstring.)

### 3.4 Drive-through (US-6) — real UI + real backend + real LLM (MANDATORY)

1. Clean restart (Risk Class E — only `loop.py` changed, a startup-loaded module; `Win32_Process` PID/PPID/StartTime sweep → fresh sole :8000 owner + startup log; `MAIN_TRANSCRIPT_OBSERVER` on). Vite :3007 (node) NOT stopped.
2. Pick a tenant/policy where the chosen tool **auto-approves (NO HITL pause)** — this sprint is about ledger persistence, not HITL (e.g. a permissive tenant, or a low-risk tool); document the exact tool + tenant used.
3. Turn 1 (real Azure): a prompt that calls a tool whose RESULT is NOT echoed in the final answer — e.g. "Use the python sandbox to compute the factorial of 8, but only tell me whether it's even or odd — don't state the number." → the loop does the tool round-trip (sandbox returns `40320`), the final answer says "even". Confirm via the UI / `message_events` that the tool ran.
4. **The fix**: in the SAME session, Turn 2 "What was the exact number?" → the model answers `40320` (it can only know this from the rehydrated `tool` result — the final answer never stated it). Before this sprint the ledger had only `[user, "even"]` → the model could not recover `40320`.
5. Cross-check the `messages` table (`artifacts/verify_ledger.py` via the app's `get_session_factory`): the session's ledger rows include the `assistant` (with `tool_calls`) + `tool` result rows between the user prompt and the final answer, seq monotonic. Per-control AP-4 walk; screenshots (turn1/turn2) + observed-vs-intended → progress.md. "drive-through PASS" only if Turn 2 actually recovers the tool result.

### 3.5 What is explicitly NOT done

The resume() pending-tool observation persist (appended before `_run_turns` → not captured by the `TOOL_USE` marker → deferred sub-carryover AD); persisting the verification in-loop self-correction messages (the failed-answer + correction-feedback — intentionally excluded by Option A); Option B (end-of-run full-slice persist); a new event type / wire / codegen / frontend / CSS change; touching the end_turn final-answer persist (57.127); the `message_events`/`messages` consolidation (intentional dual-ledger); ANY frontend / CSS / Vitest / migration change.

### 3.6 Validation (US-1..US-7)

Gates: mypy `src` **0/372** (re-assert) · run_all **10/10** (wire **24** unchanged — no codegen) · full pytest **2724+5skip + the new unit tests** · Vitest **904 UNCHANGED** (no FE change) · mockup **51 UNCHANGED** (`diff styles-mockup.css` empty) · `black`/`isort`/`flake8` clean · LLM-SDK-leak clean (loop.py is provider-neutral; no provider import added). Plus the §3.4 drive-through.

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `backend/src/agent_harness/orchestrator_loop/loop.py` | EDIT — `_run_turns` `TOOL_USE` branch: `_tool_batch_start = len(messages)` before the `assistant tool_use` append + `await self._persist_to_ledger(messages[_tool_batch_start:], turn_num=turn_count)` after the post-tool checkpoint; update `_persist_to_ledger` docstring |
| 2 | `backend/tests/unit/agent_harness/orchestrator_loop/test_loop_multiturn_rehydration.py` | EDIT — tool-round-trip persist + atomicity (single `append_calls` batch) + prior-tool-round-trip rehydration tests; extend `FakeMessageStore` with `append_calls` |
| 3 | `claudedocs/4-changes/feature-changes/CHANGE-096-chatv2-ledger-tool-roundtrips.md` | NEW — change record |
| — | `message_store.py` / `message_serde.py` (reused) · end_turn final-answer persist (57.127) · `frontend/**` · `styles-mockup.css` · codegen/wire · migration · resume() path | **UNTOUCHED** |

## 5. Acceptance Criteria

1. **Tool round-trip persisted**: `_run_turns`'s `TOOL_USE` branch writes the complete `[assistant tool_use, *tool results]` batch to the `messages` ledger (best-effort, `message_store=None`-safe) after all results are appended.
2. **Atomic + dangling-free**: the batch is one `_persist_to_ledger`/`append()` call, reached only when the round-trip is well-formed; an early-return mid-batch (cat9/cat8 terminate, cancellation) persists nothing for that turn → no dangling `assistant tool_use` in the ledger (unit atomicity test + design).
3. **No double-persist / parity**: the final answer is still persisted only at the end_turn sites (57.127, untouched); the verification self-correction messages are NOT persisted (Option A excludes them).
4. **Docstring honesty**: `_persist_to_ledger`'s docstring reflects that intra-turn tool round-trips are now passed.
5. **Rehydration**: a prior ledger containing a tool round-trip is loaded + prepended → the tool `assistant`/`tool` messages appear in the LLM request (test-proven).
6. **Multi-tenant** (鐵律): unchanged — `DBMessageStore` is bound to (session_id, tenant_id); the tool batch persists scoped to the same session+tenant as the user/final-answer persists (no new query path).
7. **Pure backend**: `diff styles-mockup.css` empty; Vitest 904 + mockup 51 UNCHANGED; wire 24; no codegen/migration; `message_serde.py`/`message_store.py` untouched.
8. Gates: mypy 0 · run_all 10/10 (24) · pytest 2724+5 + the new unit tests · black/isort/flake8 clean · LLM-SDK-leak clean.
9. **Drive-through PASS (MANDATORY, real UI + backend + LLM)**: turn 1 uses a tool whose result is not in the final answer → turn 2 recovers the tool result; the `messages` table shows the `assistant tool_use` + `tool` rows; screenshots + observed-vs-intended in progress.md. (NOT gate-only.)
10. `AD-ChatV2-Ledger-Tool-RoundTrips` CLOSED; the resume() pending-tool deferral logged as a sub-carryover; CHANGE-096; calibration recorded; navigators + next-phase-candidates updated.

## 6. Deliverables

- [ ] US-1 `_run_turns` `TOOL_USE` branch persists the complete `[assistant tool_use, *tool results]` batch after the post-tool checkpoint (`loop.py`)
- [ ] US-2 atomic single-`append()` batch, reached only when well-formed → dangling-free (`loop.py` + atomicity test)
- [ ] US-3 final answer still end_turn-only; verification self-correction excluded (no double/noise persist)
- [ ] US-4 `_persist_to_ledger` docstring updated (intra-turn tool round-trips now passed)
- [ ] US-5 unit tests: tool round-trip persisted / persisted atomically / prior tool round-trip rehydrated / no-tool baseline (`test_loop_multiturn_rehydration.py`)
- [ ] US-6 drive-through (tool result not in final answer → follow-up recovers it; screenshots; MANDATORY)
- [ ] US-7 CHANGE-096 + closeout (retro + calibration + navigators + CLOSE the AD + log resume sub-carryover)

## 7. Workload Calibration

- Scope class **`chatv2-ledger-tool-roundtrips-wiring` 0.55** (NEW — a pure-backend addition of ONE persist call site into `_run_turns`'s `TOOL_USE` branch, reusing the EXISTING `_persist_to_ledger` + `DBMessageStore.append` + `message_serde`: no new ABC / table / serializer / event type / wire / codegen / frontend / migration. Closest classes: `chatv2-resume-persistence-wiring` 0.55 (57.128 — also a pure-backend mirror-wiring of the existing persist into a sibling site) + lighter than `chatv2-multiturn-rehydration-spike` 0.60 (57.127, which BUILT the ABC + store + serde relocation + loop self-load). **Ceremony-floor note** (57.120/122/123/128): the CODE is tiny (~2 lines + docstring) but a full-ceremony parent-direct sprint WITH a mandatory drive-through does NOT drop below ~0.55 — and the drive-through DESIGN (a tool whose result is not echoed in the final answer + a follow-up that recovers it) is the wall-clock driver, not the code.)
- **Agent-delegated: no** (parent-direct — the persist placement, the dangling-protection reasoning (persist only after the complete batch), and the drive-through demonstration design (a result-not-in-answer tool + a recovering follow-up) are correctness-critical and best hand-authored + self-verified). `agent_factor` 1.0 → 3-segment form.
- Bottom-up est ~4.75 hr (Day-0 三-prong (mostly pre-done) + marker/early-return verify ~0.5 · the `TOOL_USE` persist + docstring ~0.75 · unit tests (persist + atomicity + rehydration + baseline) + `FakeMessageStore` recorder ~1.0 · drive-through (result-not-in-answer tool + recovering follow-up + clean restart + ledger cross-check) ~1.5 · CHANGE-096 + closeout ~1.0) → class-calibrated commit ~2.6 hr (mult 0.55). Day-4 retro Q2 verifies (`chatv2-ledger-tool-roundtrips-wiring` 1st data point; flag if the drive-through demonstration design over-runs — the main risk).

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| **Dangling `assistant tool_use`** (a `tool_use` row persisted without its `tool_result` → the provider rejects the rehydrated request) | the persist is placed AFTER the post-tool checkpoint (all results appended) and is reached only when the round-trip is well-formed; early-return paths (cat9/cat8 terminate, cancellation) `return` BEFORE it (D-early-return-paths); the atomicity unit test asserts the batch arrives as one `[assistant, tool result]` call |
| **Stray append in the marker window** (a non-round-trip message between `_tool_batch_start` and the persist → wrong slice) | D-no-other-appends-in-window greps `messages.append` in `:2774-:3057` → confirms only the assistant + cat9-blocked + normal-result appends; the verification self-correction appends are in a different branch that `continue`s earlier |
| **Double-persist of the final answer** | the final answer is NOT in `messages` (the loop ends without it) + the `TOOL_USE` batch fires on TOOL_USE turns (before any end_turn) → no overlap |
| **serde drops `tool_calls`/`tool_call_id`** (the reloaded batch is malformed) | `message_serde` round-trips `tool_calls` + `tool_call_id` + `name` (verified Day-0; the 57.127 integration test already covers "round-trip incl. tool_calls") |
| **Resume() persists the pending-tool twice / not at all** | resume() appends the pending-tool observation BEFORE driving `_run_turns` → NOT captured by the `TOOL_USE` marker → no double-persist; persisting it is DEFERRED (sub-carryover) so this sprint introduces no resume change |
| **Risk Class E** — stale `--reload` backend serves pre-edit `loop.py` during the drive-through | clean restart (`Win32_Process` PID/PPID/StartTime sweep; orphan spawn-workers on :8000); confirm fresh sole owner + startup log before trusting the UI |
| **Drive-through demonstration is ambiguous** (the final answer already contains the tool result → can't prove the round-trip rehydrated, only the answer) | DESIGN the turn-1 prompt so the tool result is NOT in the final answer (e.g. "only tell me even/odd, not the number") → turn 2 recovering the exact number is unambiguous evidence the `tool` message rehydrated |
| **HITL pause accidentally triggers** (the chosen tool escalates under the tenant policy → a pause, not the clean round-trip we want) | pick a tenant/policy where the tool auto-approves (NO pause); document the exact tool + tenant; if a pause fires, switch tool/tenant (this sprint is NOT about HITL) |
| **Pre-existing billing flake** (`AD-Billing-Outbox-Drain-Test-Flake`) may surface once in the full run | re-run confirms 2724+5 (do NOT skip the test); the new tests are unrelated |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- **The resume() pending-tool observation persist** — deferred sub-carryover (niche HITL path; distinct from the SHIPPED `AD-ChatV2-Resume-Transcript-Persistence` `message_events` work).
- **Persisting the verification in-loop self-correction messages** — intentionally excluded by Option A (noise for cross-send rehydration).
- **Option B (end-of-run full-slice persist)** — rejected by the user in favour of Option A.
- **Touching the end_turn final-answer persist** (57.127) — unchanged.
- **`message_events`/`messages` consolidation** — the dual-ledger is intentional (different consumers); a future canonical-ledger AD.
- **`turn_num` cross-send counter** (cosmetic — ordering is via `sequence_num`) — carried.
- **ANY frontend / CSS / Vitest / wire / codegen / migration change** (pure backend; the adapter + builder already accept these Message shapes).
