# Sprint 57.108 Retrospective — chat-v2 HITL card real tool/reason + Inspector turn metadata wire

**Closed**: 2026-06-12 · [Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-108-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-108-checklist.md) · [Progress](./progress.md) · CHANGE-075

## Q1 — What shipped vs planned?

All 4 user stories shipped; scope SHRANK at Day 0 (D1/D5) instead of creeping. `ApprovalRequested` +tool_name/reason (5 yield sites; tool site carries `tc.name`) + `llm_response` +token actuals → codegen regen → chatStore 4 captures (approval tool/rationale · turn_start traceId+TURN-span link · llm_response token overwrite · span_ended TURN→durationMs). ZERO component edits (HITLTurn/InspectorTurn store-driven). Closes `AD-ChatV2-HITL-Card-Tool-Name` + `AD-ChatV2-Inspector-Turn-Metadata-Wire` (cost + thinking carved out by documented design, not silently dropped). Drive-through ALL legs PASS.

## Q2 — Estimate accuracy (calibration)

- Plan §Workload: bottom-up ~11 hr → class-calibrated commit ~6 hr (`frontend-feature-with-event-wire-addition` 0.55). **Agent-delegated: no** (parent-direct; Explore agents used for Day-0 recon only, not implementation) → agent_factor 1.0, 3-segment form.
- Actual ≈ 6.5 hr (Day 0 ~1 · Day 1 ~1.5 · Day 2 ~1.5 · Day 3 ~1.5 · Day 4 ~1). **Ratio actual/committed ≈ 1.05-1.1 — IN band.**
- **2nd data point for the class** (57.100 1st ≈ 1.0; both IN band at 0.55) → KEEP 0.55; one more point completes the 3-sprint window.

## Q3 — What went well?

- **Day-0 head-start recon (2 Explore agents) + targeted self-greps** produced file:line ground truth that made the plan land surgically: loop.py diff = 6 kwargs + header; FE diff = 1 store file (+ fixture ripple).
- Drift findings SHRANK scope: D1 (tokens.in already wired) + D5 (HITLTurn zero-edit, store-driven) + D2 (explicit TURN span match). The "store-driven components" investment from 57.21 paid off — wiring real data needed no render changes.
- 57.107 isort lesson applied: four-segment format chain run locally before every commit; zero CI-format risk this time.
- Drive-through produced an unplanned LIVE proof: the LLM refused `os.system`, the in-loop verifier coached a retry, the retry used `subprocess`, and the deny-list's multi-pattern design caught the detour — the new `reason` field made that whole story legible on the approval card.

## Q4 — What to improve / lessons?

- **D9 (Day-2 load-bearing)**: plan §3.3 assumed span linkage in `span_started`; reality — `SpanStarted(TURN)` is emitted BEFORE `TurnStarted` (loop.py:2173→:2188), so that handler would attach the span to the PREVIOUS turn. Caught at Day-2 code time, not Day 0. Lesson (candidate Prong-2 row if it recurs): when wiring FE state from a SEQUENCE of related events, verify the EMISSION ORDER at Day 0, not just each event's shape — `AD-Day0-Prong2-Event-Emission-Order` (1st data point, watch).
- `llm_request` streams `tokens_in=0` on this adapter — the pre-existing tokens.in wiring was silently value-less on 主流量; only the Day-3 drive-through surfaced it (the response-actuals overwrite fixed it as a side effect). Reinforces drive-through-over-gates.
- Plan said "accumulate" for tokens; reality = one LLM call per TAO turn → overwrite (mirror llm_request idiom). Minor plan-vs-repo drift, absorbed at Day 0/2.

## Q5 — Anti-pattern audit

AP-1..11: 0 violations. AP-4 specifically guarded: old frames degrade to the honest "—" (Vitest-pinned); cost/thinking stay "—" rather than fake values; no new event type (count 24 unchanged); no version suffixes; no dead code introduced.

## Q6 — Category/contract hygiene

Cat 1 (yield kwargs only) × api/v1/chat (wire+serializer) × FE store. 17.md untouched — no ABC/contract change (additive event FIELDS are wire-schema territory; `event_wire_schema.py` is the single source and codegen chain enforced sync). Multi-tenant: N/A (no DB, no endpoint).

## Q7 — Carryover / next

- `AD-ChatV2-Inspector-Cost-InStream` — NOT carved (YAGNI per plan §9): cost stays a cost-dashboard concern unless a real consumer demands in-stream cost.
- `AD-Day0-Prong2-Event-Emission-Order` (🆕 watch, 1st data point — D9): verify event emission ORDER when FE wiring depends on event sequencing.
- `AD-LLMRequest-TokensIn-Zero` (🆕 🟢 minor): `llm_request.tokens_in` streams 0 on the Azure adapter — either populate the pre-call estimate or drop the field from the wire (now redundant vs llm_response actuals).
- Next slice per interleave (RBAC → C3 → B3 → UX ✅ → **C2** → B4): C2 compaction cheap-tier. Rolling discipline — plan only on user kickoff.

## Design Note Extract（spike sprint only）

N/A — feature continuation (additive fields on existing events + FE store wiring), not a new-domain spike. CHANGE-075 carries the record.
