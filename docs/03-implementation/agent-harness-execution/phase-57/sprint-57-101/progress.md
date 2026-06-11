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
