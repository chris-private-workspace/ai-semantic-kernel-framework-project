# Sprint 57.116 Retrospective — Skills Force-Load Inspector Affordance (user-turn skill chip)

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-116-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-116-checklist.md) · [Progress](./progress.md) · CHANGE-083

**Closed**: 2026-06-14 · **Branch**: `feature/sprint-57-116-skills-inspector-affordance` · **Base**: `main` `fc385a87` (post-#290)

---

## Q1 — What was delivered?

The Skills epic's **first UX affordance** (closes `AD-Skills-Inspector-Affordance`): the 57.115 deterministic `/skill-name` force-load — previously invisible after send — now shows a "⚡ {skill}" chip on the user turn. A **server-confirmed** `active_skill` additive field on the opening `loop_start` SSE event (count stays 24; `sse.py` defaults it null + `event_wire_schema.py` declares it + codegen regen + the router injects the validated force-load name in `_stream_loop_events`) drives a `.route-pill` chip stamped onto the triggering user turn (`chatStore` loop_start case, truthy-guarded). `loop.py` / `events.py` / the `LoopStarted` dataclass / `read_skill` / the resume mirror UNTOUCHED — skill knowledge stays out of Cat 1. Tests: +7 backend (4 unit + 3 e2e SSE) + 6 FE Vitest. Drive-through ALL 3 cases PASS (real Azure gpt-5.2).

## Q2 — Estimate accuracy / calibration

- Scope class **`frontend-feature-with-event-wire-addition` 0.55 — 3rd data point**.
- Bottom-up est ~6 hr → class-calibrated commit ~3.3 hr (mult 0.55, 3-segment form; parent-direct `agent_factor` 1.0).
- Actual ≈ slightly over the commit — ratio **~1.1-1.2 IN band** (upper edge). The over-edge = the one unplanned detour: the generated `active_skill` is a REQUIRED field → `tsc -b` (not the Vitest transform) surfaced a demo-fixture literal break + a union-narrowing fix in the loop_start map. Caught + fixed in ~10 min; no scope shift.
- 3-data-point window: 57.100 ~1.0 + 57.108 ~1.05-1.1 + 57.116 ~1.1-1.2 → mean **~1.05-1.1 IN band → KEEP 0.55** (validated; the class is now 3-point confirmed).
- **Agent-delegated: no** (parent-direct; the 2 Day-0 Explore recon agents only). The slice was ~6 hr of precise small edits — the router-augment design decision (vs the agent's thread-through-loop option) + the truthy-guard last-user-turn stamp were the only subtleties, both better kept parent-direct.

## Q3 — What went well?

- **Day-0 三-prong head-start (2 Explore agents) was high-ROI**: it surfaced the wire taxonomy, the parity-guard constraint (the serializer default `None` is mandatory), the `chatStore` loop_start case shape, and the `.route-pill` reuse — all confirmed precisely before code. The 1 real drift (`LoopStarted` not imported in `router.py`) was caught Day-0, not Day-1.
- **The router-augment design (overriding the Explore agent's recommendation) paid off**: keeping `active_skill` out of `LoopStarted`/`AgentLoopImpl` left `loop.py`/`events.py` diff-0 (consistent with 57.115) and respected the Cat-1 boundary. The augment is ~2 lines.
- **The echo-mode SSE test (Day-1 DRY adjustment)** exercised the real router augment without a real Azure call — echo computes `forced_skill` the same router-level way as real_llm, so the SSE field is testable cheaply.
- **Drive-through gave decisive AP-4 evidence**: Leg B (a `/nonexistent` token the FE sent → no chip) proves the chip is server-confirmed, not a client echo — exactly the mislabel the design guards against.

## Q4 — What to improve / lessons

- **A REQUIRED codegen wire field breaks every existing event LITERAL, not just consumers** (Day-2): the Vitest oxc transform skips type-checking, so `npm run test` was green while `tsc -b` (build) failed on a demo fixture + a union-narrowing issue. **Lesson: after adding a required field to a codegen wire type, run `npm run build` (tsc), not only Vitest.** (Folds into the 57.108 additive-field pattern note — a NULLABLE-but-required field is the trap.) Single data point; codify into sprint-workflow only if it recurs.
- The `loop_start` map refactor: an initial `let next = t; if (...) next = {...next, X}` form loses TS union narrowing — narrow `t` directly per branch (`return` early). Minor, caught by the build.

## Q5 — Anti-pattern audit (04-anti-patterns.md)

- **AP-1** (pipeline-as-loop) N/A. **AP-2** (side-track): ✅ the chip rides the 主流量 (force-load → router augment → loop_start → store → chip). **AP-3** (cross-dir scatter): ✅ wire field in chat api / store+render in chat_v2. **AP-4** (Potemkin): ✅ the drive-through proves the chip is server-confirmed (Leg B no-chip on an invalid name) + bound to the correct turn — not a cosmetic/always-on badge. **AP-6** (speculative abstraction): ✅ additive field on an existing event, no new event TYPE. **AP-7/8/9** N/A. **AP-10** (mock vs real): ✅ the echo-mode test + the real-Azure drive-through agree. **AP-11** (version suffix): ✅ none.
- 0 violations.

## Q6 — Carryover

- `AD-Skills-Inspector-Affordance` **CLOSED**. Remaining Skills ADs carried (unchanged): `AD-Skills-Authoring-UI`, `AD-Skills-Per-Tenant-Quota`, `AD-Skills-Bundled-Scripts`, `AD-Skills-SlashMenu-Mockup`, multi-skill-per-command (YAGNI), and `AD-ChatV2-Inspector-Turn-Metadata-Wire` (the Inspector-panel metadata row — a separate slice; this sprint chose the user-turn chip).
- Process candidate (1 data point, fold into sprint-workflow only if it recurs): "after adding a REQUIRED codegen wire field, run `npm run build` (tsc), not just Vitest — the transform skips type-checking and a fixture literal break / union-narrowing issue only surfaces at build."

## Q7 — Closeout checklist

- [x] CHANGE-083 · [x] NO design note (feature continuation) · [x] retro Q1-Q7 + calibration · [x] navigators (CLAUDE.md / MEMORY.md + subfile / next-phase-candidates / sprint-workflow matrix 3rd-point) · [x] 17.md N/A (additive field, no new contract) · [ ] PR (push on user authorization)
