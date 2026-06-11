# Sprint 57.100 Plan — chat-v2 verification-reject UI (the A2 follow-up: surface the pause `kind` on the `approval_requested` wire so chat-v2 HITL can REJECT-with-a-coaching-note → resume the verification ESCALATE pause for exactly one human-coached turn)

**Purpose**: Sprint 57.99 (A2) shipped the verification-ESCALATE backend: on max-attempts the loop pauses for a human; APPROVE delivers the held answer; **REJECT-with-note re-injects the reviewer note as a correction and runs exactly one human-coached turn** (`loop.py` `resume()` `kind="verification"`). The 57.99 drive-through proved the APPROVE half end-to-end through the real UI, but found the REJECT half is **not UI-drivable**: the chat-v2 HITL card (`HITLTurn.tsx`) was built for the tool-approval shape — APPROVE resumes (since 57.88), but REJECT is hardcoded to *terminate* (no resume, no note input), and the card cannot tell a verification pause from a tool pause because the `approval_requested` SSE wire carries only `approval_request_id` + `risk_level` — **no `kind`**. So a reviewer can SEE the escalate pause (the existing card renders) and can APPROVE, but cannot drive the REJECT-with-note coaching path the backend already supports. This slice closes that gap: (1) the load-bearing change is **adding `kind` to the `approval_requested` event + wire** (the `ApprovalRequest` already carries `kind` backend-side; the event just never surfaced it) so the frontend can distinguish a verification pause — event-ordering inference (treat-the-pause-as-verification-if-preceded-by-a-`verification_failed`) is a fragile Potemkin heuristic and is rejected; (2) the frontend captures `kind` and, **for `kind === "verification"` only**, the REJECT button reveals an optional coaching-note textarea → `governanceService.decide(id, "rejected", note)` → `resume()` (the backend coaches one bounded turn) + renders the pause kind-aware; (3) all other kinds (tool/input/between_turns/output) keep the current terminate-on-reject behavior **byte-identical** (the note input + resume-on-reject are verification-gated). This is a **feature-continuation** (it completes the 57.99 A2 leg's UI; the reviewer note rides the existing `ApprovalDecision.reason`; the held-answer + verifier reasons are already rendered by the existing chat-v2 `VerificationBlock`) → NO new design note (the 57.91-93/99 precedent); record = CHANGE-067 + update `17-cross-category-interfaces.md` (the `approval_requested` wire gains `kind`) + `25-verification-in-loop-design.md` §4 (the A2 reviewer-facing UI → SHIPPED). The wire change is **additive** (a new field on an existing event type, NOT a new event type → no 22→23 count bump; codegen regenerates the parity fixtures, `check_event_schema_sync` stays green).

**Category / Scope**: Frontend (chat-v2 HITL — `HITLTurn.tsx` gains a kind-aware REJECT-with-note path + a coaching-note input) × Cat 12 (Observability/wire — `ApprovalRequested` event + `event_wire_schema` gain `kind`; codegen regenerates the frontend schema) × Cat 9 (Guardrails/HITL — reuses the `ApprovalDecision.reason` field + `resume()` `kind="verification"`, both shipped in 57.99). Backend touch is **thin + additive**: `_contracts/events.py` (`ApprovalRequested` +`kind: str = ""`), `loop.py` (the 5 `ApprovalRequested(...)` emit sites pass their real `kind=`), `api/v1/chat/sse.py` (+`"kind"` in the `approval_requested` payload), `api/v1/chat/event_wire_schema.py` (+`"kind": "string"`), codegen regen. **No DB/migration** (no new persisted field — `kind` already lives in the persisted `ApprovalRequest`); **no new event type** (a field on the existing `approval_requested`); **no new DTO** (the note rides the existing `ApprovalDecision.reason`/`DecisionRequestBody.reason`, max 4096, shipped 57.99); **no backend resume change** (`resume()` `kind="verification"` already coaches — 57.99). Frontend: `chat_v2/types.ts` (`HITLTurn` +`kind`), `chat_v2/store/chatStore.ts` (capture `kind` from the wire), `chat_v2/components/turns/HITLTurn.tsx` (kind-aware REJECT-with-note + note input + render), `chat_v2/generated/loopEvents.generated.ts` (codegen regen). Phase 57.100

**Created**: 2026-06-10
**Status**: Draft (scope below; code execution gated on Day-0 GO — Day-0 Explore recon already run inline, findings in §0)
**Source**: Sprint 57.99 retrospective Q7 §1 (the chat-v2 verification-reject UI follow-up — the drive-through finding) + `claudedocs/1-planning/next-phase-candidates.md` (A2 carryover) + the 57.99 drive-through observed-vs-intended (APPROVE half UI-driven; REJECT half backend-unit-proven-only, `HITLTurn` reject = terminate + no note input).

> **Modification History**
> - 2026-06-10: Initial creation — chat-v2 verification-reject UI; add `kind` to the `approval_requested` wire (additive, all 5 emit sites backfilled); frontend captures `kind` + REJECT-with-note (coaching-note input + resume) gated on `kind === "verification"`; tool/input/between_turns/output reject byte-identical; no new event type / DB / DTO; feature-continuation → CHANGE-067, NO new design note, update 17.md + 25.md §4

---

## 0. Background

A2 (Sprint 57.99) made the verification ESCALATE pause real backend-side: `resume()` `kind="verification"` APPROVE delivers the held answer, REJECT-with-note re-injects `decision.reason` as a `user` correction `Message` + runs exactly one human-coached `_run_turns` turn (a 2nd failure terminates at `verification_failed`, bounded by the durable `verification_escalated` flag). The 57.99 drive-through (real UI + Azure gpt-5.2 + a forced-fail real-LLM judge) proved the APPROVE half: 3 fails → escalate pause → Approve → the held answer delivered + "Decision: APPROVED". But it surfaced the REJECT half is **not UI-drivable**: chat-v2's `HITLTurn` card (built 57.21, resume-on-approve added 57.88) hardcodes REJECT to terminate (no resume, no note input) and has no way to know the pause is a verification pause (vs a tool pause, where terminate-on-reject IS correct). That is this slice.

The right fix is the honest one: the pause `kind` already exists in the persisted `ApprovalRequest` (`"kind":"verification"` built by `_cat10_verification_escalate_pause`) but the `approval_requested` event never carried it to the wire. Surfacing it is additive (a field on an existing event), genuinely useful (every pause kind — tool/input/between_turns/output/verification — becomes distinguishable to the UI), and lets the frontend branch cleanly. The alternative (infer "this pause is verification" from a preceding `verification_failed` event in the stream) is a fragile ordering heuristic — a Potemkin signal that breaks the moment a tool pause follows a verification turn — and is rejected per `04-anti-patterns.md` AP-4.

### Ground truth (Day-0 head-start — Explore recon, file:line anchors)

A read-only recon mapped the real code on `main` (post-A2-merge `a890bb15`); Day-0 Prong 1/2/3 re-confirm these exactly:

- **The wire gap — `api/v1/chat/sse.py:229-238`.** The `ApprovalRequested` serializer emits `{"type":"approval_requested","data":{"approval_request_id":…,"risk_level":event.risk_level}}` — **no `kind`**. → add `"kind": event.kind`.
- **The event — `agent_harness/_contracts/events.py:399-403`.** `ApprovalRequested(LoopEvent)` has `approval_request_id: UUID | None = None` + `risk_level: str = ""` — **no `kind`**. → add `kind: str = ""` (frozen dataclass, optional default → all existing construction sites still build).
- **The 5 emit sites — `orchestrator_loop/loop.py`.** `yield ApprovalRequested(approval_request_id=request_id, risk_level=risk_level.value)` at `:814` (tool) / `:1030` (input) / `:1433` (between_turns) / `:1596` (output) / `:1812` (verification — the 57.99 escalate pause). Each site already knows its `kind` string (the same one it passes to `_emit_deferred_pause` / builds into `pending_approval`). → each gains `kind="<its kind>"`. Backfilling all 5 (not just verification) is free (one schema field covers all) + honest (the field reflects reality for every pause).
- **The wire schema source-of-truth — `api/v1/chat/event_wire_schema.py:119-122`.** `"approval_requested": {"approval_request_id": "string | null", "risk_level": "string"}`. → add `"kind": "string"`. (`approval_received` `:123`-ish is a separate entry — NOT touched; the reviewer note rides `decide()`'s body, not a wire event.)
- **The codegen — `scripts/codegen/generate_event_schemas.py`.** Reads `event_wire_schema.py` → regenerates `frontend/src/features/chat_v2/generated/loopEvents.generated.ts`. Parity guarded by `backend/tests/unit/api/v1/chat/test_event_wire_schema_parity.py` + `frontend/tests/unit/chat_v2/eventSchema.generated.test.ts` + the `scripts/lint/check_event_schema_sync.py` lint (in `run_all.py`). Adding a FIELD to an existing type does NOT bump the event count (22 stays 22) — only `approval_requested`'s field set changes. → run the generator; the parity fixtures regenerate; the lint stays green.
- **The reviewer note (reused, NO new DTO) — `governanceService.decide(requestId, decision, reason?, signal?)`** (`governance/services/governanceService.ts:71-83`) already POSTs `{decision, reason}`; the backend `DecisionRequestBody.reason` (max 4096) + `ApprovalDecision.reason` are wired (57.99). → the frontend just passes the coaching note as `reason`.
- **The resume (reused, NO change) — `useLoopEventStream.resume()`** (`chat_v2/hooks/useLoopEventStream.ts:98-120`) POSTs `resumeChat(sid)` (no args); the backend reads the stored decision+reason via `HITLManager.get_decision()` and runs the `kind="verification"` REJECT coaching turn (57.99). The continuation events merge into the same store. → the frontend calls `resume()` on a verification reject (today it only resumes on approve).
- **The card — `chat_v2/components/turns/HITLTurn.tsx:106-141`.** `submitDecision(decision)` → `decide(id, decision)` (NO reason) + optimistic `approval_received` merge + `if (decision === "approved" && stopReason === "awaiting_approval") await resume()`. The comment at `:128-129` states "we do not resume on reject" (correct for tool). → for `kind === "verification"`: REJECT passes the note as `reason` + also resumes (guarded on `awaiting_approval`); the `tool: {turn.tool}` meta row (`:186-188`) renders `kind: verification` instead of `tool: —`.
- **The HITLTurn type + store — `chat_v2/types.ts:146-158`** (`HITLTurn` has no `kind`; `tool: string`) + **`chat_v2/store/chatStore.ts:453-487`** (`approval_requested` builds the `HITLTurn` from `risk_level`+`approval_request_id`, sets `tool:"—"`, no `kind`). → `HITLTurn` gains `kind: string`; the store reads `ev.data.kind` (post-regen typed) into it (default `""` when absent → tool path unchanged).
- **The held answer + verifier reason are ALREADY rendered — `chat_v2/store/chatStore.ts:608-633`.** `verification_failed` → a `VerificationBlock` (claim = `reason`, evidence = `suggested_correction`) appended to the active agent turn. So the reviewer SEES *why* the answer failed inline, right above the escalate card → the approval card does NOT need to duplicate the reason onto the wire. (Day-1 drive-through confirms what is visible at the pause.)
- **This is a feature-continuation** (it completes the 57.99 A2 leg's reviewer UI; reuses `ApprovalDecision.reason` + `resume()` `kind="verification"`) → NO new design note (`sprint-workflow.md §Step 5.5` — the 57.91/92/93/99 precedent); record = CHANGE-067 + update 17.md (the `approval_requested` wire gains `kind`) + 25.md §4 (the A2 reviewer UI → SHIPPED).

---

## 1. Sprint Goal

Make the A2 verification REJECT-with-note path UI-drivable in chat-v2: (1) add `kind: str = ""` to the `ApprovalRequested` event (`_contracts/events.py`); the 5 `loop.py` emit sites pass their real `kind=` (tool/input/between_turns/output/verification); `sse.py` serializes `"kind"` into the `approval_requested` payload; `event_wire_schema.py` adds `"kind": "string"`; codegen regenerates `loopEvents.generated.ts` + the parity fixtures (no event-count bump). (2) `chat_v2/types.ts` `HITLTurn` gains `kind: string`; `chatStore.ts` reads `ev.data.kind` into it (default `""`). (3) `HITLTurn.tsx`: for `kind === "verification"` — the REJECT button reveals an optional coaching-note textarea (design-system-consistent — no mockup source for this new element, so mockup `.hitl-card`/`.btn`/input vocab is reused, not invented styling), and submitting it calls `decide(id, "rejected", note)` + `resume()` (guarded on `stopReason === "awaiting_approval"`); the meta row renders `kind: verification` instead of `tool: —`. ALL other kinds keep the current terminate-on-reject behavior **byte-identical** (no note input, no resume). Tests assert: the wire carries `kind`; the store captures it; a verification REJECT-with-note calls `decide` with the note + resumes; a tool REJECT does NOT resume + shows no note input; the wire parity holds (codegen). **Drive-through**: the REJECT half (the 57.99 drive-through did only APPROVE) — real UI + backend + Azure + a forced-fail judge → escalate pause → enter a coaching note → Reject → the loop re-answers with the reviewer's coaching in context (one bounded turn). Out of scope: a rich verification-specific approval card (held-answer/reason re-display — already covered by the existing `VerificationBlock`); per-tenant verification policy (C3); multi-round coaching (>1 turn — A2 bounds to one); the `ApprovalCard.tsx` fallback widget (legacy 53.5 path; this slice touches the canonical chat-inline `HITLTurn` only).

---

## 2. User Stories

- **US-1 (the `kind` wire field)** — As the chat-v2 UI, I want the `approval_requested` event to tell me what kind of pause this is, so I can render + behave correctly per kind. → `_contracts/events.py` `ApprovalRequested` +`kind: str = ""`; the 5 `loop.py` emit sites pass their real `kind=`; `sse.py` serializes `"kind"`; `event_wire_schema.py` +`"kind": "string"`; codegen regen (no event-count change).
- **US-2 (the frontend captures `kind`)** — As the chat-v2 store, I want to carry the pause kind on the HITL turn so the card can branch. → `chat_v2/types.ts` `HITLTurn` +`kind: string`; `chatStore.ts` `approval_requested` reads `ev.data.kind ?? ""` into the turn (default `""` = the legacy tool shape unchanged).
- **US-3 (REJECT-with-coaching-note, verification-gated)** — As the reviewer, I want to reject a verification escalate with a coaching note and have the loop try once more with my guidance. → `HITLTurn.tsx`: for `kind === "verification"`, clicking Reject reveals an optional note textarea + a confirm button; confirming calls `governanceService.decide(id, "rejected", note)` then `resume()` (guarded on `awaiting_approval`); the backend coaches one bounded turn (57.99). The note is optional (the backend handles `reason or 'no reason given'`).
- **US-4 (other kinds unchanged)** — As the maintainer, I want tool/input/between_turns/output rejects to stay exactly as they are (terminate, no resume, no note input), so this slice cannot regress the tool-approval path. → the note input + resume-on-reject are gated `kind === "verification"`; for any other kind (incl. `""`) `submitDecision("rejected")` is byte-identical to today (decide + optimistic merge, no resume).
- **US-5 (kind-aware render)** — As the reviewer, I want the card to read sensibly for a verification pause (not "tool: —"). → the meta row shows `kind: verification` (mono) when `kind === "verification"`; otherwise the existing `tool: {turn.tool}` row. (The verifier reason + held answer are already shown by the inline `VerificationBlock` above the card — not duplicated here.)
- **US-6 (drive-through — the REJECT half)** — As the user, I want to SEE the human-coached verification reject end-to-end. → drive-through (real UI + backend + Azure, a forced-fail judge): a failing answer → escalate pause (the card shows `kind: verification` + the inline `VerificationBlock` reason) → type a coaching note → Reject → the loop re-answers with the reviewer's coaching in context (one bounded turn); screenshot + observed-vs-intended in progress.md. (No "gate-only" claimed as drive-through.)

---

## 3. Technical Specifications

### 3.0 Architecture (the `approval_requested` wire gains `kind`; the card branches REJECT on it)

```
BEFORE (A2 / 57.99 — REJECT not UI-drivable)        57.100 (REJECT-with-note UI-drivable)
  events.ApprovalRequested(request_id, risk_level)    events.ApprovalRequested(request_id, risk_level, kind="")  # +field
  loop yield ApprovalRequested(..., risk_level=)      loop yield ApprovalRequested(..., risk_level=, kind="<kind>")  # 5 sites
  sse approval_requested {request_id, risk_level}     sse approval_requested {request_id, risk_level, kind}      # +wire
  HITLTurn type {…, tool}                             HITLTurn type {…, tool, kind}                              # +field
  store approval_requested -> {…, tool:"—"}           store approval_requested -> {…, tool:"—", kind: ev.data.kind ?? ""}
  HITLTurn.submitDecision(reject):                    HITLTurn.submitDecision(reject):
    decide(id,"rejected"); NO resume  ───────────────►  if kind==="verification":
                                                            reveal note textarea -> decide(id,"rejected",note) + resume()
                                                          else: decide(id,"rejected"); NO resume   # byte-identical
  card meta: tool: {turn.tool}                        card meta: kind==="verification" ? "kind: verification" : tool row
```

The frontend behavior change is **purely additive + verification-gated**: when `kind !== "verification"` (incl. the default `""` for any pre-existing wire that didn't send kind), `submitDecision` is byte-identical to 57.88. The wire change is additive (a field, not a type). The backend `resume()` is unchanged (the 57.99 `kind="verification"` REJECT coaching already works).

### 3.1 The `kind` wire field (US-1)
- `backend/src/agent_harness/_contracts/events.py` — `ApprovalRequested` +`kind: str = ""` (frozen dataclass field, default `""` → all 5 emit sites + any test constructors still build).
- `backend/src/agent_harness/orchestrator_loop/loop.py` — the 5 `yield ApprovalRequested(...)` sites pass `kind=`: `:814` `kind="tool"`, `:1030` `kind="input"`, `:1433` `kind="between_turns"`, `:1596` `kind="output"`, `:1812` `kind="verification"`. (Day-1 confirm each site's canonical kind string against the `pending_approval["kind"]` it builds — re-use the SAME literal so the wire `kind` == the persisted `kind`.)
- `backend/src/api/v1/chat/sse.py` — the `ApprovalRequested` branch (`:229-238`) adds `"kind": event.kind` to `data`.
- `backend/src/api/v1/chat/event_wire_schema.py` — the `"approval_requested"` entry (`:119-122`) adds `"kind": "string"`.
- `scripts/codegen/generate_event_schemas.py` — run it; `frontend/src/features/chat_v2/generated/loopEvents.generated.ts` regenerates (the `approval_requested` data type gains `kind`). No event-count bump (field on existing type).
- DoD: `mypy src` 0; `python scripts/codegen/generate_event_schemas.py` produces a clean regen (only the `approval_requested` `kind` field diff); `check_event_schema_sync` green; the backend + frontend parity tests green.

### 3.2 The frontend captures `kind` (US-2)
- `frontend/src/features/chat_v2/types.ts` — `HITLTurn` +`kind: string` (after `tool`).
- `frontend/src/features/chat_v2/store/chatStore.ts` — the `approval_requested` case (`:453-487`) sets `kind: ev.data.kind ?? ""` on the built `HITLTurn` (the generated type now carries `kind` so the narrow is typed; `?? ""` is belt-and-suspenders for an older replayed event).
- DoD: a unit test feeds an `approval_requested` event with `kind:"verification"` → the pushed `HITLTurn.kind === "verification"`; with no `kind` → `""`.

### 3.3 REJECT-with-coaching-note + kind-aware render (US-3 / US-4 / US-5)
- `frontend/src/features/chat_v2/components/turns/HITLTurn.tsx`:
  - Local state: `const [rejectNote, setRejectNote] = useState("")` + `const [showNoteInput, setShowNoteInput] = useState(false)`.
  - `const isVerification = turn.kind === "verification"`.
  - The Reject button: when `isVerification && !showNoteInput`, clicking it reveals the note input (`setShowNoteInput(true)`) instead of immediately submitting; when `!isVerification`, clicking it submits `"rejected"` immediately (today's behavior). A "Reject with note" confirm button (shown only when `showNoteInput`) submits `"rejected"` with `rejectNote`.
  - `submitDecision(decision, note?)`: `decide(turn.approvalRequestId, decision, note)` (pass `note` through — for approve it stays `undefined`); optimistic `approval_received` merge (unchanged); then `if (stopReason === "awaiting_approval" && (decision === "approved" || (decision === "rejected" && isVerification))) await resume()`. (APPROVE resume guard unchanged; the verification REJECT now also resumes.)
  - The note textarea: design-system-consistent — reuse the mockup `.hitl-card`/input vocab (the composer textarea pattern); placeholder e.g. "Coaching note for the agent (optional)…"; `aria-label="Coaching note"`. NEW element (no mockup source — `page-chat.jsx` L270-313 has no HITL note input) → use mockup CSS classes / `var(--*)` tokens, do NOT invent new colors (mockup-fidelity: nothing to drift from, but stay in the design system).
  - The meta row (`:186-191`): when `isVerification`, render `kind: verification` (mono, `var(--tool)` tone) instead of the `tool: {turn.tool}` row; otherwise unchanged.
- DoD: a verification turn — Reject reveals the note input; confirming calls `decide(id,"rejected",note)` + `resume()`. A tool turn (`kind===""`/`"tool"`) — Reject submits immediately, NO note input, NO resume (byte-identical). The meta row reads `kind: verification` for a verification turn.

### 3.4 What is explicitly NOT done + Lint / neutrality / 17.md / docs
- **NOT done (separate slices)**: a rich verification-specific approval card (re-rendering the held answer + verifier reasons inside the card — already covered by the inline `VerificationBlock`, chatStore `:608-633`); per-tenant verification mode/policy (C3); multi-round human coaching (>1 turn — A2 bounds to one); the `ApprovalCard.tsx` fallback widget (legacy 53.5 dual-emit path — out of scope; the canonical chat-inline render is `HITLTurn`); 4-action HITL UX (deferred AD-ChatV2-HITL-FourAction-Phase2).
- **Lint / neutrality**: backend `check_llm_sdk_leak` 0 (no SDK import — a wire field). `check_event_schema_sync` green (codegen regenerated; field added, count unchanged). `check_ap1` unaffected (no loop control-flow change — the emit sites just pass an extra kwarg). Frontend `npm run lint` (WITHOUT `--silent` — the 57.40 lesson) + `npm run build` + `npm run check:mockup-fidelity` (the new textarea uses mockup vocab + `var(--*)` tokens → no new HEX/oklch literals → `HEX_OKLCH_BASELINE` unchanged; confirm Day-1).
- **17.md (registration)**: update the `ApprovalRequested` / `approval_requested` row — the wire now carries `kind` (tool/input/between_turns/output/verification); note the chat-v2 HITL card branches REJECT on `kind === "verification"` (resume-with-note) vs terminate (others).
- **Design note (NONE — feature-continuation)**: per `sprint-workflow.md §Step 5.5`, this completes the 57.99 A2 leg's reviewer UI (reuses the shipped `resume()` `kind="verification"` + `ApprovalDecision.reason`) → feature-continuation, NOT a new-domain spike → **NO new design note**. Record = CHANGE-067 + update 17.md + 25.md §4 (the A2 reviewer-facing UI → SHIPPED, with file:line).

### 3.5 Validation (US-1..US-6)
- **Backend**: `mypy src` 0; `run_all` 10/10 (esp. `check_event_schema_sync`); `black`/`isort`/`flake8 src/ tests/` clean (run INDEPENDENTLY, FULL scope — the 57.95 + 57.98 CI lessons). `python scripts/codegen/generate_event_schemas.py` → clean regen. pytest:
  - **EDIT** `test_event_wire_schema_parity.py` — the `approval_requested` schema now includes `kind` (regenerated; assert parity holds).
  - **NEW/EDIT** an sse-serializer test: `ApprovalRequested(kind="verification")` → the wire `data` carries `"kind":"verification"`; the 5 loop emit sites pass the right kind (a focused unit asserting the verification escalate pause emits `kind="verification"` — extend the 57.99 escalate test, or a new small test).
  - Full backend suite green (NET delta documented — expect +N, 0 deletions).
- **Frontend**: `npm run lint` (no `--silent`) + `npm run build` + `npm run check:mockup-fidelity` (baseline unchanged) + `npm run test` (Vitest):
  - **EDIT** `eventSchema.generated.test.ts` — regenerated parity (approval_requested +kind).
  - **NEW** chatStore unit: `approval_requested` with `kind:"verification"` → `HITLTurn.kind==="verification"`; without kind → `""`.
  - **NEW** `HITLTurn` component unit: a verification turn — Reject reveals the note textarea; confirm → `decide` called with `(id,"rejected",note)` + `resume` called. A tool turn — Reject → `decide(id,"rejected")` (no note arg / undefined) + `resume` NOT called; no textarea rendered. Meta row reads `kind: verification` for verification.
  - The existing `approval-card.spec.ts` e2e contracts preserved (approval_id / HIGH / Decision / data-testids unchanged — the card structure is additive).
- **Drive-through** (US-6): real UI + real backend + real Azure — a forced-fail judge (the 57.99 env approach: `CHAT_VERIFICATION_MODE=enabled` + `CHAT_VERIFICATION_ESCALATE_ON_MAX=true` + a strict `CHAT_VERIFICATION_JUDGE_TEMPLATE` forcing a fail; a neutral "no tools, just re-answer" prompt per the 57.99 D-DAY3-2 lesson) → escalate pause (the card shows `kind: verification` + the inline `VerificationBlock` reason) → type a coaching note → Reject → the loop re-answers with the coaching in context (one bounded turn). Screenshot + observed-vs-intended in progress.md. Clean restart first (Risk Class E). (Per CLAUDE.md §Drive-Through Acceptance — "reject-with-note coaches one turn" is the leg-specific assertion; the buttons existing alone is gate/probe, not drive-through.)

---

## 4. File Change List

| File | Change |
|------|--------|
| `backend/src/agent_harness/_contracts/events.py` | **EDIT** — `ApprovalRequested` +`kind: str = ""`. MHist 1-line. |
| `backend/src/agent_harness/orchestrator_loop/loop.py` | **EDIT** — the 5 `yield ApprovalRequested(...)` sites (`:814`/`:1030`/`:1433`/`:1596`/`:1812`) pass `kind="tool"/"input"/"between_turns"/"output"/"verification"`. MHist 1-line. |
| `backend/src/api/v1/chat/sse.py` | **EDIT** — the `approval_requested` serializer (`:229-238`) +`"kind": event.kind`. MHist 1-line. |
| `backend/src/api/v1/chat/event_wire_schema.py` | **EDIT** — the `"approval_requested"` entry +`"kind": "string"`. MHist 1-line. |
| `frontend/src/features/chat_v2/generated/loopEvents.generated.ts` | **REGEN** — `python scripts/codegen/generate_event_schemas.py` (the `approval_requested` data type gains `kind`). Generated file — no manual edit. |
| `frontend/src/features/chat_v2/types.ts` | **EDIT** — `HITLTurn` +`kind: string`. MHist 1-line. |
| `frontend/src/features/chat_v2/store/chatStore.ts` | **EDIT** — `approval_requested` reads `ev.data.kind ?? ""` into the `HITLTurn`. MHist 1-line. |
| `frontend/src/features/chat_v2/components/turns/HITLTurn.tsx` | **EDIT** — kind-aware REJECT-with-note (note textarea reveal + `decide(id,"rejected",note)` + resume gated on `kind==="verification"` + `awaiting_approval`); kind-aware meta row (`kind: verification` vs `tool:`); `submitDecision` gains an optional `note` param. MHist 1-line. |
| `backend/tests/unit/api/v1/chat/test_event_wire_schema_parity.py` | **EDIT** — regenerated parity (approval_requested +kind). |
| `backend/tests/.../test_*sse*` or `test_loop_verification_escalate.py` | **EDIT (light)** — assert the wire carries `kind="verification"` (sse serializer) + the escalate pause emits `kind="verification"`. |
| `frontend/tests/unit/chat_v2/eventSchema.generated.test.ts` | **EDIT** — regenerated parity. |
| `frontend/tests/unit/chat_v2/store/*chatStore*` (Day-0 locate) | **EDIT/NEW** — `approval_requested` kind capture. |
| `frontend/tests/unit/chat_v2/**/HITLTurn*` (Day-0 locate; NEW if absent) | **NEW** — verification reject-with-note resumes; tool reject unchanged; meta render. |
| `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-100-plan.md` + `-checklist.md` | **NEW** — this plan + checklist. |
| `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-100/progress.md` + `retrospective.md` | **NEW** — Day 0-N progress + retro. |
| `claudedocs/4-changes/feature-changes/CHANGE-067-chatv2-verification-reject-ui.md` | **NEW** — the change record. |
| `docs/03-implementation/agent-harness-planning/17-cross-category-interfaces.md` | **EDIT** — the `approval_requested` wire gains `kind`; the chat-v2 card branches REJECT on `kind==="verification"`. |
| `docs/03-implementation/agent-harness-planning/25-verification-in-loop-design.md` | **EDIT** — §4 the A2 reviewer-facing UI → SHIPPED (with file:line); MHist. |

**NOT in this list (unchanged)**: `loop.py` `resume()` (the `kind="verification"` REJECT coaching already works — 57.99) · `_contracts/hitl.py` (the note rides the existing `ApprovalDecision.reason`) · `governanceService.ts` (`decide` already takes `reason`) · `useLoopEventStream.ts` (`resume()` already exists) · DB/migration (no new persisted field) · `ApprovalCard.tsx` (legacy fallback — out of scope) · the new event count (a field, not a type — 22 stays 22) · `ModelProfile`/`ChatClient` ABC.

---

## 5. Acceptance Criteria

- `ApprovalRequested` +`kind`; the 5 `loop.py` emit sites pass their real kind; `sse.py` serializes `"kind"`; `event_wire_schema.py` +`"kind": "string"`; codegen regen produces only the `approval_requested` `kind` diff; no event-count bump (US-1).
- `HITLTurn` type +`kind`; `chatStore` `approval_requested` reads `ev.data.kind ?? ""` (US-2).
- `HITLTurn.tsx` for `kind === "verification"` — Reject reveals an optional coaching-note textarea (mockup-vocab styling) → `decide(id, "rejected", note)` + `resume()` (guarded on `awaiting_approval`) (US-3).
- All other kinds (incl. `""`) — Reject is byte-identical to 57.88 (decide + optimistic merge, NO note input, NO resume) (US-4).
- The meta row reads `kind: verification` for a verification turn; `tool: {turn.tool}` otherwise (US-5).
- Backend `mypy src` 0 + `run_all` 10/10 (`check_event_schema_sync` green) + `black`/`isort`/`flake8 src/ tests/` clean (independent, FULL scope) + full pytest green (NET documented); frontend `lint` (no `--silent`) + `build` + `check:mockup-fidelity` (baseline unchanged) + Vitest green; CHANGE-067 + 17.md + 25.md §4.
- **Drive-through PASS** (the REJECT half): real UI + backend + Azure + forced-fail judge → escalate pause (`kind: verification` + the inline `VerificationBlock` reason) → coaching note → Reject → the loop re-answers with the coaching (one bounded turn); screenshot + observed-vs-intended. (No "gate-only" claimed.)

---

## 6. Deliverables

- [ ] `ApprovalRequested` +`kind` + 5 loop emit sites + sse wire + event_wire_schema + codegen regen (no count bump) (US-1)
- [ ] `HITLTurn` type +`kind` + chatStore captures `ev.data.kind` (US-2)
- [ ] `HITLTurn.tsx` verification REJECT-with-note (note textarea + decide(reason) + resume), verification-gated (US-3)
- [ ] tool/input/between_turns/output reject byte-identical (no note input, no resume) (US-4)
- [ ] kind-aware meta render (`kind: verification` vs `tool:`) (US-5)
- [ ] Tests: backend wire parity (regen) + sse-kind + escalate-emits-kind; frontend parity (regen) + chatStore kind-capture + HITLTurn reject-with-note-resumes / tool-reject-unchanged (US-1..US-5)
- [ ] backend mypy 0 + run_all 10/10 + format chain (independent, FULL scope) + frontend lint(no `--silent`)/build/check:mockup-fidelity/Vitest (validation)
- [ ] **drive-through PASS** (real UI + backend + Azure; forced-fail judge → escalate → coaching note → Reject → re-answer-with-coaching; screenshot + before/after) (US-6)
- [ ] CHANGE-067 + progress.md + retrospective.md + 17.md + 25.md §4
- [ ] commit (Day 0-N) — push + PR user-authorized

---

## 7. Workload Calibration

Scope class: **`frontend-feature-with-event-wire-addition` (NEW, 0.55) — 1st data point, pending 2-3 sprint validation**. The work is a thin additive backend wire field (`kind` on an existing event + 5 one-kwarg emit-site touches + 1 sse line + 1 schema line + codegen regen — no new event type, no count bump, no DB) PLUS a focused chat-v2 frontend interaction (capture `kind` + a verification-gated REJECT-with-note path + a small note textarea + a kind-aware meta row), PLUS the cross-stack parity (backend + frontend codegen fixtures regenerate together). The work splits: the wire field + 5 emit sites + sse + schema + codegen regen (~1.5 hr) / the frontend type + store + `HITLTurn` reject-with-note + note input + render (~3.5 hr) / tests — backend parity+sse-kind, frontend parity+chatStore+HITLTurn (~2.5 hr) / drive-through — the REJECT half with a forced-fail judge + clean restart (~2 hr) / docs — CHANGE-067 + progress + retro + 17.md + 25.md §4, NO design note (~1.5 hr). Bottom-up ~11 hr. Dominant costs = the `HITLTurn` reject-branch correctness (verification-gated resume + the note UX without regressing the tool path) + the drive-through (forcing a real fail → reject → re-answer). **Agent-delegated: no** (parent-direct) — the verification-gated reject-resume correctness (must NOT regress tool reject), the cross-stack codegen parity, and the drive-through (a real forced-fail → coaching → re-answer) are correctness work the parent must drive. `agent_factor = 1.0`; does NOT extend the AgentDelegated streak.

> Bottom-up est ~11 hr → class-calibrated commit ~6 hr (mult 0.55). **Agent-delegated: no.**

If Day-1 shows the wiring ripples wider than the spec'd files (e.g. the codegen regen touches more than the `approval_requested` field; `ev.data.kind` isn't typed after regen and needs a generated-type fix; the note textarea can't be styled with mockup vocab without a new token; the tool-reject path shares code that can't be left byte-identical without a refactor; a forced-fail reject can't be driven cleanly), STOP and re-scope rather than rush.

---

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| **The tool-reject path must stay byte-identical** | The note input + resume-on-reject are gated `kind === "verification"`. A frontend unit asserts a tool turn (`kind===""`/`"tool"`) — Reject → `decide(id,"rejected")` (no resume, no textarea). The existing `approval-card.spec.ts` e2e contracts (approval_id / HIGH / Decision / data-testids) preserved. |
| **Codegen regen must touch ONLY `approval_requested.kind`** | Run `python scripts/codegen/generate_event_schemas.py`; `git diff` the generated `.ts` → assert the only change is the `approval_requested` `kind` field (no spurious reformat / unrelated drift). `check_event_schema_sync` + both parity tests green. |
| **`ev.data.kind` typing after regen** | The generator types `approval_requested`'s data; post-regen `ev.data.kind` is `string`. If the union narrow doesn't surface it (Day-1), `ev.data.kind ?? ""` + a typed read; do NOT hand-edit the generated file (regen is the source of truth). |
| **The wire `kind` literal must == the persisted `kind`** | Each `loop.py` emit site already builds `pending_approval["kind"]`; pass the SAME literal to `ApprovalRequested(kind=…)` so the wire `kind` matches the checkpoint `kind` that `resume()` dispatches on. Day-1 grep the 5 sites' `pending_approval` kind strings to confirm (`tool`/`input`/`between_turns`/`output`/`verification`). |
| **The note textarea has no mockup source** | `page-chat.jsx` L270-313 has no HITL note input → reuse the mockup `.hitl-card`/composer-input vocab + `var(--*)` tokens; do NOT invent colors. `check:mockup-fidelity` baseline (HEX_OKLCH) unchanged (Day-1 confirm). Per mockup-fidelity rule: a new element with no mockup counterpart uses the design system, there is nothing to "drift" from — but stay in-vocab. |
| **Forcing a real verification fail for the drive-through** | Reuse the 57.99 env approach (`CHAT_VERIFICATION_MODE=enabled` + `CHAT_VERIFICATION_ESCALATE_ON_MAX=true` + a strict `CHAT_VERIFICATION_JUDGE_TEMPLATE`); the neutral "no tools, just re-answer" prompt (the 57.99 D-DAY3-2 lesson — a tool-equipped agent that hears "approval/reject" may call a tool, breaking the final-answer requirement). If a real fail can't be forced cleanly, the reject-with-note MECHANISM is unit-proven + the drive-through drives the toggle + the pause UI + the note input clearly labelled. |
| **Risk Class E (stale `--reload` backend masks the new wire field)** | Clean restart before the drive-through — the `kind` wire field + the escalate toggle are read at startup; a stale process serves the old wire. Kill the uvicorn reloader + the `multiprocessing.spawn` worker (`Get-CimInstance Win32_Process` PID/PPID/StartTime + `Stop-Process -Force`; verify the FRESH PID is the SOLE :8000 owner; do NOT touch the frontend node :3007 / claude-code node). The 57.91-99 streak (9 consecutive). |
| **Risk Class C (test isolation)** | Frontend Vitest mocks `governanceService`/`resume`; backend sse/parity tests are pure. Run the full suite. |
| **CI black/lint on the FULL scope (the 57.95 + 57.98 lessons)** | `black --check src/ tests/` (FULL scope) before push; frontend `npm run lint` WITHOUT `--silent` (the 57.40 lesson — `--silent` swallows lint errors). |
| **Over-engineering (scope creep into a rich verification card / multi-round)** | This slice is ONLY: the `kind` wire field + the frontend capture + the verification-gated REJECT-with-note + the kind-aware meta. NO rich held-answer/reason re-render in the card (the `VerificationBlock` already shows it), NO per-tenant policy, NO multi-round coaching, NO `ApprovalCard.tsx` fallback change, NO 4-action UX (Karpathy §2/§3). |
| **Smuggling unrelated change** | The diff is exactly: `events.py`(+field) + `loop.py`(5 kwargs) + `sse.py`(+1) + `event_wire_schema.py`(+1) + the regen + `types.ts`(+field) + `chatStore.ts`(+read) + `HITLTurn.tsx`(reject branch + note + render) + tests + docs. `resume()`/`hitl.py`-DTO/`governanceService`/DB/`ApprovalCard.tsx`/`ModelProfile` diff = 0. |

---

## 9. Out of Scope (this sprint; → separate slices / ADs)

- **A rich verification-specific approval card** — re-rendering the held answer + the verifier reasons richly INSIDE the card. The inline `VerificationBlock` (chatStore `:608-633`) already renders the reason + suggested_correction above the card; duplicating it is gold-plating. A dedicated verification approval card is a frontend follow-on.
- **Per-tenant verification mode/policy (Config 分層)** — workflow C (C3); A2 is a global toggle, this slice is its UI.
- **Multi-round human coaching (>1 turn)** — A2 bounds REJECT to exactly one human-coached turn; iterative reject→coach→reject is a follow-on.
- **The `ApprovalCard.tsx` fallback widget** — the legacy 53.5 dual-emit path; this slice touches the canonical chat-inline `HITLTurn` only. Making the fallback card kind-aware is a separate (low-priority) follow-on.
- **A3 — trace-aware critique** + cheap-judge accuracy benchmark — separate slice (design-note 24/25 carryover).
- **4-action HITL UX** (Approve-with-edits / Escalate-to-L2) — deferred AD-ChatV2-HITL-FourAction-Phase2.
