# Sprint 57.100 Retrospective — chat-v2 verification-reject UI (the A2 follow-up)

**Sprint**: 57.100 (the A2 reviewer-UI follow-up — surface the pause `kind` on the `approval_requested` wire so chat-v2 HITL can REJECT-with-a-coaching-note + resume the verification ESCALATE pause)
**Dates**: 2026-06-10 (Day 0-4, single session)
**Branch**: `feature/sprint-57-100-chatv2-verification-reject-ui` (from `main` `a890bb15` = A2 PR #273)
**Scope class**: `frontend-feature-with-event-wire-addition` (NEW, 0.55) · agent_factor 1.0 (parent-direct)

---

## Q1 — What was the goal, and was it met?

Goal: make the A2 verification REJECT-with-note path UI-drivable in chat-v2 — the 57.99 drive-through proved the APPROVE half but found the REJECT half was not UI-drivable (the card was tool-shaped: reject=terminate, no note input, no way to know the pause kind because the `approval_requested` wire carried no `kind`). Add `kind` to the wire (additive field on the existing event), capture it frontend-side, and branch the chat-v2 REJECT on `kind="verification"` (coaching-note input + resume), tool/input/between_turns/output byte-identical.

**Met.** All 6 US shipped + gate-green + the full escalate→reject-with-note→coached-turn path drive-through-verified through the real UI/backend/Azure with a forced-fail real-LLM judge. The 57.99 "REJECT not UI-drivable" finding is closed.

## Q2 — Estimate accuracy (calibration)

- Plan §Workload: **Bottom-up ~11 hr → class-calibrated commit ~6 hr (mult 0.55)**. Agent-delegated: **no** (parent-direct → `agent_factor = 1.0`; 3-segment form).
- Actual (AI-paced estimate, not human-hours): **~6 hr** → ratio `actual / committed ≈ 1.0` — **IN band**.
- `frontend-feature-with-event-wire-addition` 0.55 is the **1st data point** (a thin additive backend wire field + codegen regen + a focused chat-v2 interaction + the cross-stack parity). KEEP 0.55 pending 2-3 sprint validation. The slice was smooth: the wire field being additive (no new event type, no count bump) + the held-answer/reason already rendered by the existing `VerificationBlock` kept the scope minimal; the drift findings were all small (a literal-ordering correction, a stale fixture, a black reformat).

## Q3 — What went well

- **The honest minimal design held**: surfacing `kind` on the wire (additive — a field, not a type) was the one correct way to let the frontend distinguish a verification pause; the rejected alternative (event-ordering inference) would have been a fragile Potemkin. The wire field being REQUIRED on the generated type made the change type-safe — `tsc` caught the only stale construction site (the demo fixture) at compile time.
- **No new event type / DB / DTO / resume change**: the codegen surfaced `kind` with a 1-field schema edit (no 22→23 count bump); the reviewer note rode the existing `ApprovalDecision.reason`; the held answer + verifier reason were already rendered by the inline `VerificationBlock` → the card stayed minimal.
- **Day-0 three-prong caught D-DAY0-1 (the emit-site kind-map ordering) + D-DAY0-2 (tests already exist → extend not create)** before any code — the plan said `:814`=tool but reality was `:814`=input; grepping each `pending_approval["kind"]` literal fixed it pre-code.
- **The drive-through earned its keep**: it proved the kind-aware card + the reject-with-note + the bounded coached turn end-to-end — exactly the 57.99 gap, now closed in the live UI.

## Q4 — What to improve / lessons

- **D-DAY3-1 (the recurring full-scope black)**: `black --check src tests` (FULL scope) caught a 1-file reformat (`test_sse.py` — my hand-written 3-line `ApprovalRequested(...)` that black collapses to a canonical 1-line). The 57.98 lesson (run black on the FULL scope, not a changed-files subset, before push) held — a subset black would have missed it → CI red. **Reaffirmed: always `black --check src tests` before push.**
- **Forced-fail drive-through fixtures (the 57.99 D-DAY3-2 family)**: a *strict* judge prompt ("you MUST reject…") tripped Azure's jailbreak content-filter on some judge calls (`judge_error` → fail-closed → still a fail → escalate fires correctly, but noisy). And the forced-fail *reason text*, re-injected as a correction, drifted the un-coached answers. Both are deliberate-forced-fail artifacts, not product behavior — but the lesson: a forced-fail judge prompt should be **soft** (instruct a plain `{"passed": false}` without adversarial/jailbreak phrasing) to avoid the content-filter, and the drive-through narration must clearly separate fixture artifacts from the feature under test.
- **The note textarea had no mockup source** — handled by reusing confirmed mockup tokens (`--radius-sm`/`--border`/`--bg-1`/`--fg`); `check:mockup-fidelity` baseline (HEX_OKLCH 53) stayed unchanged. The mockup-fidelity rule's "design-system vocab for new elements with no mockup counterpart" worked cleanly.

## Q5 — Anti-pattern audit (04 / 11 points)

- AP-1 (pipeline-as-loop): N/A — the 5 emit sites just pass an extra kwarg; no loop control-flow change. `check_ap1` green.
- AP-4 (Potemkin): ✅ the kind-aware reject + note input are exercised by 5 frontend unit tests + the drive-through; the rejected event-ordering heuristic (a Potemkin signal) was explicitly NOT taken.
- AP-2 (no orphan / phantom code): ✅ the wire field is consumed end-to-end (loop → sse → wire → generated type → store → card); the demo fixture was fixed (no orphan stale construction).
- AP-11 (version suffix / naming): ✅ no `_v2`; `kind` reflects the real pause kind.
- All others N/A or ✅ (no new event type → `check_event_schema_sync` green; LLM SDK leak 0; the wire field touches Cat 12 / Cat 9 / frontend cleanly).

## Q6 — Gate evidence

- Backend: mypy `src` **0/353** · `run_all` **10/10** (`check_event_schema_sync` green — field added, count unchanged) · black/isort/flake8 **FULL `src tests` (656 files)** clean · pytest **2300 passed + 4 skipped** (baseline 2303 → +1, zero deletion).
- Frontend: build (tsc -b) **exit 0** · lint clean (no `--silent`) · `check:mockup-fidelity` HEX_OKLCH baseline **53 unchanged** · Vitest **782 passed** (777 + 5).
- Generated diff: ONLY `approval_requested.kind` (events.json + loopEvents.generated.ts); 22 wire types unchanged.
- **Drive-through PASS** (the REJECT half): real UI + backend + Azure gpt-5.2 + a forced-fail real-LLM judge → escalate pause (`kind: verification`) → Reject reveals the note textarea → Reject & coach → Decision: REJECTED + resume → a coached turn re-answers with the note → bounded terminal `verification_failed`. Screenshots in `artifacts/`.

## Q7 — Carryover (→ next-phase-candidates.md)

1. **A rich verification-specific approval card** (frontend) — re-render the held answer + the verifier reasons richly inside the card (today the inline `VerificationBlock` shows them above the card — sufficient, not gold-plated).
2. **The `ApprovalCard.tsx` fallback widget** — make the legacy 53.5 dual-emit fallback card kind-aware too (low priority; the canonical chat-inline `HITLTurn` is the live path).
3. **Soft forced-fail judge template for drive-throughs** — a reusable `{"passed": false}` judge prompt that avoids Azure's content-filter (the D-DAY3-1/57.99-D-DAY3-2 family).
4. **A3 — trace-aware critique** + cheap-judge accuracy benchmark (design-note 24/25 carryover).
5. **Per-tenant verification mode/policy** (Config 分層 = workflow C / C3).
6. **Multi-round human coaching** (>1 turn — A2 bounds to one).

---

## Design Note Extract (spike sprint only)

**N/A** — this is a **feature-continuation** (it completes the 57.99 A2 leg's reviewer UI; reuses the shipped `resume()` `kind="verification"` + `ApprovalDecision.reason` + the inline `VerificationBlock`). Per `.claude/rules/sprint-workflow.md §Step 5.5`, feature-continuation sprints do NOT extract a design note. Record = CHANGE-067 + `17-cross-category-interfaces.md` (the `approval_requested` wire +`kind`) + `25-verification-in-loop-design.md` §4 (the A2 reviewer UI → SHIPPED).
