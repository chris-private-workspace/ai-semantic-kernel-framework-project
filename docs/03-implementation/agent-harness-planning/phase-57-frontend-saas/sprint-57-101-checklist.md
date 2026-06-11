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
- [x] plan + checklist + progress committed (Day-0 commit `a7ec1951`)

---

## Day 1 — The `MessageInbox` contract + loop drain seam + the `MessageInjected` event (US-1/US-2)

### 1.1 The contract + loop drain
- [x] **`_contracts/inbox.py`** — NEW `MessageInbox(ABC)` (`async def drain(self) -> list[Message]`); imports only `Message`; file header; `check_llm_sdk_leak` 0 ✅; exported via `_contracts/__init__.py` (+ `MessageInjected`)
- [x] **`loop.py` ctor** — +`message_inbox: "MessageInbox | None" = None` (after `verification_escalate_on_max`, LAST param `:430`); `self._message_inbox` assign; `MessageInbox` under TYPE_CHECKING (annotation-only, like `VerifierRegistry`); MHist 1-line ✅
- [x] **`loop.py` `_run_turns` drain seam** — at the top of the `while` body (after the 3 termination checks, BEFORE the between-turns gate); each drained message runs the Cat 9 **INPUT** guardrail (`engine.check_input`) — **D-DAY1-1 correction**: the between-turns gate checks turn OUTPUTS (`_latest_output_text` skips user msgs), so a user injection needs `check_input`, not the between-turns gate; a non-PASS injection is DROPPED + `GuardrailTriggered(input)` (run continues), PASS → `messages.append` + `yield MessageInjected(text, trace_context=ctx)`; `message_inbox=None` byte-identical; MHist 1-line; mypy `src` **0/355** ✅

### 1.2 The `MessageInjected` wire event + codegen
- [x] **`_contracts/events.py`** — +`MessageInjected(LoopEvent)` (`text: str = ""`) in a Cat 1 mini-section; MHist ✅ (the "22 subclasses" header prose was already stale pre-57.96 — left, not chased per Karpathy §3)
- [x] **`api/v1/chat/sse.py`** — +`MessageInjected` import + serializer branch → `{"type":"message_injected","data":{"text":event.text}}` ✅
- [x] **`api/v1/chat/event_wire_schema.py`** — +`"message_injected": {"text":"string"}` (appended at END for clean diff); count comments `:30`+`:77` 23→24; MHist ✅
- [x] **`scripts/codegen/generate_event_schemas.py`** — +`"message_injected": "MessageInjectedEvent"` in `WIRE_TYPE_TO_INTERFACE` ✅
- [x] **codegen regen** — `python scripts/codegen/generate_event_schemas.py` → `events.json` (+4) + `loopEvents.generated.ts` (+12/-1) regenerated; `git diff` = ONLY `message_injected` added (new `MessageInjectedEvent` interface w/ `text: string` + union member + KNOWN set entry; count 24); no spurious reformat ✅
- [x] **`test_event_wire_schema_parity.py`** — `test_wire_schema_has_24_entries` `== 24` + `MessageInjected(text="also check the db pool")` wired instance; **33 passed** (+1) ✅
- [x] **backend lint/type** — mypy `src` **0/354**; `check_event_schema_sync` in sync; `run_all` **10/10** (`check_ap1` green = drain is data-flow not a pipeline restructure; `check_llm_sdk_leak` green) ✅

---

## Day 2 — The injection channel + API + the FE composer-mid-run + render (US-3/US-4/US-5)

### 2.1 The InjectionRegistry + inject endpoint (US-3)
- [x] **`api/v1/chat/injection_registry.py`** — NEW `InjectionRegistry` (module singleton, **tenant-scoped** `dict[tenant, dict[session, asyncio.Queue[Message]]]` — mirrors SessionRegistry): `register`/`put`(put_nowait)/`drain`(get_nowait loop)/`unregister`(prune) + `get_default_injection_registry()`; `QueueMessageInbox(MessageInbox)` binds `(registry, tenant, session)`; file header; `check_llm_sdk_leak` 0 ✅
- [x] **`router.py` register/unregister** — at chat POST (after `:273-274` SessionRegistry register) `get_default_injection_registry().register(current_tenant, session_id)`; in `_stream_loop_events` `finally` `unregister(...)` (any exit path); MHist ✅
- [x] **`router.py` `POST /{session_id}/inject`** — `InjectRequestBody(message: str, min 1 / max 4096)` in schemas.py; `Depends(get_current_tenant)`; active+owner via `SessionRegistry.get` (404 absent/cross-tenant / 409 not-running / 409 no-live-queue); `put(current_tenant, session_id, Message(role="user", content=body.message))`; 202 `{"status":"queued"}`; MHist ✅
- [x] **`handler.py`** — construct `QueueMessageInbox(get_default_injection_registry(), tenant_id, session_id)` + pass `message_inbox=` to the loop (real_llm path); MHist; mypy `src` 0/355 ✅

### 2.2 The composer usable mid-run + inject client (US-4)
- [x] **`chatService.ts`** — +`injectMessage(sessionId, message)` POST `/{id}/inject` body `{message}` (plain POST, not SSE; throws non-2xx); MHist ✅
- [x] **`useLoopEventStream.ts`** — +`inject(text)` (only while running+sessionId; failure → setError, NOT status change) → `injectMessage`; returned alongside `send`/`resume`/`cancel`/`isRunning`; MHist ✅
- [x] **`InputBar.tsx`** — composer usable mid-run for **real_llm only** (`canInject = isRunning && mode==="real_llm"` — echo_demo scripted mock → gating avoids a dead control); textarea `disabled={isRunning && !canInject}`; `onSend` routes running send → `inject()` else `send()`; labelled **Inject** button (`data-testid="inject-send"`) next to Stop; placeholder switches when injectable; MHist ✅

### 2.3 The injected message renders (US-5)
- [x] **`types.ts`** — `UserTurn` +`injected?: boolean`; MHist ✅
- [x] **`chatStore.ts`** — +`message_injected` case → append `UserTurn {role:"user", id, at, text: ev.data.text, injected:true}` (on drain, not optimistic); MHist ✅
- [x] **the `UserTurn` render** (`turns/UserTurn.tsx`) — when `turn.injected`, an "injected mid-run" tag (`data-testid="injected-tag"`) reusing `.route-pill` (NO new HEX/oklch); MHist; `check:mockup-fidelity` **53 unchanged** ✅

### 2.x Day-2 drift
- **D-DAY1-1** (the load-bearing one — backend): the "free between-turns guardrail check" claim was wrong (`_latest_output_text` skips user msgs) → switched to `check_input` + drop-on-not-PASS (progress.md Day-1). No FE/scope shift.
- **D-DAY2-1**: NO stale-fixture `tsc` break — `message_injected` is a NEW event type (not a required field on an existing one, unlike 57.100's `kind`), so `demoLoopEvents.ts` + other `LoopEvent[]` fixtures need NO change; `npm run build` green first try.

---

## Day 3 — Tests + full regression + drive-through (US-6) + CHANGE-068 + design note 26

### 3.1 Tests (US-1..US-5)
- [x] **backend inbox-drain** — `test_inbox_drain.py` (3): injection lands at the NEXT boundary (turn N+1's request) + `MessageInjected`; `message_inbox=None` → no-op; a `check_input`-BLOCKed injection DROPPED + `GuardrailTriggered(input,block)` + never reaches the LLM + run completes ✅
- [x] **backend injection-registry** — `test_injection_registry.py` (9): register/put/drain/unregister + FIFO + cross-tenant put rejected + 2-tenants-same-sid + prune + `QueueMessageInbox` delegation ✅
- [x] **backend inject-endpoint** — `test_router.py::TestInjectEndpoint` (6): 202+queued / 404 missing / 404 cross-tenant / 409 completed / 409 no-live-queue / 422 empty; `_reset_injection_registry` autouse (Risk Class C) ✅
- [x] **backend parity** — `test_event_wire_schema_parity.py` count 24 + `MessageInjected` instance (33 passed) ✅
- [x] **backend sse** — `test_sse.py::test_message_injected` → `{"type":"message_injected","data":{"text":...}}` ✅
- [x] **frontend parity** — `eventSchema.generated.test.ts` (24 + message_injected recognition) ✅
- [x] **frontend chatStore** — `chatStore.mergeEvent.test.ts` +`message_injected` → `UserTurn(injected:true, text)` ✅
- [x] **frontend InputBar** — `InputBar.test.tsx` (NEW, 3): idle→`send` / running-real_llm→`inject` + textarea enabled / running-echo→disabled + no Inject button ✅
- [x] **existing chat-v2 contracts** — run/resume/approval flows preserved (inject additive; Vitest 787 all green) ✅

### 3.2 Full gate sweep
- [x] **Full backend pytest green (NET delta documented)** — `-m "not real_llm"`: **2320 passed + 4 skipped** (baseline 57.100 = 2300p+4s → **+20 passed, 0 deletions**: inbox-drain 3 + injection-registry 9 + inject-endpoint 6 + sse 1 + parity 1); 98.9s clean. **Infra note**: the dev infra (Docker Postgres/Redis/RabbitMQ) was DOWN at session start (all ports free) → integration tests timed out ~104s/file on the dead DB (looked like a hang); `docker compose -f docker-compose.dev.yml up -d` restored it (postgres healthy, 44 tables) → admin_tenant_patch 104s+7fail → 1.5s+9pass; B1 unit tests were green throughout (218 passed in isolation). ✅
- [x] **mypy 0 + run_all 10/10 + format chain** — mypy `src` **0/355** ✅; run_all **10/10** (`check_event_schema_sync` + `check_ap1` + `check_llm_sdk_leak` green) ✅; black/isort/flake8 **FULL `src tests`** clean (independent) ✅ (final FULL `black --check` re-run at Day-3 close)
- [x] **Frontend gate** — `npm run lint` (no `--silent`) exit 0 + `npm run build` exit 0 + `npm run check:mockup-fidelity` **53 unchanged** + `npm run test` **787** (+5) ✅

### 3.3 Drive-through (US-6 — mid-run injection picks up + guardrail-on-injected) ✅ BOTH PASS
- [x] **Clean backend (Risk Class E)** — N/A clean: :8000 was FREE at start (no stale backend / no `--reload` worker to kill) → started a fresh backend (PID 2520); node :3007 (PID 5620) is the frontend; the new `/inject` route + inbox wiring are startup-constructed on this fresh process ✅
- [x] **Case A — mid-run inject → next turn picks up** ✅ — real UI (jamie@acme.com/acme-prod) + real Azure **gpt-5.2**: an autonomous tool-using run (incident_list→incident_get→correlation_analyze) → mid-run injected "check the database connection pool health for the checkout service" → landed at the next boundary as a `UserTurn(injected)` with the **"injected mid-run" tag** → **turn 8 the agent called `mock_patrol_check_servers` scope=["checkout","db-01",…]** + the final summary had an explicit "Checkout DB connection pool health:" section. `artifacts/dt57101-A-*.png` + progress.md Day-3
- [x] **Case B — guardrail-on-injected (dropped)** ✅ — injected "…approval required before you touch any production database…" mid-run → the Cat 9 INPUT guardrail (`check_input`, phrase `{"approval required"}`) caught it → **DROPPED** (no user turn; `approvalAsUserTurn=false`) + Loop visualizer shows **`guardrail_triggered input→escalate`** → run continued + completed (end_turn). `artifacts/dt57101-B-*.png` + progress.md Day-3
  - Honest timing note: the first attempt's run was too fast (2 turns) to inject into; a forceful autonomous-multi-tool prompt + injecting immediately after send (no intermediate snapshot) gave the ~15s runway. Real-LLM UI-timing, not a code issue. NOT claimed "gate-only" — both cases observed live.

### 3.4 CHANGE-068 + design note 26 + 17.md
- [x] `claudedocs/4-changes/feature-changes/CHANGE-068-between-turns-injection-primitive.md` written (status ✅ Completed)
- [x] **design note 26** — `26-between-turns-injection-design.md` extracted from the real impl; 8-point quality gate (file:line / decision matrix — module registry vs per-request mailbox + D-DAY1-1 input-check vs between-turns-check / verified invariants / 17.md cross-ref / open invariants — TEAMMATE B2 / rollback / refs / MHist) ✅
- [x] **`17-cross-category-interfaces.md`** — registered `MessageInbox` (Cat 1, `drain`) §2.1 + `message_injected` (Cat 1 event) §4.1 ✅

---

## Day 4 — Closeout (new-domain spike — design note 26)

### 4.1 Closeout
- [x] Full validation (parent re-verified): backend pytest **2320 passed + 4 skipped** (+20, 0 deletion) / mypy `src` **0/355** / run_all **10/10** / black FULL `src tests` clean (660) / frontend Vitest **787** (+5) + lint(no `--silent`) exit 0 + build exit 0 + check:mockup-fidelity **53 unchanged** / `mailbox.py`+`TeammateExecutor`+`resume()`+DB+`ModelProfile`+`HITLTurn.tsx` diff = 0 / **drive-through BOTH cases PASS** (Case A mid-run inject → agent checks checkout db pool + injected UserTurn tag; Case B "approval required" → dropped + `guardrail_triggered input→escalate`; artifacts dt57101-{A,B}.png) ✅
- [x] progress.md (Day 0-3 + infra incident + drive-through) + retrospective.md (Q1-Q7 + 8-point gate self-check) ✅
- [x] Calibration: `loop-injection-primitive-spike` 0.55 (NEW class, 1st pt) + `agent_factor` 1.0 (parent-direct); recorded `sprint-workflow.md §Scope-class matrix` row; carryover (B2 TEAMMATE) → next-phase-candidates.md ✅ (calibration-log §3 entry pending — folded into the closeout commit)
- [x] MEMORY.md pointer + `project_phase57_101_between_turns_injection.md` subfile + CLAUDE.md lean (Current Sprint row + Last Updated) + CHANGE-068 + design note 26 + 17.md ✅
- [x] commit (Day 0-N) + push + PR — 4 commits (`a7ec1951` Day-0 / `79439604` Day-1 / `ad2f1388` Day-2/3 / `8d7e1514` Day-3 drive-through + Day-4 closeout); pushed + **PR #275** opened ✅
