# Sprint 57.100 — Checklist (chat-v2 verification-reject UI — the A2 follow-up: surface the pause `kind` on the `approval_requested` wire so chat-v2 HITL can REJECT-with-a-coaching-note → resume the verification ESCALATE pause for one human-coached turn)

**Plan**: [`sprint-57-100-plan.md`](./sprint-57-100-plan.md)
**Created**: 2026-06-10
**Status**: Draft — Day-0 verify in progress

> Rule: only `[ ]` → `[x]`; never delete unchecked items; defer with `🚧 + reason`.
> **Feature-continuation** (completes the 57.99 A2 leg's reviewer UI — reuses the shipped `resume()` `kind="verification"` + `ApprovalDecision.reason` + the inline `VerificationBlock`) → **NO new design note** (`sprint-workflow.md §Step 5.5`, the 57.91-93/99 precedent). Record = CHANGE-067 + **update 17.md** (the `approval_requested` wire gains `kind`) + **25.md §4** (the A2 reviewer UI → SHIPPED). Gate = full backend pytest + frontend Vitest green (NET delta) + **drive-through PASS** (the REJECT half — a forced-fail judge → escalate pause → coaching note → Reject → the loop re-answers with the coaching). Load-bearing decision: add `kind` to the `approval_requested` wire (additive field, NOT a new event type) — the event-ordering inference alternative is a rejected Potemkin heuristic. Out: rich verification card (the `VerificationBlock` already shows the reason), per-tenant policy (C3), multi-round coaching, the `ApprovalCard.tsx` fallback, 4-action UX.

---

## Day 0 — Plan-vs-Repo Verify + Branch

### 0.1 Three-prong Day-0 verify
- [x] **Prong 1 (path)**: re-confirmed all anchors on `a890bb15` — `sse.py :229-238` (request_id+risk_level only) · `events.py ApprovalRequested :399-403` (no kind) · `loop.py` 5 yield sites `:814`/`:1030`/`:1433`/`:1596`/`:1812` + 5 `_emit_deferred_pause` `:825`/`:1061`/`:1444`/`:1608`/`:1824` · `event_wire_schema.py :119-122` · codegen + parity tests + lint · `governanceService.decide :71-83` (reason arg ✅) · `useLoopEventStream.resume :98-120` · `HITLTurn.tsx :106-141` (approve-only resume; meta `:186-191`) · `types.ts :146-158` · `chatStore.ts :453-487` + `verification_failed VerificationBlock :608-633`. (progress.md Day-0 Prong 1)
- [x] **Prong 2 (content)**: confirmed — emit-site `kind` literals from `pending_approval["kind"]` (`:821` input / `:1052` tool / `:1440` between_turns / `:1603` output / `:1819` verification); `_emit_deferred_pause` has NO `kind=` param (kind lives in `pending_approval`) → set `kind=` at the YIELD site; `sse.py` reads `event.<field>` (so `event.kind` works); schema vocab `"string"` matches; codegen nested `{type,data}` → `ApprovalRequestedEvent.data` gains `kind`; `chatStore` narrows on `ev.type` → `ev.data.kind` typed post-regen; `decide(reason?)` + `resume()` need no change. (progress.md Day-0 Prong 2)
- [x] **Prong 2.5 (frontend tree)**: confirmed — `HITLTurn.tsx` canonical (not `ApprovalCard.tsx`); e2e contracts additive-safe; the note textarea has NO mockup source → mockup `.hitl-card`/input vocab + `var(--*)` (no new HEX/oklch); **D-DAY0-2**: tests EXIST (`HITLTurn.resume.test.tsx` + `chatStore.mergeEvent.test.ts` + `eventSchema.generated.test.ts`) → EXTEND, do not create. (progress.md Day-0 Prong 2.5)
- [x] **Prong 3 (schema)**: N/A confirmed — no DB/migration/ORM; the wire change is a FIELD on the EXISTING `approval_requested` type → NO event-count bump (22 stays 22); `check_event_schema_sync` stays green after regen. No new table/column/event-type/DTO.
- [x] **Baseline capture**: `main a890bb15` — mypy `src` **0/353** ✅ · pytest collect `-m "not real_llm"` **2303** ✅ · run_all **10/10** ✅ · frontend Vitest + `check:mockup-fidelity` HEX_OKLCH baseline (background run, recorded in progress.md)
- [x] **Design-note decision**: feature-continuation → NO new design note (the 57.91-93/99 precedent); plan to UPDATE 17.md (the `approval_requested` wire +kind) + 25.md §4 (the A2 reviewer UI → SHIPPED). Confirmed in progress.md.
- [x] **Forced-fail drive-through setup**: reuse the 57.99 env approach (`CHAT_VERIFICATION_MODE=enabled` + `CHAT_VERIFICATION_ESCALATE_ON_MAX=true` + strict `CHAT_VERIFICATION_JUDGE_TEMPLATE` + neutral "no tools, just re-answer" prompt — the 57.99 D-DAY3-2 lesson); cheap deployment (57.97) set
- [x] Catalogue Day-0/Day-1 drift in progress.md; **go/no-go = GO** (slice = `kind` wire field + codegen regen + verification-gated frontend reject-with-note; D-DAY0-1 = a literal-ordering correction, no scope shift; D-DAY0-2 = scope shrinks, extend not create; D-DAY0-3 = held answer/reason already rendered)

### 0.2 Branch
- [x] Branch `feature/sprint-57-100-chatv2-verification-reject-ui` from `main` (`a890bb15`)
- [ ] plan + checklist + progress committed (Day-0 commit)

---

## Day 1 — The `kind` wire field + codegen (US-1)

### 1.1 The event + emit sites
- [x] **`_contracts/events.py`** — `ApprovalRequested` +`kind: str = ""` (frozen dataclass field, optional default); MHist ✅
- [x] **`loop.py` 5 emit sites** — pass `kind=` (D-DAY0-1 corrected map): `:814`→`"input"` / `:1030`→`"tool"` / `:1433`→`"between_turns"` / `:1596`→`"output"` / `:1812`→`"verification"`; MHist. ✅ each `kind=` literal == its `pending_approval["kind"]` (`:821`/`:1052`/`:1440`/`:1603`/`:1819`); mypy `src` 0/353

### 1.2 The wire + schema + codegen
- [x] **`api/v1/chat/sse.py`** — `approval_requested` serializer +`"kind": event.kind`; MHist ✅
- [x] **`api/v1/chat/event_wire_schema.py`** — `"approval_requested"` entry +`"kind": "string"`; MHist ✅
- [x] **codegen regen** — `python scripts/codegen/generate_event_schemas.py` → `events.json` + `loopEvents.generated.ts` regenerated ✅ `git diff` = ONLY `approval_requested.kind` (events.json +`"kind": "string"`, `.ts` +`kind: string;` on `ApprovalRequestedEvent.data`); no spurious reformat; event count unchanged (22)
- [x] **backend lint/type** — mypy `src` **0/353** ✅; `check_event_schema_sync` **in sync** ✅; `test_event_wire_schema_parity.py` **32 passed** ✅

---

## Day 2 — The frontend capture + REJECT-with-note (US-2/US-3/US-4/US-5)

### 2.1 Capture `kind` (US-2)
- [x] **`chat_v2/types.ts`** — `HITLTurn` +`kind: string` (after `tool`); MHist ✅
- [x] **`chat_v2/store/chatStore.ts`** — the `approval_requested` case sets `kind: ev.data.kind ?? ""` on the `HITLTurn`; MHist ✅ (unit: kind capture + "" fallback in `chatStore.mergeEvent.test.ts`)

### 2.2 REJECT-with-coaching-note, verification-gated (US-3/US-4)
- [x] **`HITLTurn.tsx` state + gating** — `showNoteInput`/`rejectNote` state; `isVerification = turn.kind === "verification"`; `submitDecision(decision, note?)` passes `note` to `decide`; `shouldResume = approved || (rejected && isVerification)` guarded on `awaiting_approval`; MHist ✅
- [x] **Reject button behavior** — `isVerification` → Reject reveals the note input (`setShowNoteInput(true)`); else → submits `"rejected"` immediately (byte-identical); a "Reject & coach" confirm button (`reject-confirm-btn`, only when `showNoteInput`) submits `"rejected"` + `rejectNote` ✅ (D-DAY0-2: extended `HITLTurn.resume.test.tsx` — verification reveals textarea / confirm → decide(note)+resume / tool reject no resume + no textarea; existing assertions updated to 3-arg `decide(...,undefined)`)
- [x] **The note textarea** — `var(--radius-sm)`/`var(--border)`/`var(--bg-1)`/`var(--fg)` (all confirmed mockup tokens, NO invented colors); `aria-label="Coaching note"` + `data-testid="reject-note"`; optional placeholder ✅ `check:mockup-fidelity` HEX_OKLCH baseline **53 unchanged**

### 2.3 Kind-aware render (US-5)
- [x] **The meta row** — `isVerification` → `kind: verification` (mono, `var(--tool)`) instead of `tool: {turn.tool}`; otherwise unchanged; MHist ✅ (unit: "verification meta row reads 'verification'")

### 2.x Day-2 drift
- **D-DAY2-1**: `tsc -b` caught a demo fixture `orchestrator-loop/_fixtures/demoLoopEvents.ts:155` constructing `approval_requested` WITHOUT `kind` (now required) → added `kind: "tool"` (it's a high-risk-tool HITL demo). Build green after the fix. (The wire field being REQUIRED, not optional, surfaced the only stale construction site at compile time — exactly the type-safety we want.)

---

## Day 3 — Tests + full regression + drive-through (US-6) + CHANGE-067

### 3.1 Tests (US-1..US-5)
- [x] **backend sse-kind test** — `test_sse.py`: existing `test_approval_requested` +`assert kind==""` (default); NEW `test_approval_requested_carries_kind` (`kind="verification"` → wire `"kind":"verification"`) ✅ 31 passed
- [x] **backend parity** — `test_event_wire_schema_parity.py` **32 passed** (regenerated `approval_requested` +kind) ✅
- [x] **frontend parity** — `eventSchema.generated.test.ts` green (regenerated; in the Vitest 782) ✅
- [x] **frontend chatStore unit** — `chatStore.mergeEvent.test.ts` +2: `kind:"verification"` → `HITLTurn.kind==="verification"`; no-kind-on-wire → `""` ✅
- [x] **frontend HITLTurn unit** — `HITLTurn.resume.test.tsx` (D-DAY0-2: EXTENDED, not new): +3 verification cases (reveal textarea / confirm → `decide(id,"rejected",note)`+`resume` / meta reads "verification"); tool reject → `decide(id,"rejected",undefined)` + NO resume + NO textarea; existing approve assertions → 3-arg ✅
- [x] **existing e2e contracts** — `approval-card.spec.ts` (approval_id / HIGH / Decision / data-testids) preserved (additive change — reject-btn for non-verification still submits immediately; e2e fixtures unchanged) ✅ (not run here; contract preserved by design — verified at Vitest unit level)

### 3.2 Full gate sweep
- [x] **Full backend pytest green (NET delta documented)** — **2300 passed + 4 skipped** (`-m "not real_llm"`; baseline 2303 collect = 2299p+4s → +1: `test_approval_requested_carries_kind`; zero deletion) ✅
- [x] **mypy 0 + run_all 10/10 + format chain** — mypy `src` **0/353** ✅; run_all **10/10** (`check_event_schema_sync` green; SDK leak 0) ✅; black/isort/flake8 **FULL `src tests` (656 files)** clean — run INDEPENDENTLY (D-DAY3-1: `black --check` FULL scope caught 1 file — `test_sse.py`'s multi-line `ApprovalRequested(...)` → black collapsed to canonical 1-line; the 57.98 lesson applied) ✅
- [x] **Frontend gate** — `npm run lint` (no `--silent`) clean + `npm run build` exit 0 + `npm run check:mockup-fidelity` baseline **53 unchanged** + `npm run test` **782 passed** ✅

### 3.3 Drive-through (US-6 — the REJECT half)
- [x] **Clean backend restart (Risk Class E)** — killed the `--reload` reloader (3744) + `multiprocessing.spawn` worker (39976) via `Win32_Process` + `Stop-Process -Force`; verified :8000 FREE + node :3007 (6200) untouched; started a fresh NO-`--reload` process with the forced-fail judge env (`CHAT_VERIFICATION_MODE=enabled` + `_ESCALATE_ON_MAX=true` + a raw `CHAT_VERIFICATION_JUDGE_TEMPLATE` always-`{"passed":false}` — the `llm_judge.py` raw-template path); restored the normal `--reload` backend (PID 15720) after ✅
- [x] **Drove a verification fail → escalate → REJECT-with-note → re-answer** — real UI (jamie@acme.com/acme-prod) + real backend + real Azure gpt-5.2 + the forced-fail real-LLM judge: "What is the capital of France?" → 3 verification fails → A2 escalate pause → the HITL card shows **`kind: verification`** (the 57.100 wire field, NOT `tool: —`) + the inline `VerificationBlock` reasons → **Reject** reveals the coaching-note textarea (no submit yet) → typed a coaching note → **Reject & coach** → **Decision: REJECTED** + `resume()` → a NEW coached turn 6 re-answers **"The capital of France is Paris."** (followed the coaching) → judge force-fails again → **turn 6 `stop: verification_failed`** (bounded one turn, no 2nd escalate). Screenshots `artifacts/dt57100-{A,B}.png` + observed-vs-intended in progress.md Day-3 ✅
  - NOTE (honest forced-fail artifacts, NOT 57.100 behavior): the strict judge prompt tripped Azure's jailbreak filter on 2 judge calls (`judge_error` → fail-closed → escalate still fires); the forced-fail correction text drifted the un-coached answers (the coaching note pulled it back — the point of REJECT-with-note). NOT claimed "gate-only" — a real drive-through.

### 3.4 CHANGE-067 + 17.md + 25.md §4
- [x] `claudedocs/4-changes/feature-changes/CHANGE-067-chatv2-verification-reject-ui.md` written ✅
- [x] **`17-cross-category-interfaces.md`** — the `ApprovalRequested` row notes the wire +`kind` + the chat-v2 card REJECT branch ✅ (17.md is a registry table, no MHist section)
- [x] **`25-verification-in-loop-design.md` §4** — the A2 reviewer-facing UI (chat-v2 reject-with-note) → SHIPPED (with the `kind`-wire + `HITLTurn` branch detail); MHist ✅

---

## Day 4 — Closeout (feature-continuation — NO design note)

### 4.1 Closeout
- [x] Full validation (parent re-verified): backend pytest **2300 passed + 4 skipped** (baseline 2303 → +1, zero deletion) / mypy `src` **0/353** / run_all **10/10** / **black FULL `src tests` (656) clean** / frontend Vitest **782** (+5) + lint(no `--silent`) + build exit 0 + check:mockup-fidelity **53 unchanged** / `resume()`+`hitl.py`-DTO+`governanceService`+DB+`ApprovalCard.tsx`+`ModelProfile` diff = **0** / **drive-through PASS** (the REJECT half — escalate `kind: verification` → coaching note → Reject & coach → coached turn re-answers → bounded `verification_failed`; artifacts dt57100-{A,B}.png) ✅
- [x] progress.md (Day 0-3) + retrospective.md (Q1-Q7) ✅
- [x] Calibration: `frontend-feature-with-event-wire-addition` 0.55 (NEW class, 1st pt ~1.0 IN band) + `agent_factor` 1.0 (parent-direct); recorded `calibration-log.md §3` + `sprint-workflow.md §Scope-class matrix` row; carryover → next-phase-candidates.md ✅
- [x] MEMORY.md pointer + `project_phase57_100_*.md` subfile + CLAUDE.md lean (Current Sprint row + Last Updated) + CHANGE-067 + 17.md + 25.md §4 ✅
- [x] commit (Day 0-N) + push + PR (user-authorized) — 4 commits (`d2dd8cb6` Day-0 / `dccf6421` Day-1+2+3 / `174fb2ec` Day-3 drive-through / `dd5bb109` Day-4 closeout); pushed + **PR #274** opened ✅
