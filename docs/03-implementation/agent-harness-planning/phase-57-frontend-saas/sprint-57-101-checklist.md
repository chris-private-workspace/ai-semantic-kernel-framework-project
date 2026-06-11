# Sprint 57.101 — Checklist (between-turns message injection primitive — B1: a user sends a supplementary instruction MID-RUN; it drains at the next turn boundary, is guardrail-checked, the agent picks it up; one primitive, B2 TEAMMATE reuses the drain seam later)

**Plan**: [`sprint-57-101-plan.md`](./sprint-57-101-plan.md)
**Created**: 2026-06-11
**Status**: Draft — Day-0 verify in progress

> Rule: only `[ ]` → `[x]`; never delete unchecked items; defer with `🚧 + reason`.
> **New-domain spike** (NEW Cat 1 `MessageInbox` contract + NEW `_run_turns` drain seam + NEW `MessageInjected` wire type) → **design note 26** (`sprint-workflow.md §Step 5.5`, the 57.94/97/98 precedent). Record = CHANGE-068 + design note 26 + **update 17.md** (`MessageInbox` Cat 1 + `message_injected` Cat 12 wire). Gate = full backend pytest + frontend Vitest green (NET delta) + **drive-through PASS** (real UI → multi-turn run → mid-run inject → next turn picks it up + the injected UserTurn appears; + guardrail-on-injected). Load-bearing decisions: drain at the `_run_turns` top BEFORE the between-turns guardrail (free Cat 9 check); a MODULE-level `InjectionRegistry` bridges the separate inject-POST + run requests (a per-request mailbox cannot); render the injected message on the drain event (not optimistically). Out: TEAMMATE wiring (B2), inject-during-pause, optimistic echo, edit/cancel queue, persistence, per-tenant policy (C3).

---

## Day 0 — Plan-vs-Repo Verify + Branch

### 0.1 Three-prong Day-0 verify
- [x] **Prong 1 (path)**: re-confirmed all anchors on `71336195` (2-agent Explore recon + personal re-read of loop.py seam/ctor + event_wire_schema) — `loop.py` `_run_turns :1944-1957` (`while` @`:1983`) + termination checks `:1984-2008` + between-turns gate `:2010-2034` (`_cat9_between_turns_check :2022`, gated `turn_count>0` `:2020`, `skip…=False` `:2034`) + msg-append `:2490-2493` + ctor `:373-431` (`verifier_registry :420` / `verification_escalate_on_max :430` LAST) + assign `:432-483` (`self._verification_escalate_on_max :483` LAST) · `_contracts/chat.py Message :75-96` · `_contracts/events.py LoopEvent` · `event_wire_schema.py` WIRE_SCHEMA **23** (`:30`/`:77`) · `test_event_wire_schema_parity.py:142` (`== 23`) · `sse.py` approval branch `:229-238` · `router.py` chat POST `:148-350` (register `:273-274`) + resume `:832-886` + `_stream_resume_events :807-829` · `session_registry.py get_default_registry` · `handler.py :247-259` + `:514-572` · `subagent/mailbox.py :46-100` (B2 ref). FE: `InputBar.tsx :77-82` + `:162-170` (`disabled={isRunning}` `:169`) + Stop `:178-188` · `chatService.ts :64-92`/`:107-131`/`:140+` · `useLoopEventStream.ts :60-92`/`:98-120`/`:127` · `chatStore.ts mergeEvent :298-620` (`approval_requested :454-491`) · `types.ts UserTurn :123-128` · `loopEvents.generated.ts` (KNOWN set) · `UserTurn` render (Day-2 locate). (progress.md Day-0 Prong 1)
- [x] **Prong 2 (content)**: confirmed — the between-turns gate reads `messages` `:2023` → draining+appending at `:2009` (before the gate) = injected content guardrail-checked when the gate runs; the drain runs every iteration on `inbox is not None` (NOT `turn_count`); `Message(role="user", content=str)` append shape (`:2492`); `event_wire_schema` insertion order = generated order → APPEND `message_injected` at the END; `sse.py` reads `event.<field>` → `event.text`; `resume()` shares `_run_turns` but inject-during-pause out of scope (409) + inbox None/empty on resume → drain []=no-op (no run/resume interaction). (progress.md Day-0 Prong 2)
- [x] **Prong 2.5 (frontend tree)**: confirmed — PRODUCTION composer = `InputBar.tsx` (NOT `Composer.tsx`, dead mockup scaffolding); the 2 guards `:169 disabled={isRunning}` + `:79 send-guard`; Stop `:178-188` stays; injected-tag + inject-affordance have NO mockup source → mockup `.btn`/`.user-turn` vocab + `var(--*)` (no new HEX/oklch); `chatStore.mergeEvent.test.ts` + `eventSchema.generated.test.ts` EXIST → EXTEND (the 57.100 D-DAY0-2 lesson); NO InputBar test → NEW. (progress.md Day-0 Prong 2.5)
- [x] **Prong 3 (schema)**: N/A confirmed — no DB/migration/ORM (the inbox is in-memory, per-run). The wire change is a NEW event TYPE → `len(WIRE_SCHEMA)` **23→24** (D-DAY0-1: count is 23 not 22 — 57.96 added subagent_child; `:40` MHist "22" is stale) + `test_event_wire_schema_parity.py:142` `== 24` + the WIRED_EVENT_INSTANCES set + the doc count comments (`event_wire_schema.py :30`+`:77`; `_contracts/events.py`). `check_event_schema_sync` re-greens after regen.
- [x] **Baseline capture**: `main 71336195` — mypy `src` **0/353** ✅ · pytest collect `-m "not real_llm"` **2304** ✅ · run_all **10/10** ✅. Frontend Vitest count + `check:mockup-fidelity` HEX_OKLCH baseline → captured Day 2/3 before FE edits.
- [x] **Design-note decision**: new-domain spike → design note 26 (`26-between-turns-injection-design.md`); plan to UPDATE 17.md (`MessageInbox` Cat 1 + `message_injected` Cat 12). Confirmed in progress.md.
- [x] **Drive-through setup**: a multi-turn investigation prompt (tool-using, ≥3 turns) for the mid-run inject; a between-turns-guardrail-tripping instruction for the guardrail-on-injected case; cheap deployment (57.97) set; clean-restart plan (Risk Class E) — noted in progress.md, executed Day 3
- [x] Catalogue Day-0 drift in progress.md (D-DAY0-1 count 23→24 / D-DAY0-2 drain placement + turn-0/resume edges / D-DAY0-3 production composer = InputBar / D-DAY0-4 tests exist→extend); **go/no-go = GO** (slice = §4 file list, unchanged; larger than 57.98-100 ~10 hr; plan §7 split B1a/B1b clause active if Day-1 ripples > 20%)

### 0.2 Branch
- [x] Branch `feature/sprint-57-101-between-turns-injection` from `main` (`71336195`)
- [ ] plan + checklist + progress committed (Day-0 commit)

---

## Day 1 — The `MessageInbox` contract + loop drain seam + the `MessageInjected` event (US-1/US-2)

### 1.1 The contract + loop drain
- [ ] **`_contracts/inbox.py`** — NEW `MessageInbox(ABC)` (`async def drain(self) -> list[Message]`); imports only `Message`; file header; `check_llm_sdk_leak` 0
- [ ] **`loop.py` ctor** — +`message_inbox: MessageInbox | None = None` (after `verifier_registry`); `self._message_inbox`; MHist 1-line
- [ ] **`loop.py` `_run_turns` drain seam** — at the top of the `while` body (before the `:2020` between-turns gate): `if self._message_inbox is not None: for m in await self._message_inbox.drain(): messages.append(m); yield MessageInjected(text=<str(m.content)>)`; the drained messages are appended BEFORE `_cat9_between_turns_check` (free guardrail check); `message_inbox=None` byte-identical; MHist 1-line; mypy `src` 0

### 1.2 The `MessageInjected` wire event + codegen
- [ ] **`_contracts/events.py`** — +`MessageInjected(LoopEvent)` (`text: str = ""`); bump subclass-count comment; MHist
- [ ] **`api/v1/chat/sse.py`** — +`MessageInjected` serializer branch → `{"type":"message_injected","data":{"text":event.text}}`; MHist
- [ ] **`api/v1/chat/event_wire_schema.py`** — +`"message_injected": {"text":"string"}`; count comments 23→24; MHist
- [ ] **`scripts/codegen/generate_event_schemas.py`** — +`"message_injected": "MessageInjectedEvent"` in `WIRE_TYPE_TO_INTERFACE`; MHist
- [ ] **codegen regen** — `python scripts/codegen/generate_event_schemas.py` → `events.json` + `loopEvents.generated.ts` regenerated; `git diff` = ONLY `message_injected` added (new interface + union member + KNOWN set entry; count 24); no spurious reformat
- [ ] **`test_event_wire_schema_parity.py`** — `:142` `== 24` + a `MessageInjected(text="hi")` wired instance; passes
- [ ] **backend lint/type** — mypy `src` 0; `check_event_schema_sync` in sync; `check_ap1` green (drain is data-flow, not a pipeline restructure)

---

## Day 2 — The injection channel + API + the FE composer-mid-run + render (US-3/US-4/US-5)

### 2.1 The InjectionRegistry + inject endpoint (US-3)
- [ ] **`api/v1/chat/injection_registry.py`** — NEW `InjectionRegistry` (module singleton, `dict[UUID, asyncio.Queue[Message]]`): `register`/`put`/`drain`(get_nowait loop)/`unregister` + `get_default_injection_registry()`; `QueueMessageInbox(MessageInbox)` binds `(registry, session_id)`; file header; `check_llm_sdk_leak` 0
- [ ] **`router.py` register/unregister** — at chat POST (alongside `:273-274` SessionRegistry register) `get_default_injection_registry().register(session_id)`; in the stream `finally` `unregister(session_id)`; MHist
- [ ] **`router.py` `POST /{session_id}/inject`** — `InjectRequestBody(message: str, max 4096)`; `Depends(get_current_tenant)`; verify active + owned via SessionRegistry (404 cross-tenant / 409 not-running); `put(session_id, Message(role="user", content=body.message))`; 202 `{"status":"queued"}`; MHist
- [ ] **`handler.py`** — construct `QueueMessageInbox(get_default_injection_registry(), session_id)` + pass `message_inbox=` to the loop (real_llm path); MHist; mypy `src` 0

### 2.2 The composer usable mid-run + inject client (US-4)
- [ ] **`chatService.ts`** — +`injectMessage(sessionId, message)` POST `/api/v1/chat/${sessionId}/inject` body `{message}`; MHist
- [ ] **`useLoopEventStream.ts`** — +`inject(text)` → `injectMessage(sessionId, text)`; returned alongside `send`/`resume`/`cancel`/`isRunning`; MHist
- [ ] **`InputBar.tsx`** — textarea enabled mid-run (drop the `disabled={isRunning}` on the textarea); the send path: `isRunning && trimmed` → `inject(trimmed)` + clear (NOT `send`); idle → `send` (unchanged); keep the Stop button; labelled inject affordance (`data-testid="inject-send"`, aria makes clear it's a note to the running agent); MHist

### 2.3 The injected message renders (US-5)
- [ ] **`types.ts`** — `UserTurn` +`injected?: boolean`; MHist
- [ ] **`chatStore.ts`** — +`message_injected` case → append `UserTurn {role:"user", id, at, text: ev.data.text, injected:true}`; MHist
- [ ] **the `UserTurn` render** — when `turn.injected`, show an "injected" tag (mockup vocab + `var(--*)`, NO new HEX/oklch); MHist; `check:mockup-fidelity` baseline unchanged

### 2.x Day-2 drift
- (record any `tsc -b` / codegen / typing surprises here, e.g. a stale fixture constructing an event without the new field — the 57.100 D-DAY2-1 pattern)

---

## Day 3 — Tests + full regression + drive-through (US-6) + CHANGE-068 + design note 26

### 3.1 Tests (US-1..US-5)
- [ ] **backend inbox-drain** — `test_inbox_drain.py`: a stub `MessageInbox` returns a message on the 2nd drain → appears in `messages` before turn 2's LLM call + a `MessageInjected` event yielded + the between-turns guardrail saw it; `message_inbox=None` → no change (existing loop tests green)
- [ ] **backend injection-registry** — `test_injection_registry.py`: register/put/drain/unregister; `put` on an unregistered session rejected; autouse reset fixture (Risk Class C)
- [ ] **backend inject-endpoint** — `test_inject_endpoint.py` (or extend router tests): 202 active+owned; 404 cross-tenant; 409 not-running
- [ ] **backend parity** — `test_event_wire_schema_parity.py` (count 24 + `MessageInjected` instance) passes
- [ ] **backend sse** — `MessageInjected(text="x")` → `{"type":"message_injected","data":{"text":"x"}}`
- [ ] **frontend parity** — `eventSchema.generated.test.ts` green (regenerated; count 24)
- [ ] **frontend chatStore** — `chatStore.mergeEvent.test.ts` +`message_injected` → `UserTurn(injected:true, text)`
- [ ] **frontend InputBar** — NEW: mid-run send → `inject` called (not `send`); idle send → `send`; textarea interactable during a run
- [ ] **existing chat-v2 contracts** — run/resume/approval flows preserved (inject is additive)

### 3.2 Full gate sweep
- [ ] **Full backend pytest green (NET delta documented)** — `-m "not real_llm"`; baseline → +N (0 deletions)
- [ ] **mypy 0 + run_all 10/10 + format chain** — mypy `src` 0; run_all 10/10 (`check_event_schema_sync` + `check_ap1` + `check_llm_sdk_leak` green); black/isort/flake8 **FULL `src tests`** clean — run INDEPENDENTLY (the 57.98 lesson — full-scope `black --check`)
- [ ] **Frontend gate** — `npm run lint` (no `--silent`) clean + `npm run build` exit 0 + `npm run check:mockup-fidelity` baseline unchanged + `npm run test` (Vitest +N)

### 3.3 Drive-through (US-6 — mid-run injection picks up + guardrail-on-injected)
- [ ] **Clean backend restart (Risk Class E)** — kill the `--reload` reloader + the `multiprocessing.spawn` worker (`Win32_Process` PID/PPID/StartTime + `Stop-Process -Force`); verify :8000 FREE + node :3007 untouched; start a fresh process (the new `/inject` route + the inbox wiring are startup-constructed); restore the normal `--reload` backend after
- [ ] **Drove a multi-turn run → mid-run inject → next turn picks up** — real UI (jamie@acme.com/acme-prod) + real backend + real Azure: a tool-using investigation (≥3 turns) → mid-run type "also check the database connection pool" → inject → the NEXT turn acknowledges + incorporates it + the injected `UserTurn(injected)` appears in the timeline (the tag); screenshots + observed-vs-intended in progress.md
- [ ] **Drove the guardrail-on-injected case** — inject a between-turns-guardrail-tripping instruction → the guardrail acts (pause/block) on the injected content; screenshot + observed-vs-intended
  - NOTE honest artifacts (if the multi-turn run can't be forced to ≥3 turns cleanly, or the injection timing is hard to land — record exactly what happened; NOT claimed "gate-only")

### 3.4 CHANGE-068 + design note 26 + 17.md
- [ ] `claudedocs/4-changes/feature-changes/CHANGE-068-between-turns-injection-primitive.md` written
- [ ] **design note 26** — `26-between-turns-injection-design.md` extracted from the real impl; 8-point quality gate (file:line / decision matrix — module registry vs per-request mailbox / verified invariants / 17.md cross-ref / open invariants — TEAMMATE B2 / rollback / refs / MHist)
- [ ] **`17-cross-category-interfaces.md`** — register `MessageInbox` (Cat 1, `drain`) + `message_injected` (Cat 12 wire) + note the loop drains before the Cat 9 between-turns guardrail

---

## Day 4 — Closeout (new-domain spike — design note 26)

### 4.1 Closeout
- [ ] Full validation (parent re-verified): backend pytest (baseline → +N, 0 deletion) / mypy `src` 0 / run_all 10/10 / black FULL `src tests` clean / frontend Vitest (+N) + lint(no `--silent`) + build exit 0 + check:mockup-fidelity unchanged / `mailbox.py`+`TeammateExecutor`+`resume()`+DB+`ModelProfile`+`HITLTurn.tsx` diff = 0 / **drive-through PASS** (mid-run inject → next turn picks up + injected UserTurn; + guardrail-on-injected; artifacts)
- [ ] progress.md (Day 0-3) + retrospective.md (Q1-Q7) + design-note-extract self-check record (8-point gate)
- [ ] Calibration: `loop-injection-primitive-spike` 0.55 (NEW class, 1st pt) + `agent_factor` 1.0 (parent-direct); recorded `calibration-log.md §3` + `sprint-workflow.md §Scope-class matrix` row; carryover (B2 TEAMMATE) → next-phase-candidates.md
- [ ] MEMORY.md pointer + `project_phase57_101_*.md` subfile + CLAUDE.md lean (Current Sprint row + Last Updated) + CHANGE-068 + design note 26 + 17.md
- [ ] commit (Day 0-N) + push + PR (user-authorized)
