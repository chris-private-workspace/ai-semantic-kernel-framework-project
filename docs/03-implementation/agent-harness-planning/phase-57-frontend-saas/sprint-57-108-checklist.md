# Sprint 57.108 — Checklist (UX slice: chat-v2 HITL card real tool/reason + Inspector turn metadata wire — additive `approval_requested` + `llm_response` fields, codegen regen, FE store captures → tool-escalate drive-through)

[Plan](./sprint-57-108-plan.md)

---

## Day 0 — Plan-vs-Repo Verify + Branch ✅

### 0.1 Three-prong Day-0 verify (against `main` HEAD `a42ed717`) — DONE, catalogued in progress.md D1-D8
- [x] **Prong 1 — path verify**: EDIT files Glob-1 (`events.py` / `loop.py` / `event_wire_schema.py` / `sse.py` / `chatStore.ts` / `types.ts` / `HITLTurn.tsx` (actual: `components/turns/`) / `ApprovalCard.tsx` / `InspectorTurn.tsx` / generated artifacts ×2 / codegen script); test suites pinned (`ChatInspector.test.tsx` / `approval-card.spec.ts` / loop escalate unit suites / `test_event_wire_schema_parity.py`); NO new files expected (Glob-0 check n/a)
- [x] **Prong 2 — content verify** (D1 tokensIn already wired via llm_request → overwrite not accumulate; D2 TURN span explicit; D3 no turn_end → durationMs via TURN span_ended fold-in; D6 :1833 reason in scope; D7 constructors keyword-only ×8; D8 relay excludes ApprovalRequested): ALL plan §0 STALE anchors — verification site :1833 reason-in-scope · grep ALL `ApprovalRequested(` constructors (src + tests + resume replay 57.99 + subagent relay `_TAO_CHILD_EVENT_TYPES`) · `llm_response` serializer body (where `cached_input_tokens` is read) · FE `turn_start` handler shape (:382-398) + `stop_reason`/`durationMs` already-wired? (`turn_end`/`loop_end` handlers) · span event payload shape (name/kind — turn-root identifiable?) · `llm_response` multiplicity per AgentTurn · HITLTurn.tsx tool/rationale render lines (D5 — ZERO component edits needed; store-driven) · `events.json` committed envelope shape (codegen-shape drift class)
- [x] **Prong 2.5 — FE tree audit**: HITLTurn / ApprovalCard / InspectorTurn child-import depth-2 grep (shadcn residue / inline-style escapes) — clean (no structural change this sprint; HITLTurn header documents styles-mockup.css classes)
- [x] **Prong 3 — schema verify**: N/A (no DB / no migration) — recorded explicitly
- [x] **Catalog drift** findings in progress.md Day 0 (D1-D8 + implications; plan §8 cross-ref)
- [x] **Go/no-go**: GO — findings SHRINK scope (HITLTurn no-edit; tokens.in done; explicit span match)

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-108-chatv2-hitl-inspector-wire` (from `main` `a42ed717`)

---

## Day 1 — Backend: additive event fields + wire + serializer + codegen (US-1 + US-3 backend) ✅

### 1.1 `ApprovalRequested` +2 fields + 5-site emission (US-1)
- [x] **`_contracts/events.py`**: `ApprovalRequested` += `tool_name: str | None = None` + `reason: str = ""` (defaulted; frozen dataclass; MHist 1-line)
- [x] **`loop.py`**: 5 yield sites pass `reason=` from in-scope local; tool site (:1048) additionally `tool_name=tc.name`; verification site carries the joined verifier reason (D6 — real reason, no `""` fallback needed)
  - DoD: grep `yield ApprovalRequested` → 5 sites all carry reason ✓; loop.py diff limited to yield sites ✓
- [x] **Wire + serializer**: `event_wire_schema.py` approval_requested += `{tool_name: "string | null", reason: "string"}`; `sse.py` approval serializer reads both
- [x] **Unit tests CONVERT**: 5 escalate-site assertions extended (tool site = `sensitive_tool` + reason; input/between_turns/output/verification = tool_name None + reason truthy) + test_sse defaults/tool-context cases — 0 deletions; parity auto-holds, count stays 24

### 1.2 `llm_response` token pair (US-3 backend)
- [x] **Wire + serializer**: `event_wire_schema.py` llm_response += `{input_tokens: "number", output_tokens: "number"}`; `sse.py` llm_response serializer reads `event.input_tokens`/`event.output_tokens` (dataclass already carries them — no events.py change beyond ApprovalRequested)
- [x] **Codegen regen**: `python scripts/codegen/generate_event_schemas.py` → `events.json` + `loopEvents.generated.ts` committed in the SAME commit
  - DoD: `check_event_schema_sync` green ✓; run_all 10/10 (count 24 UNCHANGED) ✓; mypy strict 0/359 ✓; black/isort/flake8 0 ✓; full backend pytest **2462+4skip (+2, 0 del)** ✓

---

## Day 2 — FE: store captures + renders + Vitest (US-2 + US-3 FE) ✅

### 2.1 HITL card real tool/reason (US-2)
- [x] **chatStore.ts** `approval_requested` case: `tool: ev.data.tool_name ?? "—"` + `rationale: ev.data.reason || "—"` (dropped the :546 hardcode); `approvals[id]`/`types.ts` ApprovalEntry extension DROPPED per D5 (nothing renders tool from the approvals dict — YAGNI)
- [x] **HITLTurn.tsx + ApprovalCard.tsx**: ZERO component edits per D5 — HITLTurn already renders `turn.tool` (:197-199) + gates rationale/payload on `!== "—"` (:206/:212); fully store-driven
- [x] **Vitest ADD**: approval tool-context + "—" fallback store cases (HITLTurn render path covered via the store-driven gates)

### 2.2 Inspector metadata captures (US-3 FE)
- [x] **trace_id**: `turn_start` handler `traceId: ev.data.trace_id ?? null` (dropped the :394 hardcode)
- [x] **span_id**: linked in the `turn_start` handler from the newest RUNNING TURN span (D9: SpanStarted(TURN) precedes TurnStarted — linking in span_started would attach to the PREVIOUS turn) — explicit `spanType === "TURN"` match per D2
- [x] **tokens**: `llm_response` handler OVERWRITES `tokensIn`/`tokensOut` from `ev.data` actuals when > 0 (D1: one LLM call per TAO turn — mirror the llm_request idiom; 0/absent keeps prior so old frames / unmeasured paths stay honest "—")
- [x] **durationMs bonus fold-in (D3)**: `span_ended` TURN fills the spanId-matched `AgentTurn.durationMs` (no turn_end event exists)
- [x] **Vitest ADD ×8** (`chatStore.mergeEvent.test.ts` 46→54): trace+span link / second-turn own-span / token overwrite / token absent-keeps-prior / approval context / approval fallback / TURN duration fill / non-TURN untouched. `ChatInspector.test.tsx` UNCHANGED — InspectorTurn component untouched; its null-fallback test stays valid (old frames CAN still carry nulls)
  - DoD: FE lint 0 (non-silent) ✓ · build ✓ (incl. demoLoopEvents.ts type-contract ripple fix) · Vitest **836 (+8, 0 del)** ✓ · mockup-fidelity 51==51 ✓

---

## Day 3 — Full gates + drive-through (US-4) + CHANGE-075 ✅

### 3.1 Full gate sweep
- [x] mypy strict 0/359 · black/isort/flake8 0 · run_all 10/10 (count 24) · full pytest 2462+4skip (0 del) · FE 4 gates (Vitest 836 / mockup-fidelity 51==51) · wire schema diff = additive-only · loop.py diff = 5 yield kwargs + header only

### 3.2 Drive-through (US-4 — real UI :3007 + fresh no-reload backend PID 33124 + real Azure gpt-5.2; zero dev-login; Risk Class E clean restart) ✅ ALL LEGS PASS
- [x] **HITL card reality**: risky sandbox ask → LLM refused → verifier coached → `subprocess` retry → RiskyActionDetector ESCALATE → card shows **tool: python_sandbox** + real rationale (`risky_action: sandbox code matched '\bsubprocess\b'`) → Approve → tool executed (real output) → `Decision: APPROVED` → final answer + verification 0.99
- [x] **Non-tool fallback**: "approval required" input phrase → pause before any LLM call → card **tool: —** (honest) + **reason: input matched escalation phrase** (real)
- [x] **Inspector reality**: tokens.in **2,301** (actuals overwrote the `tokens_in=0` llm_request estimate — D1 design proved live) · tokens.out **75** · trace_id + span_id real (span_id = the turn's TURN span exactly, D9) · duration fills on TURN span_ended (5.33s/6.45s) and stays "—" mid-pause (honest) · cost/thinking "—" by design
- [x] Screenshots ×3 (`artifacts/dt57108-*.png`) + observed-vs-intended table in progress.md
  - DoD: ALL legs PASS ✓; Leg B pause rejected (cleanup); no tenant policy was modified (defaults used throughout)

### 3.3 CHANGE-075
- [x] `claudedocs/4-changes/feature-changes/CHANGE-075-chatv2-hitl-card-inspector-metadata-wire.md` (1-page; spike design note NOT required — feature continuation, not a new-domain spike)

---

## Day 4 — Closeout

### 4.1 Closeout
- [x] retrospective.md Q1-Q7 + calibration (`frontend-feature-with-event-wire-addition` 0.55 2nd data point, ratio ≈1.05-1.1 IN band; agent-delegated: no) + progress.md final
- [x] Navigators: CLAUDE.md Current-Sprint row + Last-Updated; MEMORY.md quality pointer + memory subfile; next-phase-candidates (closes `AD-ChatV2-HITL-Card-Tool-Name` + `AD-ChatV2-Inspector-Turn-Metadata-Wire`; cost carve-out documented; NEW `AD-Day0-Prong2-Event-Emission-Order` watch + `AD-LLMRequest-TokensIn-Zero` 🟢); sprint-workflow matrix row (2nd data point)
- [x] PR (push + open on user authorization — authorized 2026-06-12)
