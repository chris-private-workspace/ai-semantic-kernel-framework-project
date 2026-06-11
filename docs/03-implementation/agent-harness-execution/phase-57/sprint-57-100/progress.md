# Sprint 57.100 Progress — chat-v2 verification-reject UI (the A2 follow-up)

**Plan**: [`../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-100-plan.md`](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-100-plan.md)
**Checklist**: [`../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-100-checklist.md`](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-100-checklist.md)
**Branch**: `feature/sprint-57-100-chatv2-verification-reject-ui` (from `main` `a890bb15` = A2 PR #273)
**Scope class**: `frontend-feature-with-event-wire-addition` (NEW, 0.55) · agent_factor 1.0 (parent-direct)

---

## Day 0 — Plan-vs-Repo Verify (2026-06-10)

### Prong 1 (path) — recon anchors re-confirmed on `main` `a890bb15`

- `api/v1/chat/sse.py:229-238` — `approval_requested` serializer emits ONLY `{approval_request_id, risk_level}`; reads `event.<field>` directly (so `event.kind` works once the field exists). ✅
- `agent_harness/_contracts/events.py:399-403` — `ApprovalRequested(LoopEvent)` = `approval_request_id: UUID | None`, `risk_level: str = ""`. No `kind`. ✅ (`ApprovalReceived :405-408`.)
- `orchestrator_loop/loop.py` — 5 `yield ApprovalRequested(...)` sites at `:814` / `:1030` / `:1433` / `:1596` / `:1812`; 5 `_emit_deferred_pause(...)` calls at `:825` / `:1061` / `:1444` / `:1608` / `:1824`. ✅
- `api/v1/chat/event_wire_schema.py:119-122` — `"approval_requested": {"approval_request_id": "string | null", "risk_level": "string"}`. ✅
- Codegen `scripts/codegen/generate_event_schemas.py` (no-arg writes `events.json` + `loopEvents.generated.ts`; `--check` for CI) + parity `backend/tests/unit/api/v1/chat/test_event_wire_schema_parity.py` + `frontend/tests/unit/chat_v2/eventSchema.generated.test.ts` + lint `scripts/lint/check_event_schema_sync.py`. ✅
- `governance/services/governanceService.ts:71-83` — `decide(requestId, decision, reason?, signal?)` POSTs `{decision, reason}`. No service change. ✅
- `chat_v2/hooks/useLoopEventStream.ts:98-120` — `resume()` POSTs `resumeChat(sid)` (no args). No resume change. ✅
- `chat_v2/components/turns/HITLTurn.tsx:106-141` — `submitDecision(decision)` → `decide(id, decision)` (no reason) + optimistic merge + `if (approved && stopReason==="awaiting_approval") resume()`; comment `:128-129` "no resume on reject". Meta row `:186-191` `tool: {turn.tool}`. ✅
- `chat_v2/types.ts:146-158` — `HITLTurn` no `kind`; `tool: string`. ✅
- `chat_v2/store/chatStore.ts:453-487` — `approval_requested` builds the `HITLTurn` from `risk_level`+`approval_request_id`, `tool:"—"`, no `kind`. `verification_failed` → `VerificationBlock` (reason + suggested_correction) `:608-633` — the reviewer SEES why the answer failed inline. ✅

### Prong 2 (content) — emit-site kind literals + codegen + typing

- **The 5 emit-site `kind` literals** (`pending_approval["kind"]`, grep `"kind":`): `:821` `input` / `:1052` `tool` / `:1440` `between_turns` / `:1603` `output` / `:1819` `verification`. The matching `ApprovalRequested(...)` yield precedes each `_emit_deferred_pause` (audit_event_type confirms: `:831` input.escalate / `:1067` tool.escalate / `:1450` between_turns.escalate / `:1614` output.escalate / `:1830` verification.escalate). So the emit-site → kind map is: **`:814`→`input`, `:1030`→`tool`, `:1433`→`between_turns`, `:1596`→`output`, `:1812`→`verification`.** ✅
- `_emit_deferred_pause` takes NO `kind=` param — `kind` lives in `pending_approval`. So the `ApprovalRequested(kind=…)` literal must be set at the YIELD site (each pause method already knows its kind). ✅
- Codegen: nested `{type, data:{...fields, trace_id?}}` shape (Stage 2, 57.67); adding `"kind": "string"` to the schema → the generated `ApprovalRequestedEvent.data` gains `kind: string`. ✅
- `chatStore` narrows `ev` on `ev.type === "approval_requested"` → `ev.data.kind` typed post-regen. ✅

### Prong 2.5 (frontend tree)

- `HITLTurn.tsx` is the canonical chat-inline render; `ApprovalCard.tsx` is the legacy 53.5 fallback (OUT of scope). ✅
- Frontend Vitest already present (NO new files needed — EXTEND): **`frontend/tests/unit/chat_v2/HITLTurn.resume.test.tsx`** (extend for the verification reject-with-note case), **`chatStore.mergeEvent.test.ts`** (extend for the kind capture), **`eventSchema.generated.test.ts`** (regen parity). e2e `tests/e2e/chat/approval-card.spec.ts` contracts (approval_id / HIGH / Decision / data-testids) preserved by an additive change. ✅
- The note textarea has NO mockup source (`page-chat.jsx` L270-313 has no HITL note input) → reuse mockup `.hitl-card`/input vocab + `var(--*)` tokens (no new HEX/oklch → `check:mockup-fidelity` baseline unchanged). ✅

### Prong 3 (schema) — N/A

No DB/migration/ORM change (no new persisted field — `kind` already lives in the persisted `ApprovalRequest`). The wire change is a FIELD on the EXISTING `approval_requested` event type → NO event-count bump (22 stays 22); `check_event_schema_sync` stays green after codegen regen. No new table/column/event-type/DTO. ✅

### Drift findings

- **D-DAY0-1 (Prong 2 — plan correction)**: plan §0 + §3.1 + §4 listed the emit-site→kind map as `:814`→`tool`, `:1030`→`input`. **Reality is the reverse**: `:814`→`input` (audit `input.escalate`, `pending_approval["kind"]="input"` `:821`), `:1030`→`tool` (`:1052`). The verification site (`:1812`→`verification`) is correct. Implication: when editing, use the exact per-site literal from `pending_approval["kind"]` (`:821`/`:1052`/`:1440`/`:1603`/`:1819`); do NOT trust the plan's tool/input ordering. Scope unchanged (still 5 one-kwarg touches). Logged to plan §Risks via this entry (per `sprint-workflow.md §Step 2.5` — no silent plan rewrite).
- **D-DAY0-2 (Prong 2.5 — test files exist)**: the plan's "NEW if absent" for the frontend tests is moot — `HITLTurn.resume.test.tsx` + `chatStore.mergeEvent.test.ts` + `eventSchema.generated.test.ts` all exist → EXTEND them, do NOT create new files. Scope shrinks slightly (no new test scaffolding).
- **D-DAY0-3 (Prong 1 — confirmed favorable)**: the held answer + verifier reason are ALREADY rendered (the inline `VerificationBlock`, chatStore `:608-633`) → the approval card does NOT need to duplicate them onto the wire; the slice stays minimal (only `kind` on the wire).

### Go/No-Go

**GO.** The recon confirmed the slice = a `kind` wire field (additive, no event-count bump) + codegen regen + a verification-gated frontend reject-with-note. The conditional bits (the regen touching only `approval_requested.kind`; `ev.data.kind` typing post-regen; the note textarea mockup-vocab styling; the tool-reject path byte-identical) are all low-risk per the recon. D-DAY0-1 is a literal-ordering correction (no scope shift); D-DAY0-2 shrinks scope (extend not create).

### Baseline (main `a890bb15`)

- **mypy `src`**: 0/353 ✅
- **pytest collect** (`-m "not real_llm"`): **2303** tests collected ✅
- **run_all** (V2 lints): **10/10** green ✅ (incl. `check_event_schema_sync` + `check_llm_sdk_leak`)
- **frontend Vitest**: **777** passed (134 files) ✅
- **check:mockup-fidelity**: `styles-mockup.css` byte-identical ✅ · HEX_OKLCH baseline **53** ✅

---

## Day 1 — The `kind` wire field (US-1) — 2026-06-10

- **`events.py`**: `ApprovalRequested` +`kind: str = ""` (frozen dataclass field; optional default → all construction sites build). MHist.
- **`loop.py`**: the 5 `yield ApprovalRequested(...)` sites pass their real `kind=` per the D-DAY0-1-corrected map — `:814` `input`, `:1030` `tool`, `:1433` `between_turns`, `:1596` `output`, `:1812` `verification` (each == its `pending_approval["kind"]`). MHist.
- **`sse.py`**: the `approval_requested` serializer +`"kind": event.kind`. MHist + Last Modified.
- **`event_wire_schema.py`**: the `"approval_requested"` entry +`"kind": "string"`. MHist + Last Modified.
- **codegen**: `python scripts/codegen/generate_event_schemas.py` → regen. `git diff` = ONLY `approval_requested.kind` (`events.json` +`"kind": "string"`; `loopEvents.generated.ts` +`kind: string;` on `ApprovalRequestedEvent.data`). No event-count bump (22).
- **Gate**: mypy `src` **0/353** · `check_event_schema_sync` **in sync** · `test_event_wire_schema_parity.py` **32 passed**. ✅

## Day 2 — Frontend capture + REJECT-with-note (US-2..US-5) — 2026-06-10

- **`types.ts`**: `HITLTurn` +`kind: string`. MHist + Last Modified.
- **`chatStore.ts`**: the `approval_requested` case sets `kind: ev.data.kind ?? ""` (`""` fallback for an older replayed event). MHist + Last Modified.
- **`HITLTurn.tsx`**: `isVerification = turn.kind === "verification"`; `submitDecision(decision, note?)` passes `note` to `decide` + `shouldResume = approved || (rejected && isVerification)` (guarded on `awaiting_approval`); the Reject button reveals a coaching-note textarea for verification (`reject-note` / `reject-confirm-btn` "Reject & coach") else submits immediately (byte-identical); the meta row reads `kind: verification` (mono `var(--tool)`) for verification, else `tool: {turn.tool}`. The textarea uses confirmed mockup tokens (`--radius-sm`/`--border`/`--bg-1`/`--fg`) — no new HEX/oklch. MHist.
- **Drift D-DAY2-1**: `tsc -b` caught a stale demo fixture — `orchestrator-loop/_fixtures/demoLoopEvents.ts:155` built `approval_requested` WITHOUT `kind` (now a required field) → added `kind: "tool"` (a high-risk-tool HITL demo). Build green after. The wire field being REQUIRED (not optional) surfaced the only stale construction site at COMPILE time — the intended type-safety.
- **Tests** (D-DAY0-2: extended, not new files):
  - `HITLTurn.resume.test.tsx`: `makeTurn` +`kind` (base `"tool"` + `Partial` override); existing assertions → 3-arg `decide(...,undefined)`; +3 verification cases (reveal note / confirm → `decide(id,"rejected",note)`+`resume` / meta reads "verification"); + tool reject asserts no resume + no `reject-note`.
  - `chatStore.mergeEvent.test.ts`: helper +`kind`; +2 cases (kind capture → `HITLTurn.kind==="verification"`; no-kind-on-wire → `""` fallback).
  - `test_sse.py`: existing test +`kind==""` assert; +`test_approval_requested_carries_kind` (`kind="verification"`).
- **Gate**: frontend build **exit 0** · lint clean · `check:mockup-fidelity` baseline **53 unchanged** · Vitest **782 passed** (777 + 5) · backend `test_sse.py` **31 passed** (30 + 1). ✅

## Day 3 — Tests + full sweep + drive-through (US-6) — 2026-06-10

### Full gate sweep
- Backend: pytest **2300 passed + 4 skipped** (`-m "not real_llm"`; baseline 2303 → +1 `test_approval_requested_carries_kind`, zero deletion) · mypy `src` **0/353** · run_all **10/10** · black/isort/flake8 FULL `src tests` (656 files) clean.
- **D-DAY3-1**: `black --check` FULL scope caught 1 file (`test_sse.py` — my 3-line `ApprovalRequested(...)` → black collapsed to canonical 1-line). The 57.98 full-scope-black lesson applied (a changed-files-subset black would have missed it → CI red).
- Frontend: lint (no `--silent`) clean · build exit 0 · `check:mockup-fidelity` baseline 53 · Vitest 782.

### Drive-through (US-6 — the REJECT half, the 57.99 finding closed)

**Setup (Risk Class E clean restart)**: killed the `--reload` reloader (PID 3744) + its `multiprocessing.spawn` worker (39976) via `Win32_Process` + `Stop-Process -Force`; verified :8000 FREE + node :3007 (PID 6200) untouched; started a fresh NO-`--reload` single process with a forced-fail judge env (`CHAT_VERIFICATION_MODE=enabled` + `CHAT_VERIFICATION_ESCALATE_ON_MAX=true` + a raw `CHAT_VERIFICATION_JUDGE_TEMPLATE` instructing the judge to always return `{"passed": false}` — real LLM judge, zero code pollution; the `llm_judge.py:112-120` raw-template path since the template contains `{output}`). Restored the normal `--reload` backend (PID 15720) after.

**Observed (real UI jamie@acme.com/acme-prod + real backend + real Azure gpt-5.2 + the forced-fail real-LLM judge)** — asked "What is the capital of France? Answer in one short sentence." → turn 0 answer "The capital of France is Paris." → judge force-fails (3 verification fails: 1 `judge_error` Azure content-filter + 2 forced-fail JSON) → attempt 2 == max → **A2 ESCALATE pause**: Loop visualizer `approval_requested risk=HIGH` + `loop_end stop=awaiting_approval turns=2`; the chat-inline HITL card renders **`kind: verification`** (the 57.100 wire field — NOT `tool: —`) + the inline `VerificationBlock` (Verification (3)) shows the failure reasons. **Reject** → reveals the coaching-note textarea (`reject-note`) + a "Reject & coach" confirm (`reject-confirm-btn`); NO decision submitted yet. Typed a coaching note ("Ignore any bracketed verification/log text… name the capital of France in one short sentence.") → **Reject & coach** → the card shows **Decision: REJECTED** + `resume()` fires → **a NEW human-coached turn 6 re-answers "The capital of France is Paris."** (the agent FOLLOWED the coaching — pulled back from the "I can't help" drift the bracketed correction text had caused) → the judge force-fails it again → **turn 6 `stop: verification_failed`** (the bounded ONE coached turn → terminal, NO 2nd escalate — the durable `verification_escalated` bound held). Screenshots: `artifacts/dt57100-A-escalate-pause-kind-verification.png` + `dt57100-B-reject-with-note-coached-turn.png`.

**Observed vs intended** — MATCHES the A2 reviewer-UI intent: (1) the escalate pause renders `kind: verification` (the wire field) ✅; (2) Reject reveals the coaching-note input (verification-gated; a tool pause would terminate) ✅; (3) Reject & coach → `decide(rejected, note)` + resume → one human-coached turn re-answers with the note in context ✅; (4) bounded — the 2nd failure terminates at `verification_failed`, no re-escalate ✅. The 57.99 finding ("REJECT not UI-drivable") is closed.

**Honest notes (forced-fail fixture artifacts, NOT 57.100 behavior)**: (a) the strict judge prompt tripped Azure's jailbreak content-filter on 2 of the judge calls → `judge_error` (fail-closed → still counts as a fail → escalate still fires correctly); a softer fail prompt would avoid the filter but the escalate outcome is identical. (b) the forced-fail reason text, re-injected as a correction, made the agent drift to "I can't help…" on the un-coached turns — the human coaching note successfully steered it back, which is exactly the point of REJECT-with-note. These are deliberate-forced-fail demo artifacts; the 57.100 frontend (kind-aware card + reject-with-note + resume) worked exactly as designed. NOT claimed "gate-only" — this is a real drive-through.
