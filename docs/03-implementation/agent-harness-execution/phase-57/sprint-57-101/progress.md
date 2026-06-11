# Sprint 57.101 Progress — between-turns message injection primitive (B1)

**Plan**: [`../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-101-plan.md`](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-101-plan.md)
**Checklist**: [`../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-101-checklist.md`](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-101-checklist.md)
**Branch**: `feature/sprint-57-101-between-turns-injection` (from `main` `71336195`)

---

## Day 0 — Plan-vs-Repo Verify + Branch (2026-06-11)

### Recon method
A read-only 2-agent Explore recon (backend + frontend) mapped the real code on `main` post-57.100-merge `71336195`; the plan §0 ground-truth anchors come from it. Day-0 then personally re-read the load-bearing backend anchors (the `_run_turns` seam + the ctor + the wire schema) to confirm placement before code.

### Prong 1 (path) — confirmed
- `loop.py` `_run_turns` sig `:1944-1957` (re-enterable, shared by run()/resume() since 57.89/90/98/99); `while True:` @`:1983`; pre-LLM termination checks `:1984-2008`; **between-turns gate `:2010-2034`** (`_cat9_between_turns_check` @`:2022`, gated `turn_count > 0 and not skip_between_turns_once` @`:2020`, reads `messages`, `skip_between_turns_once = False` @`:2034`); compaction `:2036+`. Msg-append precedent `:2490-2493` (`messages.append(Message(role="user"/"assistant", content=…))`). Ctor `:373-431` (`verifier_registry` @`:420`, `verification_escalate_on_max` @`:430` = LAST param) + assigns `:432-483` (`self._verification_escalate_on_max` @`:483` = LAST).
- `_contracts/chat.py` `Message :75-96` (frozen; `role: Literal[...]`, `content: str | list[...]`, `metadata`); `_contracts/events.py` `LoopEvent` base + subclasses.
- `event_wire_schema.py` `WIRE_SCHEMA` = **23 entries** (`:30` + `:77` comments say "23"; the `:40` MHist line "22 unchanged" is STALE — see D-DAY0-1). `test_event_wire_schema_parity.py:142` `assert len(WIRE_SCHEMA) == 23`.
- `sse.py` approval serializer branch (`:229-238` per recon); `router.py` chat POST `:148-350` (SessionRegistry `register(tenant, session_id)` @`:273-274`) + resume `:832-886` + `_stream_resume_events :807-829`; `session_registry.py get_default_registry()`; `handler.py build_real_llm_handler :247-259` + `build_handler :514-572`; `subagent/mailbox.py :46-100` (per-request — B2 ref only).
- FE: `InputBar.tsx` `:77-82` send guard + `:162-170` textarea (`disabled={isRunning}` @`:169`) + Stop button `:178-188`; `chatService.ts streamChat :64-92` / `resumeChat :107-131` / `consumeSSEStream :140+`; `useLoopEventStream.ts send :60-92` / `resume :98-120` / `isRunning :127`; `chatStore.ts mergeEvent :298-620` (`approval_requested :454-491`); `types.ts UserTurn :123-128`; `loopEvents.generated.ts` (KNOWN_LOOP_EVENT_TYPES set); tests `chatStore.mergeEvent.test.ts` + `eventSchema.generated.test.ts`.

### Prong 2 (content) — confirmed
- The between-turns gate reads `messages` (`:2023`) → **draining + appending BEFORE the gate (at `:2009`, after the termination checks) means injected content is in `messages` when `_cat9_between_turns_check` runs** → free Cat 9 check (the proposal's design). The drain itself runs every iteration (gated only on `self._message_inbox is not None`, NOT on `turn_count`), so an injection during turn N lands at the N→N+1 boundary.
- ctor DI: `message_inbox: "MessageInbox | None" = None` goes after `verification_escalate_on_max` (`:430`); `self._message_inbox = message_inbox` after `:483`; guard `if self._message_inbox is None: <skip drain>` mirrors `:1293` (`if self._guardrail_engine is None: return`).
- `Message(role="user", content=<str>)` is the append shape (matches `:2492`).
- `event_wire_schema.py` insertion order = generated declaration order → **append `"message_injected"` at the END of WIRE_SCHEMA** for a clean codegen diff (no reorder of existing entries). `sse.py` serializer reads `event.<field>` → `event.text` works.
- `resume()` shares `_run_turns`; inject-during-pause is OUT of scope (the loop is paused, not running → the inject endpoint returns 409). On a resume the loop's `message_inbox` is None/empty → `drain()` returns `[]` → no behavior change. No run/resume interaction.

### Prong 2.5 (frontend tree) — confirmed
- The PRODUCTION composer is `InputBar.tsx` (NOT `Composer.tsx`, which is mockup-only disabled scaffolding `:50-56`, unused by `chat-v2/index.tsx`). The two guards to change: textarea `disabled={isRunning}` (`:169`) + the send guard `if (!trimmed || isRunning) return;` (`:79`). The Stop button (`:178-188`) stays.
- The injected-message tag + the inject affordance have NO mockup source (`page-chat.jsx` has no mid-run inject / injected-user-turn) → reuse mockup `.btn`/`.user-turn` vocab + `var(--*)` tokens, no new HEX/oklch (`check:mockup-fidelity` baseline must stay unchanged).
- `chatStore.mergeEvent.test.ts` + `eventSchema.generated.test.ts` EXIST → **EXTEND** (the 57.100 D-DAY0-2 lesson). NO InputBar component test exists → **NEW**.

### Prong 3 (schema) — N/A confirmed
- No DB/migration/ORM (the inbox is in-memory, per-run). The wire change is a NEW event TYPE → `len(WIRE_SCHEMA)` 23→24 + `test_event_wire_schema_parity.py:142` `== 24` + the WIRED_EVENT_INSTANCES set + the doc count comments (`event_wire_schema.py :30` + `:77`; `_contracts/events.py` subclass comment). `check_event_schema_sync` re-greens after regen.

### Drift findings
- **D-DAY0-1 (count is 23, not 22)** — The event count is **23** (Sprint 57.96 added `subagent_child` 22→23). The `event_wire_schema.py:40` MHist line "no new wire-type; 22 unchanged" is a STALE marker (the `:30`/`:77` body comments correctly say 23). Implication: B1 bumps **23→24** (not 22→23); the parity assertion `:142` `== 23` → `== 24`. The plan/checklist already use 23→24 throughout — no scope shift; this just locks the number. I update the `:30`/`:77` count comments to 24 (files I edit); the stale `:40` historical MHist line is left (newest-first; I add a 57.101 line).
- **D-DAY0-2 (drain placement + the turn-0 / resume edges)** — The drain goes at `:2009` (after the termination checks, before the between-turns gate). The between-turns Cat 9 check only runs when `turn_count > 0 and not skip_between_turns_once`, so: (a) an injection during turn 0 (the very first turn) would be drained at the turn-0→1 boundary where the gate DOES run → checked; an injection drained AT a `turn_count==0` iteration (loop just started, nothing realistically queued yet) appends un-between-turns-checked but is still subject to the downstream output/tool guardrails; (b) on a `skip_between_turns_once` resume re-entry the gate is skipped for that one iteration. Honest edge — documented in design note 26. No scope shift.
- **D-DAY0-3 (production composer = InputBar, not Composer)** — confirmed; the B1 target is `InputBar.tsx`'s two `isRunning` guards. `Composer.tsx` is dead mockup scaffolding (not touched).
- **D-DAY0-4 (tests exist → extend)** — `chatStore.mergeEvent.test.ts` + `eventSchema.generated.test.ts` extended, not created; `InputBar` test is new.

### Go/no-go
**GO.** Slice = the §4 file list, unchanged. Load-bearing decisions all confirmed against real code: drain at `_run_turns` `:2009` before the between-turns gate (free Cat 9 check); module-level `InjectionRegistry` bridges the separate inject-POST + run requests (a per-request mailbox cannot); render on the drain event (not optimistically). This is a larger slice than 57.98-100 (~10 hr committed); plan §7 STOP-and-rescope clause active if Day-1 ripples > 20% (split B1a backend / B1b frontend + re-confirm with user).

### Baseline (main `71336195`)
- mypy `src` **0/353** ✅ · pytest collect `-m "not real_llm"` **2304** ✅ · run_all **10/10** ✅ (check_event_schema_sync green). Frontend Vitest count + `check:mockup-fidelity` HEX_OKLCH baseline → captured Day 2/3 before the FE edits.

### Design-note decision
New-domain spike (NEW Cat 1 `MessageInbox` + NEW `_run_turns` drain seam + NEW `MessageInjected` wire type) → **design note 26** (`26-between-turns-injection-design.md`); UPDATE 17.md (`MessageInbox` Cat 1 + `message_injected` Cat 12). The 57.94/97/98 new-domain-spike precedent.

---

## Day 1 — The contract + loop drain + the `MessageInjected` wire event (US-1/US-2) (2026-06-11)

### Done
- **`_contracts/inbox.py`** (NEW) — `MessageInbox(ABC)` with `async def drain(self) -> list[Message]` (non-blocking; `[]` if none). Imports only `Message` → `check_llm_sdk_leak` clean. Exported via `_contracts/__init__.py` (+ `MessageInjected`).
- **`loop.py`** — ctor +`message_inbox: "MessageInbox | None" = None` (after `verification_escalate_on_max`, the LAST param) + `self._message_inbox` assign; `MessageInbox` imported under TYPE_CHECKING (annotation-only, mirrors the 57.98 `VerifierRegistry` pattern — avoids flake8 F401). `MessageInjected` added to the runtime `_contracts` import (it's yielded). **`_run_turns` drain seam**: after the 3 termination checks, BEFORE the between-turns gate — `if self._message_inbox is not None: for injected in await self._message_inbox.drain(): messages.append(injected); yield MessageInjected(text=<str-coerced injected.content>, trace_context=ctx)`. Drained BEFORE `_cat9_between_turns_check` reads `messages` → free Cat 9 check; fired on drain (proof it landed); `message_inbox=None` → no-op byte-identical.
- **`MessageInjected` wire event** — `_contracts/events.py` +`MessageInjected(LoopEvent)` (`text: str = ""`); `sse.py` +import +serializer branch (`{"type":"message_injected","data":{"text":event.text}}`); `event_wire_schema.py` +`"message_injected": {"text":"string"}` (appended at END) + count comments `:30`/`:77` 23→24; `generate_event_schemas.py` +`"message_injected": "MessageInjectedEvent"` interface map.
- **codegen regen** — clean: `events.json` +4, `loopEvents.generated.ts` +12/-1 = ONLY `MessageInjectedEvent` (interface w/ `trace_id?` + `text: string`, union member, KNOWN set entry); no spurious reformat; count 24.
- **`test_event_wire_schema_parity.py`** — `test_wire_schema_has_24_entries` (`== 24`) + a `MessageInjected(text="also check the db pool")` wired instance.

### Gates (Day 1)
- mypy `src` **0/354** (+1 = inbox.py) ✅
- parity test **33 passed** (+1) ✅
- `run_all` **10/10** ✅ — `check_event_schema_sync` in sync (codegen regenerated); `check_ap1` green (the drain is a `for … append + yield` data-flow at the loop top — the loop is still `while True` driven by stop_reason; NOT a fixed-step pipeline restructure); `check_llm_sdk_leak` green.

### Notes
- The `events.py` header "22 subclasses" prose was already stale before 57.96 (which added `SubagentChildEvent`) — left untouched (Karpathy §3; the gating count is the parity test's `len(WIRE_SCHEMA) == 24`, which is correct). Added a 57.101 MHist line only.

### D-DAY1-1 (the load-bearing drift — the "free between-turns guardrail check" claim was wrong)
The plan/proposal assumed draining BEFORE the between-turns guardrail means the injected content is Cat 9-checked "for free". Reading the real code disproved it: `_cat9_between_turns_check` checks `content = self._latest_output_text(messages)` (`loop.py:1311`), and `_latest_output_text` (`:1283-1285`) returns the last **assistant/tool** message — it **skips `role="user"` messages**. So a `role="user"` injection is NOT what the between-turns gate inspects (that gate gates CONTINUATION on the just-completed turn's OUTPUT, not on a new input).
- **Correct fix**: the injection is an INPUT → run the Cat 9 **INPUT** guardrail (`engine.check_input`) on each drained message. A non-PASS injection is **DROPPED** (not appended) + a `GuardrailTriggered(guardrail_type="input")` event tells the UI; the run continues without it (a bad side-instruction must not kill the main task). PASS → append + `MessageInjected`. NO pause-resume on a blocked injection (bounded — pause-on-injection is a follow-on).
- This is more faithful to the proposal's intent ("注入內容自動受 Cat 9 檢查") AND realizes the DoD "guardrail-on-injected case" honestly. Scope unchanged (still a drain seam; the check is one `check_input` call + a drop branch). The loop drain comment now documents this.

---

## Day 1 (cont) + Day 2 — The injection channel + the FE composer (US-3/US-4/US-5) (2026-06-11)

### Backend channel (US-3)
- **`api/v1/chat/injection_registry.py`** (NEW) — `InjectionRegistry` (module singleton via `get_default_injection_registry()`, tenant-scoped `dict[tenant_id, dict[session_id, asyncio.Queue[Message]]]` — mirrors `SessionRegistry`; a per-request mailbox cannot bridge the SEPARATE inject-POST + run requests): `register`/`put` (put_nowait, False if no live queue)/`drain` (get_nowait loop)/`unregister` (prunes empty tenant). `QueueMessageInbox(MessageInbox)` binds `(registry, tenant, session)` → the loop's drain view.
- **`router.py`** — at chat POST: register the injection queue (alongside the SessionRegistry register); in `_stream_loop_events`' `finally`: unregister (any exit path). NEW `POST /{session_id}/inject` (202): `Depends(get_current_tenant)` + active+owner gate via `SessionRegistry.get` (404 absent/cross-tenant — the 鐵律; 409 not-running; 409 if `put` finds no live queue) → `put(Message(role="user", content=body.message))`. `InjectRequestBody(message: str, min 1 / max 4096)` in `schemas.py`.
- **`handler.py`** — `build_real_llm_handler` constructs `QueueMessageInbox(get_default_injection_registry(), tenant_id, session_id)` + passes `message_inbox=` to the loop ctor (real_llm path; echo_demo is a deterministic 2-turn mock → no inbox, no dead-control on the FE side via mode-gating).

### Frontend (US-4/US-5)
- **`chatService.ts`** — `injectMessage(sessionId, message)`: plain POST `/{id}/inject` (NOT an SSE stream — the ALREADY-OPEN run stream delivers `message_injected` on drain); throws on non-2xx.
- **`useLoopEventStream.ts`** — `inject(text)`: only valid while `status==="running"` + a sessionId; `injectMessage(...)`; an inject failure surfaces via `setError` but does NOT change status (the run is unaffected).
- **`InputBar.tsx`** — composer usable mid-run for **real_llm only** (`canInject = isRunning && mode==="real_llm"` — echo_demo is a scripted mock that can't act on a mid-run note → gating avoids a dead control per the Drive-Through rule): the textarea is enabled (`disabled={isRunning && !canInject}`), `onSend` routes a running send to `inject()` (else `send()`), and a clearly-labelled **Inject** button (`data-testid="inject-send"`) sits next to Stop. Placeholder switches to "Add an instruction for the running agent…" when injectable.
- **`types.ts`** — `UserTurn` +`injected?: boolean`.
- **`chatStore.ts`** — `message_injected` case → append a `UserTurn(injected: true)` (rendered on the drain event, not optimistically).
- **`UserTurn.tsx`** — an "injected mid-run" tag (`data-testid="injected-tag"`) reusing the existing `.route-pill` class (no new HEX/oklch → `check:mockup-fidelity` baseline unchanged).

### Tests (US-1..US-5)
- **`test_inbox_drain.py`** (NEW, 3) — injection lands at the NEXT turn boundary (turn N+1's request, not N's) + `MessageInjected` fires; `message_inbox=None` → no-op; a `check_input`-BLOCKed injection is DROPPED + `GuardrailTriggered(input,block)` + never reaches the LLM + the run still completes.
- **`test_injection_registry.py`** (NEW, 9) — register/put/drain/unregister + FIFO + cross-tenant put rejected + two-tenants-same-sid independence + empty-tenant prune + `QueueMessageInbox` delegation.
- **`test_router.py` `TestInjectEndpoint`** (NEW, 6) — 202+queued / 404 missing / 404 cross-tenant / 409 completed / 409 no-live-queue / 422 empty; sync seeding by direct dict (avoids the cross-loop lock bind; `put_nowait`/`get_nowait` are loop-agnostic) + a `_reset_injection_registry` autouse fixture (Risk Class C).
- **`test_sse.py`** +`test_message_injected` (the wire frame).
- **`test_event_wire_schema_parity.py`** — count 24 + a `MessageInjected` instance.
- **Frontend**: `eventSchema.generated.test.ts` (24 + message_injected recognition); `chatStore.mergeEvent.test.ts` (message_injected → `UserTurn(injected)`); `InputBar.test.tsx` (NEW, 3 — idle→send / running-real_llm→inject + textarea enabled / running-echo→disabled + no Inject button).

### Gates (Day 1-cont + 2 + 3 partial)
- Backend: mypy `src` **0/355** (+2 = inbox.py + injection_registry.py) · flake8 `src tests` clean · `run_all` **10/10** · targeted suites green (chat api + loop + inbox + registry + router = 199 + 12 + 19 passed earlier). Full suite NET delta → recorded on the background run's completion.
- Frontend: `npm run build` ✅ (tsc — `demoLoopEvents.ts` needed NO change since `message_injected` is a NEW type, not a required field) · Vitest **787 passed** (+5) · `check:mockup-fidelity` **53 unchanged** · `npm run lint` exit 0 (no `--silent`).
