# Sprint 57.116 Plan — Skills Force-Load Inspector Affordance (the user-turn "active skill" chip): Sprint 57.115 shipped a `/skill-name` deterministic force-load (the picked skill's instructions injected into the system prompt server-side, the model loads it WITHOUT `read_skill`) — but after send the force-load is INVISIBLE (the `/token` is stripped, there is no `read_skill` event). This slice surfaces it: the chat router emits a SERVER-CONFIRMED `active_skill` on the run's opening `loop_start` event (additive wire field, count stays 24), and the chat-v2 frontend stamps the just-sent user turn with it and renders a small "⚡ {skill}" chip. Server-confirmed (not the sent value) so an invalid/dropped skill name shows NO chip — avoiding an AP-4 mislabel. The first Skills-epic UX affordance (closes `AD-Skills-Inspector-Affordance`); `loop.py` / `events.py` / `read_skill`'s own tool-stream visibility stay UNTOUCHED.

**Status**: Approved-to-execute (user selected slice 2026-06-14: "Skills Inspector-affordance"; affordance = user-turn chip; scope = force-load only, read_skill untouched)
**Branch**: `feature/sprint-57-116-skills-inspector-affordance`
**Base**: `main` HEAD `fc385a87` (post-#290 merge — Sprint 57.115 slash-command force-load)
**Slice**: Skills System epic — **first UX affordance** (closes `AD-Skills-Inspector-Affordance`). 57.113 model-invoked lazy-load core / 57.114 per-tenant overlay / 57.115 user-invoked `/skill-name` force-load. The force-load path is deterministic but currently leaves NO trace in the timeline (unlike model-invoked `read_skill`, which IS a visible Cat-2 tool call). This slice gives the force-load a server-confirmed visual: a chip on the user turn. Per the rolling-planning discipline (CLAUDE.md §"也不是再寫一批新規劃文件"): this is a **feature continuation** of the validated Skills epic AND the validated chat-v2 additive-wire-field pattern (Sprint 57.108 `approval_requested` +tool_name/reason, `llm_response` +tokens) — NOT a new pattern → **no design note** (mirrors 57.108's feature-continuation cadence; only CHANGE-083 + retrospective).
**Scope decisions** (per user selection 2026-06-14 — group-1 Skills epic, slice = Inspector-affordance): (a) **Affordance = a user-turn chip** (NOT an Inspector-panel metadata row) — the chip "⚡ {skill}" attaches to the just-sent user message turn (the `.turn-head`, reusing the `.route-pill` pattern the `injected` tag already uses), the most direct fix for "invisible after send". (b) **Scope = force-load only** — the model-invoked `read_skill` path already shows as a Cat-2 tool call in the stream and is NOT touched. (c) **Server-confirmed, not client-predicted** — the chip is driven by a NEW `active_skill` field the backend adds to the opening `loop_start` SSE event, carrying the router's VALIDATED force-load name (an unknown/dropped name → `None` → no chip). The FE does NOT chip from the sent `force_load_skill` (that would lie when the name was invalid — AP-4). (d) **Additive wire field, count stays 24** — `active_skill` rides the existing `loop_start` event (mirrors 57.108); a codegen re-run regenerates the TS wire types; NO new event type. (e) **`loop.py` + `events.py` UNTOUCHED (Cat-1 boundary)** — force-load / skills is a chat-API + Cat-5/Cat-2 concern, not an orchestrator-loop concern (the loop only ever sees a `system_prompt` string, never a "skill"). The serializer (`sse.py`) emits `active_skill: null` by default; the chat ROUTER (which owns the validated force-load) injects the confirmed value into the serialized `loop_start` frame in `_stream_loop_events`. The Cat-1 `LoopStarted` dataclass gains NOTHING. (f) **Resume-safe** — the resume mirror (`_stream_resume_events`) has no force-load context → its `loop_start` carries `active_skill: null`; the FE stamps only on a truthy value (never overwrites an existing chip with null). (g) **Inline English chip label** (the chat-v2 `injected` tag is inline English `"injected mid-run"` — same convention; no i18n key).

---

## 0. Background

Sprint 57.115 closed `AD-Skills-Slash-Command`: a chat user types `/skill-name` in the chat-v2 composer; `InputBar` parses the leading token, sets `ChatRequest.force_load_skill`, strips the token from the message; the router validates the name against the per-tenant `skill_registry` (unknown → graceful `None`) and passes it to `build_handler`, which appends the skill's full instructions to the turn's system prompt under `## Active Skill` — the model follows the skill WITHOUT calling `read_skill` (the 57.115 drive-through proved `read_skill` 0× yet the output followed). The user-invoked force-load is deterministic and works — but **after send it leaves no trace**: the `/token` is stripped from the visible message, and (by design) there is no `read_skill` tool call to surface in the timeline. The model-invoked path (57.113) does NOT have this gap — `read_skill` rides the generic Cat-2 tool stream and IS visible.

`AD-Skills-Inspector-Affordance` (logged 57.113, reinforced 57.115) asks for a dedicated affordance so a force-loaded skill is visible. This slice closes it with the minimal, most-direct surface: a small chip on the user turn, driven by a SERVER-CONFIRMED signal.

### Design decision (a server-confirmed `active_skill` on the opening `loop_start` event via a chat-API-layer router augment — `loop.py`/`events.py` untouched — + a chat-v2 user-turn `.route-pill` chip; a 1-leg-3-case drive-through)

- **US-1 is "the server-confirmed wire signal"** (chat API layer; `loop.py`/`events.py` UNTOUCHED): the opening `loop_start` event (`LoopStarted` → `sse.py` serializer) gains an additive `active_skill: string | null` field. The Cat-1 loop has no concept of "skill" (it only receives a `system_prompt` string) → the field is NOT added to the `LoopStarted` dataclass. Instead: the `sse.py` serializer emits `"active_skill": None` as the default (so the wire field is always present + the serializer-vs-`event_wire_schema` conformance holds); the chat ROUTER — which already computed the validated `forced_skill` (`router.py:279`) — injects the confirmed value into the serialized `loop_start` frame inside `_stream_loop_events` (`router.py:641`, right after `serialize_loop_event`). The resume mirror (`_stream_resume_events`) passes nothing → `null`. `event_wire_schema.py` declares the field (drives codegen); a codegen re-run regenerates the TS types (wire count stays 24 — additive field, no new type).
- **US-2 is "the FE store stamp"**: the chat-v2 `UserTurn` type gains `activeSkill?: string`; `chatStore.mergeEvent`'s `case "loop_start"` stamps the most-recent `UserTurn` with `ev.data.active_skill` — **only when truthy** (a `null`/absent value never overwrites an existing chip; resume-safe). The user turn was pushed at send time (`pushUserMessage`) with no skill; `loop_start` (the first frame of the run that the send triggered) carries the confirmed skill a moment later.
- **US-3 is "the chip render"**: `UserTurn.tsx` renders a `.route-pill` chip "⚡ {activeSkill}" in the `.turn-head` (after the timestamp, mirroring the `injected` tag's conditional `.route-pill`) when `turn.activeSkill` is set. `.route-pill` uses `styles-mockup.css` design tokens (no new colour literal → `check:mockup-fidelity` count 51 holds). Inline English label.
- **US-4 is "Vitest"**: a `chatStore` test (a `loop_start` with `active_skill` stamps the last user turn; a `null` does not; a force-load run end-to-end) + a `UserTurn`/`TurnList` render test (the chip shows when `activeSkill` set, absent otherwise).
- **US-5 is "the drive-through"** (real chat-v2 + real Azure, 1 leg / 3 cases): (A) force-load `/release-notes <task>` via the picker → the just-sent user turn shows a "⚡ release-notes" chip (server-confirmed) AND the output follows the skill AND `read_skill` is 0× (the chip reflects the deterministic injection); (B) an unknown `/nonexistent task` → NO chip (the router dropped it → `active_skill: null`); (C) a plain message (no `/`) → NO chip. Proves the chip is server-confirmed, not a client echo.
- **Rejected / deferred**: an Inspector-panel metadata row (the user chose the user-turn chip; the Inspector turn-metadata wire — `AD-ChatV2-Inspector-Turn-Metadata-Wire` — is a separate slice); a dedicated NEW SSE event type (`skill_force_loaded`) — the additive field on `loop_start` is cheaper + count stays 24; specially marking the model-invoked `read_skill` as a "skill load" (out of scope — it's already visible as a tool call); threading `active_skill` through `AgentLoopImpl`/`loop.py` (the Explore agent's option — rejected: it leaks a chat-API concept into Cat-1; the router augment keeps `loop.py`/`events.py` diff 0); a per-turn skill chip for model-invoked skills (the model can self-select multiple skills mid-run; the run-level `loop_start` field models the ONE force-loaded skill — a per-`read_skill`-call chip is a separate affordance if ever wanted).

### Ground truth (Day-0 head-start — 2 Explore recon agents + direct greps, file:line on `main` HEAD `fc385a87`; ALL re-verified in the formal Day-0 三-prong §checklist 0.1)

**Backend wire (US-1):**
- `api/v1/chat/sse.py`: `serialize_loop_event` → `_serialize_inner` (`~:135-145`): `if isinstance(event, LoopStarted): return {"type":"loop_start", "data":{"session_id": ..., "request_id": str(event.event_id)}}`. → add `"active_skill": None` to the `data` dict (default; the router overrides for force-load). `LoopStarted` imported `:88`.
- `api/v1/chat/event_wire_schema.py`: `WIRE_SCHEMA["loop_start"] = {"session_id":"string | null", "request_id":"string"}` (`:87-90`). → add `"active_skill": "string | null"`. (The 24-type count is the number of dict KEYS in `WIRE_SCHEMA`, not the field count — adding a field keeps the count at 24.)
- `api/v1/chat/router.py`: the chat POST computes `forced_skill = (req.force_load_skill if (req.force_load_skill and skill_registry.get(req.force_load_skill) is not None) else None)` (`:279-283`) + passes `force_load_skill=forced_skill` to `build_handler` (`:330`). The stream is `StreamingResponse(_stream_loop_events(...))` (`:412-413`). `_stream_loop_events` (`async def` `:570`) iterates `loop.run()` + serializes each event via `serialize_loop_event(event)` (`:641`). → add an `active_skill: str | None = None` param to `_stream_loop_events`; pass `active_skill=forced_skill` at the `:413` call; at `:641`, after `payload = serialize_loop_event(event)`, `if isinstance(event, LoopStarted) and active_skill: payload["data"]["active_skill"] = active_skill`. (`LoopStarted` import in `router.py` — Day-0 confirms; add if absent.)
- The resume mirror `_stream_resume_events` (`:1080`, serializes at `:1090`) is NOT touched — resume has no force-load context → its `loop_start` keeps the serializer default `null` (the user turn already carries its chip from the initial run).
- `agent_harness/_contracts/events.py` `LoopStarted` (`~:72-74`, `session_id: UUID|None`) + `agent_harness/orchestrator_loop/loop.py`: **UNTOUCHED** (the field is a chat-API-layer concern; the loop never sets it).

**Codegen (US-1):**
- `scripts/codegen/generate_event_schemas.py`: generates `frontend/src/features/chat_v2/generated/loopEvents.generated.ts` (+ `events.json`) from `event_wire_schema.py`. Re-run (no-arg writes; `--check` in `run_all` diffs). After adding the field → regenerate → `run_all` codegen check passes (count 24). `KNOWN_LOOP_EVENT_TYPES` is generated + re-exported in `frontend/src/features/chat_v2/types.ts:55`.

**Frontend (US-2/US-3):**
- `features/chat_v2/types.ts`: `UserTurn = { role:"user"; id; at; text; injected? }` (`~:128-136`). → add `activeSkill?: string`.
- `features/chat_v2/store/chatStore.ts`: `pushUserMessage` (`~:350-356`, creates the user turn at send — no skill yet); `mergeEvent` `case "loop_start"` (`~:363-381`, sets `sessionId`+`status="running"`, dismisses the handoff banner, **preserves turns**). → in the `loop_start` case, when `ev.data.active_skill` is truthy, stamp the most-recent `UserTurn` (map `turns`, set `activeSkill` on the last `role==="user"`).
- `features/chat_v2/components/turns/UserTurn.tsx`: `.turn-head` (`~:48-58`) holds `displayName` + `.route-pill` role badge + the conditional `injected` `.route-pill` (`~:53-56`) + the `.mono.subtle` timestamp (`~:58`); `.turn-body` renders `{turn.text}` (`~:60`). → add a conditional `.route-pill` chip "⚡ {turn.activeSkill}" in `.turn-head` (after the timestamp).
- `features/chat_v2/styles? ` — `.route-pill` in `frontend/src/styles-mockup.css` (`~:1101-1105`, `var(--bg-2)`/`var(--border)`/`var(--fg-muted)` tokens) — REUSE (no new class, no colour literal).
- `useLoopEventStream.send(message, opts?: {forceLoadSkill?})` (Sprint 57.115) — **UNTOUCHED** (the FE already SENDS `force_load_skill`; this slice only reads the confirmed value BACK on `loop_start`).

**Tests + baselines:**
- Backend: `tests/unit/api/v1/chat/` (serializer / wire-schema) + `tests/integration/api/` (the force-load chat POST — extend `test_chat_force_load_skill.py` from 57.115 to assert the `loop_start` SSE frame carries `active_skill`). FE: `frontend/tests/unit/chat_v2/` (`chatStore.mergeEvent.test.ts` + a `UserTurn`/`TurnList` test).
- **Baselines (57.115 closeout)**: full pytest **2616+5skip** · wire count **24** · FE Vitest **863** · mockup-fidelity **51** · mypy `src` **0/370** · run_all **10/10** (count 24). Re-verify Day-0.
- **No migration.** **No design note** (feature continuation). **CHANGE next free = 083** (082 = slash-command). Wire count 24 unchanged (additive field); **codegen regen** (`loop_start` +`active_skill`).

### STALE / drift anchors to re-confirm in the formal Day-0 三-prong (§ checklist 0.1)

The exact `sse.py` `_serialize_inner` `LoopStarted` block + whether a serializer-vs-`event_wire_schema` conformance test exists (so the `sse.py` default `None` must be present for it to pass) · whether `router.py` already imports `LoopStarted` (else add) + the exact `_stream_loop_events` signature + call args at `:413` (so the `active_skill` thread is minimal + existing callers stay valid) · the `_stream_resume_events` confirm-no-touch · the exact `chatStore` `loop_start` case body (it returns a new state object — the stamp must map `turns` immutably) + how the "most-recent user turn" is identified (last `role==="user"`) · the `UserTurn.tsx` `.turn-head` structure + the `injected` `.route-pill` exact JSX to mirror · the `.route-pill` token set (no colour literal) · the chat-v2 Vitest harness for `chatStore.mergeEvent` + the user-turn render test location (`frontend/tests/unit/chat_v2/` — the 57.114 path-correction lesson; Glob the basename — the 57.109 unique-basename lesson) · the codegen command + that `run_all`'s codegen `--check` will diff until regen · a dev tenant + a custom skill for the force-load leg (reuse the 57.115 `acme-skills` with the `release-notes` overlay) · baselines re-verify (pytest 2616+5skip / wire 24 / Vitest 863 / mockup 51 / mypy 0/370 / run_all 10/10).

## 1. Sprint Goal

A force-loaded skill becomes **visible** in chat-v2: the chat router emits a SERVER-CONFIRMED `active_skill` (the validated `force_load_skill`, or `null`) as an additive field on the run's opening `loop_start` SSE event (the `sse.py` serializer defaults it `null`; the router injects the confirmed value in `_stream_loop_events`; `event_wire_schema.py` declares it + a codegen re-run regenerates the TS types; wire count stays 24; `loop.py`/`events.py` UNTOUCHED), and the chat-v2 frontend stamps the just-sent `UserTurn` with it (`chatStore` `loop_start` case, truthy-guarded) and renders a "⚡ {skill}" `.route-pill` chip in the `.turn-head` — proven by a real chat-v2 + Azure drive-through (force-load → the user turn shows the chip + the output follows the skill + `read_skill` 0×; an unknown `/token` → no chip; a plain message → no chip). Closes `AD-Skills-Inspector-Affordance`; an Inspector-panel metadata row, a per-`read_skill` chip, and a dedicated skill SSE event stay deferred.

## 2. User Stories

- **US-1**: 作為 platform，我希望 run 的開場 `loop_start` 事件帶一個 server-confirmed 的 `active_skill: string | null`：`sse.py` 的 `LoopStarted` serializer 預設輸出 `"active_skill": None`（宣告 wire 欄位恆在 + 通過 serializer-vs-schema conformance），`event_wire_schema.py` 宣告該欄位（驅動 codegen），chat router 在 `_stream_loop_events` 序列化 `loop_start` frame 後注入已驗證的 `forced_skill`（`router.py:641`）；`loop.py`/`events.py`/`LoopStarted` dataclass 不動（force-load 是 chat-API/Cat-5 概念，非 Cat-1）；codegen re-run 重生 TS 型別、wire count 維持 24，以便前端能取得「真的被 force-load 的 skill 名」（未驗證/dropped → null）。
- **US-2**: 作為 chat 使用者，我希望前端 store 把 confirmed 的 `active_skill` 蓋到我剛送出的那則 user turn：`UserTurn` 型別加 `activeSkill?: string`；`chatStore.mergeEvent` 的 `case "loop_start"` 在 `ev.data.active_skill` 為 truthy 時把最新的 `UserTurn` 蓋上（null/absent 不覆蓋既有 chip — resume 安全），以便 force-load 的事實被綁到正確的訊息。
- **US-3**: 作為 chat 使用者，我希望那則 user turn 顯示一個「⚡ {skill}」chip：`UserTurn.tsx` 在 `turn.activeSkill` 有值時於 `.turn-head`（timestamp 之後）渲染一個 `.route-pill` chip（複用 `injected` tag 同款 pattern；`styles-mockup.css` token、無新 color literal、mockup-fidelity 51 holds；inline 英文 label），以便我送出後看得到剛才用了哪個 skill。
- **US-4**: 作為 platform，我希望單元測試守住：backend（`loop_start` serializer 預設 `active_skill: None` · `event_wire_schema` 含該 key · 一個 force-load chat POST 的 `loop_start` frame 帶 confirmed 名 · 一個未知名 → `null`）；FE Vitest（`chatStore` `loop_start` 帶 `active_skill` → 蓋到最新 user turn / `null` → 不蓋 · `UserTurn` 在 `activeSkill` 有值時渲染 chip、否則無），以便回歸受保護。
- **US-5**: 作為 reviewer，我希望一個真 drive-through（真 UI chat-v2 :3007 + 真後端 + 真 Azure LLM，非 echo/mock）證明：（A）force-load — 以 picker 選 `/release-notes` + 一般任務 → 送出的 user turn 顯示「⚡ release-notes」chip（server-confirmed）且輸出跟隨 skill、`read_skill` 0×；（B）graceful — `/nonexistent task` → 無 chip（router drop → `active_skill: null`）；（C）plain — 一般訊息（無 `/`）→ 無 chip。截圖 + observed-vs-intended 記入 progress.md（證明 chip 是 server-confirmed 非 client echo）。

## 3. Technical Specifications

### 3.0 Architecture (an additive `active_skill` field on `loop_start` via the chat-API serializer default + a router `_stream_loop_events` augment + a codegen regen + a chat-v2 `UserTurn.activeSkill` store stamp + a `.route-pill` chip; NO new SSE event type / wire count 24 UNCHANGED / `loop.py`/`events.py`/`LoopStarted` dataclass/`read_skill`/the resume mirror/`useLoopEventStream` UNTOUCHED; NO migration)

```
api/v1/chat/sse.py (EDIT): LoopStarted serializer data dict += "active_skill": None (default; router overrides)
api/v1/chat/event_wire_schema.py (EDIT): WIRE_SCHEMA["loop_start"] += "active_skill": "string | null" (count 24 unchanged)
api/v1/chat/router.py (EDIT): _stream_loop_events(..., active_skill=None) param + pass active_skill=forced_skill at the call + inject into the serialized loop_start frame at :641
scripts/codegen/generate_event_schemas.py → REGEN frontend/src/features/chat_v2/generated/loopEvents.generated.ts (+ events.json) — loop_start +active_skill
frontend chat_v2: types.ts (UserTurn += activeSkill?) + store/chatStore.ts (loop_start stamps the last user turn, truthy guard) + components/turns/UserTurn.tsx (.route-pill chip)
loop.py / events.py / LoopStarted dataclass / read_skill / _stream_resume_events / useLoopEventStream / migration: UNTOUCHED
```

### 3.1 `active_skill` on `loop_start` — serializer default + wire schema (US-1, backend half)

- **`sse.py`** (`_serialize_inner`, the `LoopStarted` branch): add `"active_skill": None` to the returned `data` dict. The Cat-1 loop never sets a skill; the serializer's job is to make the field ALWAYS present on the wire (so the FE type is non-conditional + a serializer-vs-`event_wire_schema` conformance test, if present, passes). The real value comes from the router augment (§3.2).
- **`event_wire_schema.py`** (`WIRE_SCHEMA["loop_start"]`): add `"active_skill": "string | null"`. This is the codegen source → the generated `loopEvents.generated.ts` `loop_start` data type gains `active_skill: string | null`. The dict-KEY count of `WIRE_SCHEMA` (the 24 wire types) is unchanged — `active_skill` is a field inside `loop_start`, not a new top-level type.

### 3.2 Router augment — inject the confirmed skill into the `loop_start` frame (US-1, router half)

- **`router.py`** `_stream_loop_events`: add `active_skill: str | None = None` to the signature; at the `StreamingResponse(_stream_loop_events(...))` call (`:413`) pass `active_skill=forced_skill` (already computed at `:279`). Inside the generator, at `:641` after `payload = serialize_loop_event(event)`: `if isinstance(event, LoopStarted) and active_skill: payload["data"]["active_skill"] = active_skill`. (Confirm `LoopStarted` is imported in `router.py`; add to the `agent_harness._contracts.events` import if absent.) The augment runs once per stream (only the single `LoopStarted` frame matches). The `_stream_resume_events` mirror is NOT given an `active_skill` → its `loop_start` keeps the serializer default `null`.
- Why router-augment, not thread-through-loop: force-load/skills is a chat-API + Cat-5/Cat-2 concept; the orchestrator loop (Cat 1) only ever receives a `system_prompt` string. Putting `active_skill` into `LoopStarted`/`AgentLoopImpl` would leak a chat-API concept into Cat 1. The router already owns the validated `forced_skill` and already iterates+serializes every frame → the augment is ~2 lines and keeps `loop.py`/`events.py` diff 0 (consistent with 57.115).

### 3.3 Codegen regen (US-1)

- After §3.1–3.2, run `python scripts/codegen/generate_event_schemas.py` → regenerates `frontend/src/features/chat_v2/generated/loopEvents.generated.ts` (+ `events.json`) with `loop_start.active_skill`. `run_all`'s codegen `--check` will FAIL until regen, then PASS (count 24). Commit the regenerated artifacts (the 57.108 additive-field-+-regen pattern).

### 3.4 FE store stamp — `UserTurn.activeSkill` (US-2)

- **`types.ts`**: `UserTurn` += `activeSkill?: string` (after `injected?`).
- **`chatStore.ts`** (`mergeEvent` `case "loop_start"`): the case returns a new state preserving `turns`. When `ev.data.active_skill` is truthy, also map `turns` to set `activeSkill` on the LAST `role === "user"` turn (immutable map; a helper `stampLastUserTurn(turns, skill)`). A `null`/absent `active_skill` → `turns` unchanged (never overwrites an existing chip — the resume mirror's `null` is a no-op). The user turn was pushed by `pushUserMessage` at send; `loop_start` is the first frame of THAT run → the last user turn is the right target.

### 3.5 FE chip render — `UserTurn.tsx` (US-3)

- **`UserTurn.tsx`**: in `.turn-head`, after the timestamp `<span>`, add `{turn.activeSkill && <span className="route-pill" title={`Skill: ${turn.activeSkill}`}>⚡ {turn.activeSkill}</span>}` (mirroring the `injected` tag's conditional `.route-pill`). `data-testid="user-turn-skill-chip"`. `.route-pill` (`styles-mockup.css`) uses design tokens only → no colour literal → `check:mockup-fidelity` 51 holds. Inline English (the `injected` tag is inline English — same convention).

### 3.6 Drive-through (US-5) — real chat-v2 + real Azure LLM

The mockup needs no change (the chip is a net-new conditional element on the existing user turn). The drive-through:
1. Real UI :3007 + a fresh single-process no-reload backend (Risk Class E clean restart + `Win32_Process` PID/PPID/StartTime orphan sweep + a startup probe) + real Azure (non-echo). Reuse the 57.115 dev tenant `acme-skills` (jamie@acme.com, cookie) with its persisted `release-notes` overlay.
2. **Leg A (force-load → chip + determinism)**: in chat-v2 (real_llm), `/` → pick `release-notes` (or type `/release-notes`) + a generic task → Send. Expect: the sent user turn shows a "⚡ release-notes" chip; the output follows the release-notes shape; the Inspector shows `read_skill` 0× (the chip reflects the deterministic force-load). Screenshot the user turn with the chip + the Inspector.
3. **Leg B (graceful unknown → no chip)**: `/nonexistent write a haiku` → the router drops the unknown name (`active_skill: null`) → NO chip on the user turn; the chat answers normally. Screenshot the chip-less turn.
4. **Leg C (plain → no chip)**: a normal message with no `/` → NO chip. Screenshot.
5. Screenshots (the chip present / absent×2) + observed-vs-intended in progress.md. Verify the chip is SERVER-confirmed: Leg B proves an invalid name (which the FE DID send as a candidate) yields NO chip → the chip is not a client echo (Drive-Through-Acceptance + AP-4 guard — no mislabel).

### 3.7 What is explicitly NOT done

An Inspector-panel "active skill" metadata row (the chosen affordance is the user-turn chip; `AD-ChatV2-Inspector-Turn-Metadata-Wire` is a separate slice); a dedicated NEW SSE event type for skill loads (the additive `loop_start` field is cheaper; count stays 24); specially marking the model-invoked `read_skill` tool call as a "skill load" (it's already visible as a Cat-2 tool call — out of scope per the user's "force-load only"); threading `active_skill` through `AgentLoopImpl`/`loop.py`/the `LoopStarted` dataclass (the router augment keeps Cat-1 untouched); a per-`read_skill`-call chip for model-invoked skills; touching `read_skill`'s behaviour / `useLoopEventStream` / the resume mirror / any migration.

### 3.8 Validation (US-1..US-5)

Unit (backend, CI-safe): `sse.py` — `serialize_loop_event(LoopStarted(...))` `data` has `active_skill` key defaulting `None`; `event_wire_schema` — `WIRE_SCHEMA["loop_start"]` has `active_skill`; a serializer-vs-schema conformance test (if present) stays green. Integration (TestClient, stubbed LLM): a chat POST with a valid `force_load_skill` for a tenant that has it → the emitted `loop_start` SSE frame's `data.active_skill` == the name; an unknown `force_load_skill` → `loop_start.active_skill` is `null` (graceful); a request with no `force_load_skill` → `null`. FE (Vitest): `chatStore` — a `loop_start` event with `active_skill` stamps the last `UserTurn.activeSkill`; a `null` leaves it unset; a non-user last turn is not mis-stamped; `UserTurn`/`TurnList` — the chip renders when `activeSkill` set, absent otherwise. Gates: mypy strict 0 · run_all 10/10 (count 24; codegen REGEN committed → `--check` clean) · full pytest +N (0 del) vs 2616 · Vitest +M vs 863 · mockup-fidelity 51 holds (the chip reuses `.route-pill`, no CSS change) · `loop.py`/`events.py`/`LoopStarted` dataclass/`read_skill`/`_stream_resume_events`/`useLoopEventStream` UNTOUCHED · LLM-neutrality lint green · `check_cross_category_import` green.

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `backend/src/api/v1/chat/sse.py` | EDIT — `LoopStarted` serializer `data` += `"active_skill": None` (default) |
| 2 | `backend/src/api/v1/chat/event_wire_schema.py` | EDIT — `WIRE_SCHEMA["loop_start"]` += `"active_skill": "string \| null"` (count 24 unchanged) |
| 3 | `backend/src/api/v1/chat/router.py` | EDIT — `_stream_loop_events(..., active_skill=None)` + pass `active_skill=forced_skill` + inject into the serialized `loop_start` frame; import `LoopStarted` if absent |
| 4 | `frontend/src/features/chat_v2/generated/loopEvents.generated.ts` | REGEN (codegen) — `loop_start` +`active_skill` |
| 5 | `frontend/src/features/chat_v2/generated/events.json` | REGEN (codegen) |
| 6 | `backend/tests/unit/api/v1/chat/test_loop_start_active_skill.py` | NEW — serializer default `None` + wire-schema key + (conformance if present) |
| 7 | `backend/tests/integration/api/test_chat_force_load_skill.py` | EDIT — assert the `loop_start` SSE frame carries `active_skill` (confirmed / unknown→null) |
| 8 | `frontend/src/features/chat_v2/types.ts` | EDIT — `UserTurn` += `activeSkill?: string` |
| 9 | `frontend/src/features/chat_v2/store/chatStore.ts` | EDIT — `loop_start` case stamps the last `UserTurn.activeSkill` (truthy guard) |
| 10 | `frontend/src/features/chat_v2/components/turns/UserTurn.tsx` | EDIT — `.route-pill` "⚡ {activeSkill}" chip in `.turn-head` |
| 11 | `frontend/tests/unit/chat_v2/chatStore.activeSkill.test.ts` | NEW — Vitest (stamp on truthy / no-stamp on null / last-user-turn target) |
| 12 | `frontend/tests/unit/chat_v2/UserTurn.skillChip.test.tsx` | NEW — Vitest (chip present when `activeSkill` set, absent otherwise) |
| 13 | `claudedocs/4-changes/feature-changes/CHANGE-083-*.md` | NEW — change record (incl. the drive-through) |
| — | `loop.py` / `events.py` / `LoopStarted` dataclass / `read_skill` / `_stream_resume_events` / `useLoopEventStream` / migration / a design note | **UNTOUCHED / NONE** |

## 5. Acceptance Criteria

1. The `loop_start` SSE event carries an additive `active_skill: string | null` field: the `sse.py` serializer defaults it `None`; `event_wire_schema.py` declares it; a codegen re-run regenerates the TS types; wire count stays 24; `loop.py`/`events.py`/the `LoopStarted` dataclass UNTOUCHED.
2. The chat router injects the VALIDATED `forced_skill` into the `loop_start` frame in `_stream_loop_events` (a valid name → that name; an unknown name → `null`); the resume mirror is untouched (its `loop_start` stays `null`).
3. The chat-v2 `UserTurn` type gains `activeSkill?`; `chatStore`'s `loop_start` case stamps the most-recent user turn only when `active_skill` is truthy (a `null` never overwrites an existing chip).
4. `UserTurn.tsx` renders a `.route-pill` "⚡ {skill}" chip in the `.turn-head` when `activeSkill` is set (mockup tokens, no colour literal); absent otherwise.
5. Unit + integration + Vitest cover: the serializer default + wire-schema key; a force-load chat POST's `loop_start.active_skill` (confirmed / unknown→null); the store stamp (truthy / null / last-user-turn); the chip render (present / absent).
6. Gates: mypy strict 0 · run_all 10/10 (count 24, codegen regen committed) · full pytest +N (0 del) vs 2616 · Vitest +M vs 863 · mockup-fidelity 51 holds · LLM-neutrality + `check_cross_category_import` green.
7. Real drive-through PASS: (A) force-load → the user turn shows the "⚡ {skill}" chip + the output follows + `read_skill` 0×; (B) unknown `/token` → no chip; (C) plain message → no chip. Screenshots + observed-vs-intended (proves server-confirmed, not client echo).
8. `AD-Skills-Inspector-Affordance` closed; CHANGE-083; calibration recorded (`frontend-feature-with-event-wire-addition` 0.55, 3rd data point); remaining Skills ADs (authoring UI / per-tenant quota / bundled scripts / Inspector-panel metadata row) carried.

## 6. Deliverables

- [ ] US-1 `active_skill` on `loop_start` (sse.py default + event_wire_schema field + router `_stream_loop_events` augment) + codegen regen + backend tests (serializer default · wire-schema key · force-load POST confirmed/unknown→null)
- [ ] US-2 `UserTurn.activeSkill?` + `chatStore` `loop_start` stamp (truthy guard) + Vitest (stamp/no-stamp/last-user-turn)
- [ ] US-3 `UserTurn.tsx` `.route-pill` "⚡ {skill}" chip + Vitest (present/absent)
- [ ] US-4 (folded into US-1..US-3 test bullets above)
- [ ] US-5 drive-through PASS (force-load → chip + follow + read_skill 0× · unknown → no chip · plain → no chip; screenshots + observed-vs-intended)
- [ ] CHANGE-083 + closeout (retro Q1-Q7 + calibration + navigators + next-phase-candidates `AD-Skills-Inspector-Affordance` closed + remaining Skills ADs carried; NO design note — feature continuation; 17.md N/A — no new contract)

## 7. Workload Calibration

- Scope class **`frontend-feature-with-event-wire-addition` 0.55** (3rd data point; 57.100 ≈1.0 + 57.108 ≈1.05-1.1, mean ~1.05 IN band → KEEP). EXACT shape match: an additive field on an EXISTING event (count unchanged 24) + codegen regen + chat-v2 FE store-capture + render + cross-stack parity. Lighter than 57.115's `skills-slash-command-fullstack` 0.55 (no greenfield widget, no new endpoint, no request field — the FE already SENDS `force_load_skill`; this only reads it back).
- **Agent-delegated: no** (parent-direct; the 2 Explore recon agents already ran; the slice is ~6 hr of precise small edits — the router-augment design decision + the truthy-guard stamp are the only subtlety). `agent_factor` 1.0 → §Workload uses the 3-segment form (class multiplier only).
- Bottom-up est ~6 hr (`sse.py`+`event_wire_schema.py` field + backend serializer/conformance tests ~0.75 · router `_stream_loop_events` augment + integration test ~1 · codegen regen ~0.25 · `types.ts`+`chatStore` stamp + Vitest ~1.25 · `UserTurn.tsx` chip + Vitest ~1 · drive-through ~1 · CHANGE-083 + closeout ~0.75) → class-calibrated commit ~3.3 hr (mult 0.55). Day-4 retro Q2 verifies (3rd `frontend-feature-with-event-wire-addition` data point; if ratio diverges > 30% note for the matrix).

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| A serializer-vs-`event_wire_schema` conformance test asserts exact key sets → the `sse.py` default `None` is REQUIRED (else the schema declares a key the serializer omits) | Day-0 Prong-2 greps for a conformance test; `sse.py` emits `"active_skill": None` so `serialize_loop_event(LoopStarted)` keys ⊇ schema keys; a unit test asserts the key is present |
| `router.py` does not import `LoopStarted` → the `isinstance` augment NameErrors | Day-0 confirms the import; add `LoopStarted` to the `agent_harness._contracts.events` import if absent; mypy + the integration test catch a miss |
| The augment is placed where `forced_skill` is NOT in scope (a nested generator) | `_stream_loop_events` gains an explicit `active_skill` param threaded from the `:413` call (where `forced_skill` IS in scope); NOT a closure capture |
| The resume `loop_start` mis-shows / clears a chip | `_stream_resume_events` is NOT given `active_skill` → its `loop_start` is `null`; the FE stamp is truthy-guarded → a `null` never overwrites the chip set on the initial run; a Vitest case covers `null` no-op |
| The store stamps the WRONG turn (not the just-sent one) | the user turn is pushed at send (`pushUserMessage`) immediately before the run; `loop_start` is the first frame of THAT run → the last `role==="user"` turn is the target; a Vitest case asserts the last-user-turn target + that a trailing agent turn is not mis-stamped |
| The chip introduces a colour literal → `check:mockup-fidelity` count breaks | reuse the existing `.route-pill` (design tokens only); no CSS change; run `check:mockup-fidelity` (51 holds); the 57.115 `oklch`-literal lesson |
| Codegen not re-run → `run_all` `--check` fails (or a stale generated type) | run `python scripts/codegen/generate_event_schemas.py` after the schema edit; commit the regenerated `loopEvents.generated.ts` + `events.json`; `run_all` 10/10 confirms |
| Risk Class E — a stale `--reload` backend serves old code (no `active_skill` on the wire) at the drive-through | clean no-reload restart from repo-root (`--env-file .env` + `PYTHONPATH=backend/src`) + `Win32_Process` PID/PPID/StartTime orphan sweep + a startup probe (the 57.97/109/110/114/115 routine) before driving |
| Test path — the new Vitest files land in a co-located `__tests__/` vite does not collect | place under `frontend/tests/unit/chat_v2/`; Glob the basename across the test tree before creating (57.109/57.114 lessons) |
| AP-4 — the chip shows even for a dropped/invalid skill (a client echo) | the chip is driven by the SERVER `active_skill` (the router's validated value), NOT the sent `force_load_skill`; Leg B (unknown → no chip) proves it; a Vitest `null` no-op case backs it |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- An Inspector-panel "active skill" metadata row (`AD-ChatV2-Inspector-Turn-Metadata-Wire` is a separate slice; the chosen affordance is the user-turn chip).
- A dedicated NEW SSE event type for skill loads (the additive `loop_start` field is the chosen mechanism; count stays 24).
- Specially marking the model-invoked `read_skill` tool call as a "skill load" (it is already visible as a Cat-2 tool call; the user scoped this to force-load only).
- A per-`read_skill`-call chip for model-invoked skills (the run-level `loop_start` field models the one force-loaded skill).
- Threading `active_skill` through `AgentLoopImpl`/`loop.py`/the `LoopStarted` dataclass (the router augment keeps Cat-1 untouched).
- `AD-Skills-Authoring-UI` / `AD-Skills-Per-Tenant-Quota` / `AD-Skills-Bundled-Scripts` / multi-skill-per-command / `AD-Skills-SlashMenu-Mockup`.
- The remaining `next-phase-candidates.md` map (IAM Block C MFA WebAuthn/recovery, SOC 2 + SBOM, frontend mockup rebuild, non-Azure adapters).
