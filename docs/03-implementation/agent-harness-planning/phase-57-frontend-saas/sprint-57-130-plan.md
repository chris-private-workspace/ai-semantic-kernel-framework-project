# Sprint 57.130 Plan — chat-v2 LoopTerminated wire surface (wire the server-side-only `LoopTerminated` Cat-8 event to the chat-v2 SSE stream + render a terminal state + clear the stuck pending tool chip). Closes `AD-LoopTerminated-Wire-Surface` — the 57.110 carryover: a FATAL-terminated run (`fail_fast` / rate-limit / circuit-open / max-retries / budget / fatal-exception via the Cat-8 ErrorTerminator) ends by `yield`ing `LoopTerminated`, but `serialize_loop_event` has no branch for it → it falls through to `NotImplementedError` → the router silently drops it (`logger.debug("sse: skip ...")`). Symptom: the SSE stream just ENDS with no terminal frame → the chat-v2 UI shows a **stuck pending tool chip** (the prior `tool_call_request` never gets a `tool_call_result`) + the turn silently stops with no reason shown to the user (an AP-4 broken-UX on the 主流量 — any fatal error hits it). **Cross-stack thin slice**: add `LoopTerminated` to the SSE serializer + the `WIRE_SCHEMA` registry (24→25 — a NEW wire event type) → codegen regenerates the FE types → `mergeEvent` gains a `loop_terminated` case that flips any dangling pending `ToolBlock` to `error` (reason as output), surfaces a turn-level "terminated · {reason}" indicator, and sets the turn terminal so the composer unfreezes. **Minimal render**: reuse the EXISTING danger tokens (`var(--danger)`) + the established inline-chip pattern (mirrors the `awaiting approval` chip in `AgentTurn` + the `VerificationBlock.failed` danger semantic) — NO new CSS class, NO mockup authoring, NO new `oklch(`/`#hex` literal (`HEX_OKLCH_BASELINE` 51 unchanged). **Drive-through MANDATORY** (stage a REAL fatal termination — a tool that exhausts retries / a budget cap → `LoopTerminated` → the UI shows the terminated reason + the pending chip clears, instead of hanging). CHANGE-097; a cross-stack wire-surfacing fix (NOT a spike — surfaces an existing Cat-8 event), so NO design note.

**Status**: Approved-to-execute (user 2026-06-16: "執行 🟡 C. chat-v2 收尾 / carryovers" → AskUserQuestion picked **LoopTerminated wire surface**). 2 read-only Explore recon passes mapped the backend SSE/event path + the frontend store/render with file:line anchors (the Day-0 三-prong head-start; re-verified in §checklist 0.1).
**Branch**: `feature/sprint-57-130-chatv2-loop-terminated-wire-surface`
**Base**: `main` HEAD `b9334946` (post-#306 — the 57.129 PR-pending→MERGED status flip).
**Slice**: closes `AD-LoopTerminated-Wire-Surface` (carried from 57.110). A standalone cross-stack wire-surfacing fix (no arc).
**Scope decisions**: (a) **Wire the EXISTING `LoopTerminated` event** (defined `events.py:297`, emitted `loop.py:2939`/`:3008`) — no backend logic change; only add it to the SSE serializer (`sse.py`) + the `WIRE_SCHEMA` registry + run codegen. (b) **24→25 wire events** (a NEW wire event type) — bump the parity test + move `LoopTerminated` UNWIRED→WIRED. (c) **Minimal FE render, NO new mockup CSS** — flip the dangling pending `ToolBlock` to `status:"error"` (reuses the existing `.badge.danger` tone — the direct stuck-chip fix) + a turn-level inline "terminated · {reason}" chip using `var(--danger)` (mirrors the `awaiting approval` chip / `VerificationBlock.failed` precedent) + set the turn terminal so the composer unfreezes. ZERO new CSS class / `styles-mockup.css` edit / mockup authoring / `oklch(`/`#hex` literal (a richer mockup-authored `TerminatedBlock` is a deferred follow-on). (d) **codegen regenerates** `loopEvents.generated.ts` (the FE types + `KNOWN_LOOP_EVENT_TYPES`) — the only "generated" touch; `check_event_schema_sync` verifies sync. (e) User-facing behaviour change (a fatal error now shows a reason + clears the stuck chip instead of hanging) → a real UI + real backend + real LLM **drive-through is MANDATORY** (stage a real fatal termination). (f) Mirror the closest wired fatal-termination precedent `tripwire_triggered {violation_type, detail}` for the wire shape.

---

## 0. Background

### The gap (the 57.110 carryover `AD-LoopTerminated-Wire-Surface`)

The Cat-8 ErrorTerminator path ends a run by `yield`ing a `LoopTerminated` event (NOT a normal `loop_end`). But that event was never added to the chat-v2 SSE wire, so the frontend never receives it. When a fatal termination happens **mid-tool** (a `tool_call_request` was already streamed, then the tool fatally errors), the SSE stream simply ENDS — no `tool_call_result`, no `loop_end`, no terminal frame. The result on the 主流量:
1. **Stuck pending tool chip** — the `ToolBlock` stays `status:"pending"` forever (only a `tool_call_result` clears it; it never arrives).
2. **Silent stop with no reason** — the user sees the turn just stop; the termination reason (`budget_exceeded` / `circuit_open` / `fatal_exception` / `max_retries_exhausted`) is server-side-only.

This is an AP-4 Potemkin-class broken-UX sitting on the main chat flow (any fatal error reaches it), invisible to every gate (the backend "works", the API "responds" with a clean stream end).

### Why it matters (the missing capability)

A user whose run hits a fatal error (a tool that keeps failing → `max_retries_exhausted`, a token budget cap → `budget_exceeded`, an open circuit breaker) gets a frozen UI: a spinner that never resolves + a composer that may stay disabled. They cannot tell whether it's still working, broke, or what to do. Surfacing `LoopTerminated` gives them a clear terminal state + the reason, and unfreezes the UI.

### Root cause (recon code read, file:line; ALL re-verified §checklist 0.1)

| Layer | Reality (on `main` HEAD `b9334946`) | Anchor |
|-------|-------------------------------------|--------|
| `LoopTerminated` is a defined `LoopEvent` | `@dataclass(frozen=True) class LoopTerminated(LoopEvent): reason: str; detail: str \| None; last_state_version: int \| None` | `agent_harness/_contracts/events.py:297-309` |
| It IS emitted (2 sites) then `return`s | both in the tool-error path: hard exception + soft `result.success=False` → `yield LoopTerminated(reason=term_reason.value, detail=term_detail, ...)` then `return` | `loop.py:2939` (hard) / `:3008` (soft) |
| The SSE serializer has NO branch for it | `serialize_loop_event` (23 isinstance branches) ends with `raise NotImplementedError(...)` — `LoopTerminated` falls through | `api/v1/chat/sse.py:481-484` |
| The router silently drops it | `try: payload = serialize_loop_event(event) except NotImplementedError: logger.debug("sse: skip unserialized event %s", ...); continue` | `api/v1/chat/router.py:747-751` |
| The wire registry has 24 entries | `WIRE_SCHEMA` dict (ordered) — `loop_terminated` is ABSENT | `api/v1/chat/event_wire_schema.py:80-229` |
| The parity test asserts 24 + lists it UNWIRED | `assert len(WIRE_SCHEMA) == 24`; `LoopTerminated` is in `UNWIRED_EVENT_INSTANCES` | `tests/unit/api/v1/chat/test_event_wire_schema_parity.py:144-145` (count) / `:138` (UNWIRED) / `:68` (WIRED list) |
| Closest wired fatal-terminate precedent | `tripwire_triggered: {violation_type, detail}` (Cat 9 severe-violation terminate) | `sse.py:~300-306` |
| FE codegen output (DO NOT EDIT) | `loopEvents.generated.ts` — discriminated union + `KNOWN_LOOP_EVENT_TYPES`; produced by `scripts/codegen/generate_event_schemas.py` from `WIRE_SCHEMA` | `frontend/src/features/chat_v2/generated/loopEvents.generated.ts` |
| FE merge reducer; unknown type → no crash | `mergeEvent(ev)` exhaustive `switch (ev.type)`; `default` preserves in `rawEvents`, no throw | `frontend/src/features/chat_v2/store/chatStore.ts:422-1037` (default `:1031-1035`) |
| The stuck chip = pending `ToolBlock` | `ToolBlock` renders `status:"pending"` while `output===null`; only `tool_call_result` (`chatStore.ts:625-644`) flips it to `ok`/`error` | `components/blocks/ToolBlock.tsx:54-94` + `chatStore.ts:625-644` |
| Stream-end fallback unfreezes but leaves pending | `useLoopEventStream.ts:94-96` force-sets `status:"completed"` on stream-end without `loop_end`, BUT pending tools stay pending | `hooks/useLoopEventStream.ts:94-96` |
| Danger render precedent | `VerificationBlock.failed` (`.block.verification.failed`, danger-tinted, `var(--danger)` inline) + `AgentTurn` `awaiting approval` inline chip (`var(--warning)`) | `components/blocks/VerificationBlock.tsx:46-50` + `components/turns/AgentTurn.tsx:66-72` |

→ The fix must (1) **serialize `LoopTerminated`** + add it to `WIRE_SCHEMA` (24→25) + regenerate the FE types, and (2) **handle `loop_terminated` in `mergeEvent`** — flip the dangling pending `ToolBlock` to `error`, surface a turn-level terminated indicator with the reason, set the turn terminal.

### The design (cross-stack: 1 serializer branch + 1 wire entry + codegen + 1 merge case + 1 turn-render)

```
# BACKEND — sse.py serialize_loop_event (before the final NotImplementedError, mirror tripwire_triggered)
if isinstance(event, LoopTerminated):
    return {"type": "loop_terminated",
            "data": {"reason": event.reason, "detail": event.detail,
                     "last_state_version": event.last_state_version}}

# BACKEND — event_wire_schema.py WIRE_SCHEMA (append the 25th entry)
"loop_terminated": {"reason": "string", "detail": "string | null", "last_state_version": "number | null"},

# → run: python scripts/codegen/generate_event_schemas.py  (regenerates loopEvents.generated.ts + KNOWN_LOOP_EVENT_TYPES)

# FRONTEND — chatStore.ts mergeEvent (new case)
case "loop_terminated": {
    // flip any dangling pending ToolBlock in the active turn → error (reason as output) — the stuck-chip fix
    // set turn.terminated = { reason, detail } + turn terminal (status "completed") so the composer unfreezes
    // preserve rawEvents (audit trail)
}

# FRONTEND — AgentTurn.tsx: when turn.terminated, render an inline "⚠ terminated · {reason}" chip (var(--danger),
#            mirrors the awaiting-approval chip) — NO new CSS class, NO new oklch literal
```

**Why minimal render (no new `TerminatedBlock`/CSS)**: the two user-visible symptoms — the stuck pending chip + the silent stop — are both fixable with EXISTING primitives: flip the pending `ToolBlock` to `error` (its `.badge.danger` tone already exists) and add a turn-level inline danger chip (`var(--danger)`, mirroring the `awaiting approval`/`VerificationBlock.failed` precedent). This keeps `styles-mockup.css` byte-identical (mockup 51 unchanged), adds zero `oklch(`/`#hex` literals (`HEX_OKLCH_BASELINE` 51 unchanged), and authors no new mockup element. A richer mockup-authored `TerminatedBlock` (the Explore-recommended Option 2) is a deferred follow-on AD (it would trip the `mockup-author-and-port` ceremony + a baseline bump for marginal gain over the minimal danger chip).

**Why `LoopTerminated` carries the fix for ALL fatal paths**: the event carries the `reason` regardless of cause (tool error, budget, circuit, retries), so wiring it surfaces every Cat-8 fatal termination. The pending-chip flip applies when a tool was mid-flight; when there is no pending tool, the turn-level terminated chip still surfaces the reason (better than a silent end).

### Ground truth (recon head-start — code read on `main` HEAD `b9334946`; ALL re-verified §checklist 0.1)

- `agent_harness/_contracts/events.py:297-309` — `LoopTerminated(LoopEvent)` (`reason` / `detail` / `last_state_version`).
- `agent_harness/orchestrator_loop/loop.py:2939` (hard) / `:3008` (soft) — the 2 `yield LoopTerminated(...)` + `return` sites (re-grep `LoopTerminated(` Day-0 to confirm no 3rd site).
- `api/v1/chat/sse.py:~300-306` — the `tripwire_triggered` branch (the wire-shape precedent to mirror) + `:481-484` — the `NotImplementedError` (the new branch goes just before it).
- `api/v1/chat/event_wire_schema.py:80-229` — `WIRE_SCHEMA` (append `loop_terminated`).
- `api/v1/chat/router.py:747-751` — the silent-drop `except NotImplementedError` (once serialized, the event flows; no router edit needed).
- `tests/unit/api/v1/chat/test_event_wire_schema_parity.py:68` (WIRED list) / `:138` (UNWIRED list) / `:144-145` (`== 24`) — move `LoopTerminated` UNWIRED→WIRED + bump 24→25.
- `scripts/codegen/generate_event_schemas.py` — run after the `WIRE_SCHEMA` edit (regenerates `loopEvents.generated.ts`); `scripts/lint/check_event_schema_sync.py` (via `run_all.py`) verifies sync.
- `frontend/src/features/chat_v2/store/chatStore.ts:422-1037` — `mergeEvent` (add `case "loop_terminated"`; `loop_end` at `:646` + `tool_call_result` at `:625-644` are the shape precedents).
- `frontend/src/features/chat_v2/types.ts:~129-134` — the Turn/Block types (add a `terminated?: {reason; detail}` field to `AgentTurn`).
- `frontend/src/features/chat_v2/components/turns/AgentTurn.tsx:66-72` — the inline `awaiting approval` chip (mirror for the terminated chip).
- `frontend/src/features/chat_v2/components/blocks/ToolBlock.tsx:54-94` — the pending/ok/error status tones (the pending→error flip reuses these).
- `frontend/tests/unit/chat_v2/chatStore.mergeEvent.test.ts` — the merge-reducer test harness (add `loop_terminated` cases).
- `frontend/scripts/check-mockup-fidelity.mjs` — `HEX_OKLCH_BASELINE = 51` (must stay 51 — no new literal).

**Baselines (57.129 closeout + #305/#306)**: full pytest **2727+5skip** · wire **24** → **25** this sprint · Vitest **904** · mockup **51** · mypy `src` **0/372** · run_all **10/10**. Re-verify Day-0. (The intermittent `AD-Billing-Outbox-Drain-Test-Flake` Risk Class C billing flake — pre-existing, untouched — may surface once; re-run confirms.)

### STALE / drift findings (Day-0; full detail → progress.md — placeholder, filled in §checklist 0.1)

- **D-loopterminated-emission-sites** — re-grep `LoopTerminated(` across `backend/src`: confirm the emission sites are `loop.py:2939` + `:3008` (and whether any other path emits it) → confirms what the drive-through must trigger.
- **D-serializer-precedent-shape** — confirm the `tripwire_triggered` branch shape in `sse.py` (the `{type, data:{...}}` envelope) so the new `loop_terminated` branch mirrors it exactly.
- **D-wire-count-24-vs-fe-union** — recon reported backend `WIRE_SCHEMA == 24` but the FE generated union at ~23; re-count BOTH (`len(WIRE_SCHEMA)` + the generated union members) to resolve the discrepancy BEFORE editing (the codegen should make them equal; canonical = 24). Confirm the codegen is the sole writer of `loopEvents.generated.ts`.
- **D-codegen-invocation** — confirm the exact codegen command + that `check_event_schema_sync` is in `run_all.py` (so the regen is gate-verified).
- **D-mergeEvent-default-noncrash** — confirm `mergeEvent`'s `default` case preserves unknown events without throwing (so the pre-codegen / pre-case state is safe) + the exact `loop_end`/`tool_call_result` case shapes to mirror.
- **D-pending-toolblock-identify** — confirm how a pending `ToolBlock` is found in the active turn (by `status:"pending"` / `output===null`) so the flip targets the right block(s).
- **D-mockup-fidelity-zero-delta** — confirm the terminated chip can reuse `var(--danger)` inline with NO new CSS class / NO `styles-mockup.css` edit / NO new `oklch(`/`#hex` (HEX_OKLCH_BASELINE 51 stays).
- **D-drive-through-trigger** — identify the CHEAPEST reliable way to force a `LoopTerminated` in a real run (a tool that always errors → `max_retries_exhausted`; or a tiny token budget → `budget_exceeded`; or a forced circuit-open) — the main drive-through-setup risk.
- **D-baselines** — re-assert the 6 gate baselines (note wire 24→25 this sprint).

## 1. Sprint Goal

Close `AD-LoopTerminated-Wire-Surface`: a FATAL-terminated chat-v2 run now surfaces its `LoopTerminated` event to the UI instead of silently ending. Backend — add a `LoopTerminated` branch to `serialize_loop_event` (mirroring `tripwire_triggered`) + a `loop_terminated` entry to `WIRE_SCHEMA` (24→25 — a NEW wire event type), then run the codegen so `loopEvents.generated.ts` + `KNOWN_LOOP_EVENT_TYPES` regenerate; bump the parity test (24→25) + move `LoopTerminated` UNWIRED→WIRED. Frontend — `mergeEvent` gains a `loop_terminated` case that (a) flips any dangling pending `ToolBlock` in the active turn to `error` (the reason as its output — the direct stuck-chip fix), (b) records a turn-level `terminated:{reason, detail}` indicator rendered as an inline "⚠ terminated · {reason}" chip on the `AgentTurn` (reusing `var(--danger)` + the established inline-chip pattern — NO new CSS class, NO mockup authoring, NO new `oklch(`/`#hex` literal), and (c) sets the turn terminal so the composer unfreezes. Proven by backend wire-parity + serializer tests, FE `mergeEvent` Vitest cases (pending-tool flip + terminated indicator + status terminal + `rawEvents` preserved), **and a MANDATORY real UI + real backend + real LLM drive-through** (stage a REAL fatal termination → the UI shows the terminated reason + the pending chip clears, instead of hanging). `styles-mockup.css` byte-identical (mockup 51 unchanged); `HEX_OKLCH_BASELINE` 51 unchanged. CHANGE-097; cross-stack wire-surfacing (NO design note).

## 2. User Stories

- **US-1** (serialize the event): 作為 chat-v2 SSE，我希望 `serialize_loop_event` 為 `LoopTerminated` 產生 `{type:"loop_terminated", data:{reason, detail, last_state_version}}`（鏡像 `tripwire_triggered`），以便 router 不再把它 `NotImplementedError`-drop。
- **US-2** (wire registry 24→25 + codegen): 作為 wire schema，我希望 `WIRE_SCHEMA` 新增 `loop_terminated` 條目、parity test 由 `==24` 改 `==25`、`LoopTerminated` 從 UNWIRED 移到 WIRED、並重跑 codegen 讓 `loopEvents.generated.ts` + `KNOWN_LOOP_EVENT_TYPES` 同步（`check_event_schema_sync` 綠）。
- **US-3** (stuck-chip fix): 作為 chat-v2 UI，我希望 `mergeEvent` 的 `loop_terminated` case 把 active turn 中仍 `pending` 的 `ToolBlock` 翻成 `error`（reason 當 output），以便 fatal terminate mid-tool 後不再有永久轉圈的 pending chip。
- **US-4** (terminal surface + unfreeze): 作為使用者，我希望 turn 顯示「⚠ terminated · {reason}」inline 指示（`var(--danger)`，復用既有 inline-chip 樣式，無新 CSS class）並把 turn 設為 terminal 讓 composer 解凍，以便 fatal error 不再是無聲停止。
- **US-5** (tests): backend — serializer 對 `LoopTerminated` 回傳正確 payload + wire-parity（25 條、`LoopTerminated` 在 WIRED）；frontend — `mergeEvent` Vitest：(a) `loop_terminated` 把 pending ToolBlock 翻 error；(b) 設 `turn.terminated={reason,detail}` + status terminal；(c) `rawEvents` 保留；(d) 無 pending tool 時仍記錄 terminated（不 crash）。
- **US-6** (drive-through — MANDATORY): 真 UI + 真後端 + 真 Azure — 製造一個 REAL fatal termination（最便宜可靠的觸發，Day-0 決定：always-error tool → `max_retries_exhausted` / 極小 token budget → `budget_exceeded` / 強制 circuit-open）→ 確認 UI 顯示 terminated reason + pending chip 清除（不再 hang）+ composer 解凍；逐控件 AP-4 walk + 截圖 + 實際-vs-預期 → progress.md。
- **US-7** (closeout): CHANGE-097 + 收尾（retro + calibration + navigators + **CLOSE the AD**）；cross-stack wire-surfacing → NO design note。

## 3. Technical Specifications

### 3.0 Architecture (backend: 1 serializer branch + 1 wire entry + codegen regen + parity test; frontend: 1 merge case + 1 turn field + 1 turn-render + tests; NO new CSS class / mockup edit / migration)

```
# BACKEND (EDIT)
backend/src/api/v1/chat/sse.py                 (EDIT): add LoopTerminated branch to serialize_loop_event
backend/src/api/v1/chat/event_wire_schema.py   (EDIT): append "loop_terminated" entry (24→25)
backend/tests/unit/api/v1/chat/test_event_wire_schema_parity.py  (EDIT): == 24 → == 25; LoopTerminated UNWIRED→WIRED
# BACKEND (GENERATED — via codegen, do not hand-edit)
frontend/src/features/chat_v2/generated/loopEvents.generated.ts  (REGEN): python scripts/codegen/generate_event_schemas.py
# FRONTEND (EDIT)
frontend/src/features/chat_v2/store/chatStore.ts       (EDIT): add case "loop_terminated" (pending-tool flip + terminated field + terminal)
frontend/src/features/chat_v2/types.ts                 (EDIT): add terminated?: {reason; detail} to AgentTurn
frontend/src/features/chat_v2/components/turns/AgentTurn.tsx  (EDIT): render inline "terminated · {reason}" chip (var(--danger))
frontend/tests/unit/chat_v2/chatStore.mergeEvent.test.ts  (EDIT): loop_terminated merge cases
# docs
claudedocs/4-changes/feature-changes/CHANGE-097-chatv2-loop-terminated-wire-surface.md  (NEW)
# UNTOUCHED: loop.py (LoopTerminated already emitted) · events.py · router.py (silent-drop self-heals once serialized) ·
#            styles-mockup.css (byte-identical) · reference/design-mockups/** · no migration · no new CSS class
```

### 3.1 Serialize `LoopTerminated` (US-1) — `sse.py`

- In `serialize_loop_event` (the `_serialize_inner` isinstance chain), BEFORE the final `raise NotImplementedError` (`:481`): add `if isinstance(event, LoopTerminated): return {"type": "loop_terminated", "data": {"reason": event.reason, "detail": event.detail, "last_state_version": event.last_state_version}}` + a WHY-comment (surface the Cat-8 fatal terminate; mirror `tripwire_triggered`; AD ref). Import `LoopTerminated` if not already imported.
- Mirror the `tripwire_triggered` envelope exactly (`{type, data:{...}}`); `detail`/`last_state_version` may be `None` → serialize as JSON `null` (the FE type marks them optional/nullable).

### 3.2 Wire registry 24→25 + codegen (US-2) — `event_wire_schema.py` + parity test + codegen

- Append to `WIRE_SCHEMA` (after the last entry, preserving order): `"loop_terminated": {"reason": "string", "detail": "string | null", "last_state_version": "number | null"}`.
- `test_event_wire_schema_parity.py`: change `assert len(WIRE_SCHEMA) == 24` → `== 25`; remove `LoopTerminated` from `UNWIRED_EVENT_INSTANCES` (`:138`); add a `LoopTerminated(reason="fatal_exception", detail="...")` instance to `WIRED_EVENT_INSTANCES` (`:68`).
- Run `python scripts/codegen/generate_event_schemas.py` → `loopEvents.generated.ts` gains `LoopTerminatedEvent` + `"loop_terminated"` in `KNOWN_LOOP_EVENT_TYPES`. Do NOT hand-edit the generated file. `run_all.py`'s `check_event_schema_sync` must be green (FE generated == backend wire).

### 3.3 `mergeEvent` `loop_terminated` case (US-3/4) — `chatStore.ts` + `types.ts`

- `types.ts`: add `terminated?: { reason: string; detail?: string | null }` to the `AgentTurn` type (optional → existing turns unaffected).
- `chatStore.ts` `mergeEvent`: add `case "loop_terminated"`:
  - find the active `AgentTurn`'s blocks; for each `ToolBlock` with `status === "pending"` (output null), flip to `status:"error"` with `output` = a short "terminated: {reason}" (the direct stuck-chip fix — reuses the existing error tone).
  - set `turn.terminated = { reason: ev.data.reason, detail: ev.data.detail }` + set the turn terminal (status `"completed"` — consistent with the `useLoopEventStream` stream-end fallback so the composer unfreezes; do NOT introduce a new status enum value this slice).
  - preserve `rawEvents` (push the event — same as other cases).
- Mirror the `loop_end` (`:646`) + `tool_call_result` (`:625-644`) case shapes (immutable turn/block update pattern).

### 3.4 Terminated chip render (US-4) — `AgentTurn.tsx`

- When `turn.terminated` is set, render an inline chip mirroring the `awaiting approval` chip (`:66-72`): a `<AlertTriangle size={13}/>` (or the existing danger icon) + mono text `terminated · {reason}` with `color: var(--danger)`, `fontSize: 11` — inline-style with the STYLE.md §3 `eslint-disable-next-line no-restricted-syntax` escape comment (same as the existing waiting chip). NO new CSS class, NO `styles-mockup.css` edit, NO new `oklch(`/`#hex` literal.
- The `{detail}` (if present) may render in a `.subtle` mono line below (mirroring `VerificationBlock`'s evidence row) — optional; reason alone is sufficient for the fix.

### 3.5 Tests (US-5)

- **Backend** (`test_event_wire_schema_parity.py` EDIT): the parity suite now asserts 25 entries + `LoopTerminated` is WIRED; add/confirm a serializer assertion that `serialize_loop_event(LoopTerminated(reason="max_retries_exhausted", detail="...", last_state_version=3))` returns `{"type":"loop_terminated","data":{"reason":"max_retries_exhausted","detail":"...","last_state_version":3}}` (mirror the existing per-event serializer tests in the chat sse test module — Day-0 locate the serializer test file).
- **Frontend** (`chatStore.mergeEvent.test.ts` EDIT): add cases — (a) a turn with a pending `ToolBlock` + a `loop_terminated` event → the `ToolBlock` is `error` (no longer pending); (b) `turn.terminated == {reason, detail}` + the turn status is terminal; (c) `rawEvents` contains the event; (d) a `loop_terminated` with no pending tool → records `terminated` + terminal, no crash. Reuse the existing fixtures (`turnStart`/`toolReq`/`llmResponse`).

### 3.6 Drive-through (US-6) — real UI + real backend + real LLM (MANDATORY)

1. Clean restart (Risk Class E — `loop.py` UNCHANGED this sprint, but `sse.py`/`event_wire_schema.py` are startup-loaded; `Win32_Process` PID/PPID/StartTime sweep → fresh sole :8000 owner + startup log; `MAIN_TRANSCRIPT_OBSERVER` on). Vite :3007 (node) NOT stopped. Rebuild the FE if the dev server doesn't pick up the regenerated types.
2. **Stage a REAL fatal termination** (Day-0 D-drive-through-trigger picks the cheapest reliable one):
   - preferred: a tool that ALWAYS errors → the Cat-8 error handler exhausts retries → `LoopTerminated(reason="max_retries_exhausted")`; OR
   - a tiny per-run token budget → `LoopTerminated(reason="budget_exceeded")`; OR
   - a forced circuit-open.
   Drive turn 1 with a prompt that calls that tool (real Azure) so the loop reaches the terminate.
3. **The fix**: confirm in the real UI that — (a) the previously-pending tool chip flips to an error/terminated state (no longer a perpetual spinner), (b) a "terminated · {reason}" indicator appears with the real reason, (c) the composer is re-enabled (turn no longer "running"). Capture the SSE frames (`browser_network_requests` / response body) showing the `loop_terminated` frame arrived.
4. Per-control AP-4 walk; screenshots (the hung-before mental model vs the terminated-after) + observed-vs-intended → progress.md. "drive-through PASS" only if the UI actually shows the terminated reason + the pending chip clears (NOT gate-only).

### 3.7 What is explicitly NOT done

A richer mockup-authored `TerminatedBlock` component + `.block.terminated` CSS (deferred follow-on — the minimal danger chip + ToolBlock error flip is the real fix); any change to `loop.py`/the `LoopTerminated` emission logic (the event already fires correctly); a new loop/turn `status` enum value ("terminated") — reuse "completed" so the composer unfreezes without touching every status check; retroactively terminating pending tools on a NORMAL stream-end without `loop_end` (a separate edge case — `useLoopEventStream` already force-completes; this slice handles the explicit `loop_terminated` signal); the resume-path terminate surfacing (out of scope); ANY migration / new backend primitive.

### 3.8 Validation (US-1..US-7)

Gates: mypy `src` **0/372** (re-assert) · run_all **10/10** (**wire 25** — `check_event_schema_sync` green after codegen) · full pytest **2727+5skip + the new parity/serializer assertions** · Vitest **904 + the new `mergeEvent` cases** · mockup **51 UNCHANGED** (`diff styles-mockup.css` empty; `check:mockup-fidelity` `HEX_OKLCH_BASELINE` 51) · `black`/`isort`/`flake8` clean · `npm run lint && npm run build` (NO `--silent`) · LLM-SDK-leak clean. Plus the §3.6 drive-through.

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `backend/src/api/v1/chat/sse.py` | EDIT — add `LoopTerminated` branch to `serialize_loop_event` (mirror `tripwire_triggered`) |
| 2 | `backend/src/api/v1/chat/event_wire_schema.py` | EDIT — append `"loop_terminated"` entry (24→25) |
| 3 | `backend/tests/unit/api/v1/chat/test_event_wire_schema_parity.py` | EDIT — `== 24`→`== 25`; `LoopTerminated` UNWIRED→WIRED (+ serializer assertion) |
| 4 | `frontend/src/features/chat_v2/generated/loopEvents.generated.ts` | REGEN (codegen) — `LoopTerminatedEvent` + `KNOWN_LOOP_EVENT_TYPES` |
| 5 | `frontend/src/features/chat_v2/store/chatStore.ts` | EDIT — `case "loop_terminated"`: pending-tool flip + `terminated` field + terminal |
| 6 | `frontend/src/features/chat_v2/types.ts` | EDIT — add `terminated?: {reason; detail}` to `AgentTurn` |
| 7 | `frontend/src/features/chat_v2/components/turns/AgentTurn.tsx` | EDIT — render inline "terminated · {reason}" chip (`var(--danger)`) |
| 8 | `frontend/tests/unit/chat_v2/chatStore.mergeEvent.test.ts` | EDIT — `loop_terminated` merge cases |
| 9 | `claudedocs/4-changes/feature-changes/CHANGE-097-chatv2-loop-terminated-wire-surface.md` | NEW — change record |
| — | `loop.py` / `events.py` (`LoopTerminated` already emitted) · `router.py` (self-heals once serialized) · `styles-mockup.css` · `reference/design-mockups/**` · migration · new CSS class | **UNTOUCHED** |

## 5. Acceptance Criteria

1. **Serialized**: `serialize_loop_event(LoopTerminated(...))` returns `{"type":"loop_terminated","data":{reason, detail, last_state_version}}`; the router no longer drops it.
2. **Wire 24→25**: `WIRE_SCHEMA` has 25 entries incl. `loop_terminated`; parity test asserts 25; `LoopTerminated` is WIRED; codegen regenerated `loopEvents.generated.ts` (+ `KNOWN_LOOP_EVENT_TYPES`); `check_event_schema_sync` green.
3. **Stuck-chip fix**: a `loop_terminated` event flips the active turn's dangling pending `ToolBlock`(s) to `error` (no perpetual spinner).
4. **Terminal surface + unfreeze**: the turn records `terminated:{reason, detail}`, renders the inline danger chip, and is set terminal so the composer re-enables.
5. **Mockup fidelity**: `diff styles-mockup.css` empty; `HEX_OKLCH_BASELINE` 51 unchanged; mockup 51 unchanged; no new CSS class / `oklch(`/`#hex` literal.
6. **No-crash robustness**: `mergeEvent` handles `loop_terminated` with or without a pending tool; `rawEvents` preserved.
7. Gates: mypy 0 · run_all 10/10 (**25**) · pytest 2727+5 + new assertions · Vitest 904 + new cases · `npm run build` clean · black/isort/flake8 clean · LLM-SDK-leak clean.
8. **Drive-through PASS (MANDATORY, real UI + backend + LLM)**: a staged real fatal termination → the UI shows the terminated reason + the pending chip clears + the composer unfreezes; SSE `loop_terminated` frame captured; screenshots + observed-vs-intended in progress.md. (NOT gate-only.)
9. `AD-LoopTerminated-Wire-Surface` CLOSED; CHANGE-097; calibration recorded; navigators + next-phase-candidates updated.

## 6. Deliverables

- [ ] US-1 `serialize_loop_event` `LoopTerminated` branch (`sse.py`)
- [ ] US-2 `WIRE_SCHEMA` +`loop_terminated` (24→25) + parity test 25 + UNWIRED→WIRED + codegen regen (`loopEvents.generated.ts`)
- [ ] US-3 `mergeEvent` `loop_terminated`: flip dangling pending `ToolBlock` → error (stuck-chip fix)
- [ ] US-4 turn `terminated` field + inline danger chip (`AgentTurn.tsx`, `var(--danger)`, no new CSS) + turn terminal (unfreeze)
- [ ] US-5 tests: backend serializer + wire-parity 25; FE `mergeEvent` (pending flip / terminated indicator / terminal / rawEvents / no-pending no-crash)
- [ ] US-6 drive-through (staged real fatal terminate → UI shows reason + chip clears + composer unfreezes; screenshots; MANDATORY)
- [ ] US-7 CHANGE-097 + closeout (retro + calibration + navigators + CLOSE the AD)

## 7. Workload Calibration

- Scope class **`chatv2-fatal-terminate-wire-surface` 0.55** (NEW — a cross-stack surfacing of an ALREADY-emitted-but-unwired backend event: 1 serializer branch + 1 `WIRE_SCHEMA` entry (a NEW wire type, 24→25) + codegen regen + 1 `mergeEvent` case + 1 turn field + 1 inline-chip render + tests. NO new backend primitive (the event + emission already exist), NO new CSS class / mockup authoring, NO migration. Closest classes: `frontend-feature-with-event-wire-addition` 0.55 (57.100/108/116, 3-pt ~1.07 — but those added a FIELD to an existing event; this adds a NEW event type, slightly heavier on the codegen/parity side) + `loop-injection-primitive-spike` 0.55 (57.101 — also a NEW wire event type cross-stack, but THAT built a backend primitive too; this is lighter on backend, comparable on FE). **Ceremony-floor note** (57.120/122/123/126/128/129): the code is bounded but a full-ceremony parent-direct sprint WITH a mandatory drive-through does NOT drop below ~0.55 — and the drive-through SETUP (staging a REAL fatal termination — an always-error tool / a budget cap) is the wall-clock risk, mirroring the HITL-setup cost in 57.128/129. If the drive-through staging over-runs, expect a re-point toward 0.85.)
- **Agent-delegated: no** (parent-direct — the stuck-chip-clearing logic (which blocks to flip, terminal-without-new-status), the mockup-fidelity-safe render (reuse `var(--danger)`, no new CSS), and the drive-through staging (forcing a real fatal terminate) are correctness-critical and best hand-authored + self-verified). `agent_factor` 1.0 → 3-segment form.
- Bottom-up est ~6.0 hr (Day-0 三-prong (recon head-start, re-verify) ~0.5 · backend serializer + wire entry + parity test + codegen ~1.0 · FE `mergeEvent` case + turn field + chip render ~1.25 · tests (backend parity/serializer + FE `mergeEvent` cases) ~1.25 · drive-through (stage a real fatal terminate + clean restart + SSE-frame capture + AP-4 walk) ~1.5 · CHANGE-097 + closeout ~0.5) → class-calibrated commit ~3.3 hr (mult 0.55). Day-4 retro Q2 verifies (`chatv2-fatal-terminate-wire-surface` 1st data point; flag if the drive-through staging over-runs — the main risk).

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| **Drive-through can't stage a real fatal terminate** (the hardest part — need an actual `LoopTerminated`, not a normal answer) | Day-0 D-drive-through-trigger picks the cheapest reliable trigger: an always-error tool → `max_retries_exhausted`, OR a tiny per-run token budget → `budget_exceeded`, OR a forced circuit-open. Document the exact trigger; verify the backend log shows `LoopTerminated` fired. |
| **Wire-count drift (24 vs FE union 23)** | D-wire-count-24-vs-fe-union re-counts BOTH before editing; the codegen makes them equal (canonical 24→25); `check_event_schema_sync` is the gate. |
| **Codegen hand-edit / drift** | Edit only `WIRE_SCHEMA`; run the codegen; never hand-edit `loopEvents.generated.ts`; `check_event_schema_sync` (run_all) enforces sync. |
| **Mockup-fidelity baseline bump** (a new `oklch(`/`#hex` literal sneaks in via the chip) | Reuse `var(--danger)` inline (the existing waiting/Verification precedent uses tokens, not literals); `diff styles-mockup.css` empty; `npm run check:mockup-fidelity` asserts `HEX_OKLCH_BASELINE` 51 (run it, do NOT trust eyeballing). |
| **New status enum ripple** (adding a "terminated" status touches every status check) | Reuse "completed" + a `terminated` field (composer unfreeze logic keys off "completed"); no new enum value. |
| **`mergeEvent` mis-targets the pending block** (flips the wrong/none block) | D-pending-toolblock-identify confirms the pending-block predicate (`status:"pending"`); the Vitest case asserts only the pending block flips + others untouched. |
| **Risk Class E** — stale `--reload` backend serves pre-edit `sse.py`/`event_wire_schema.py` during the drive-through | clean restart (`Win32_Process` PID/PPID/StartTime sweep; orphan spawn-workers on :8000); confirm fresh sole owner + startup log before trusting the UI. |
| **Pre-existing billing flake** (`AD-Billing-Outbox-Drain-Test-Flake`) may surface once | re-run confirms 2727+5 (do NOT skip the test); the new tests are unrelated. |
| **`detail`/`last_state_version` None handling** | serialize as JSON `null`; the FE type marks them optional/nullable; the chip renders `reason` (always present) + `detail` only if set. |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- **A richer mockup-authored `TerminatedBlock` component + `.block.terminated` CSS** — deferred follow-on (the minimal danger chip + ToolBlock error flip is the real fix; the richer block would trip `mockup-author-and-port` ceremony + a baseline bump for marginal gain).
- **Retroactively terminating pending tools on a NORMAL stream-end** (no `loop_end`, no `loop_terminated`) — `useLoopEventStream` already force-completes; a separate edge case.
- **The resume-path terminate surfacing** — out of scope (the resume generator's terminate handling is a distinct path).
- **A new loop/turn `status` enum value** ("terminated") — reuse "completed" + a `terminated` field.
- **Any change to `loop.py` / the `LoopTerminated` emission** — the event already fires correctly; this is a pure surfacing fix.
- **`AD-ChatV2-HITL-Card-Tool-Name` / Inspector turn metadata / transcript retention** — the other bucket-C carryovers (separate slices).
- **ANY migration / new backend primitive.**
