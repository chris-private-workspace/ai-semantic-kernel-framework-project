# Sprint 57.21 — Progress

**Sprint**: 57.21 — AD-ChatV2-Full-Mockup-Fidelity Phase-1
**Branch**: `feature/sprint-57-21-chatv2-mockup-fidelity-phase-1`
**Plan**: [sprint-57-21-plan.md](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-21-plan.md)
**Checklist**: [sprint-57-21-checklist.md](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-21-checklist.md)
**Base commit**: `ebc0dc60` (main HEAD after Sprint 57.20 closeout PR #151 merge)

---

## Day 0 — 2026-05-17 — Setup + 三-prong + Playwright MCP reference captures

### Accomplishments

- Sprint 57.21 plan landed (~600 lines; mirrors Sprint 57.20 format: 12 sections; YAML frontmatter; Group A-E user stories; calibration class `frontend-mockup-direct-port` 0.55 2nd application)
- Sprint 57.21 checklist landed (Day 0-4 + Anti-Pattern self-check + Carryover; 5 sub-sections per Day matching Sprint 57.20 cadence)
- Feature branch created: `feature/sprint-57-21-chatv2-mockup-fidelity-phase-1` from main `ebc0dc60`
- Progress.md + claudedocs skeleton + DRIFT-REPORT-PHASE1.md skeleton created
- Day 0 三-prong verify (see below)
- Playwright MCP reference captures (see below)

### Drift findings (Day 0 三-prong)

_Catalogued via plan-vs-repo grep before Day 1 code starts._

**Prong 1 — Path verify** ✅ all confirmed:

- `frontend/src/features/chat_v2/components/blocks/` does NOT exist (✅ plan expects create Day 2)
- `frontend/src/features/chat_v2/components/inspector/` does NOT exist (✅ plan expects create Day 4)
- `frontend/src/features/chat_v2/components/turns/` does NOT exist (✅ plan expects create Day 2)
- `frontend/src/features/chat_v2/fixtures/` does NOT exist (✅ plan expects create Day 3)
- `reference/design-mockups/page-chat.jsx` = 533 lines ✅
- 9 existing chat_v2 files (types.ts / chatStore.ts / chatService.ts / useLoopEventStream.ts / 5 components) ✅

**Prong 2 — Content verify** ✅ key assertions confirmed:

- `chatStore.ts` `mergeEvent` confirmed at L72 (signature) + L120 (impl) + discriminated union switch with cases for `loop_start` (L125) / `turn_start` (L135) / `approval_requested` (L215) / `approval_received` (L235) ✅
- `useLoopEventStream` hook at L38 of `hooks/useLoopEventStream.ts` ✅
- `governanceService.decide` confirmed at `features/governance/services/governanceService.ts:71` → wraps `POST /api/v1/governance/approvals/{id}/decide` ✅ — HITL workflow preservation viable
- `STYLE.md §3` confirms risk color palette + Sprint 57.18 4 risk tokens (`text-risk-{low,medium,high,critical}`)

**Prong 3 — Schema verify** N/A this sprint (pure frontend; 0 DB schema work).

**D-PRE-1** (scope confirmation, NOT shift): Sprint 57.18 wired 4 risk tokens (`text-risk-{low,medium,high,critical}` at `hsl(150 60% 45%)`/`hsl(38 92% 50%)`/`hsl(20 90% 55%)`/`hsl(0 70% 40%)`) per STYLE.md §2 table L128-131. **Plan should use these tokens** for HITLTurn severity rendering instead of arbitrary `text-[#hex]`. Caveat: `approval-card.spec.ts` sentinel `#b71c1c` (`hsl(0 70% 40%)` ≈ `text-risk-critical`) — token version may break exact hex literal assertion. Mitigation: Day 2 ApprovalCard rewrite either (a) updates spec to assert `text-risk-critical` class, OR (b) preserves `#b71c1c` arbitrary literal for sentinel via `text-[#b71c1c]` per STYLE.md §3 escape hatch. Decision at Day 2 time.

**D-PRE-2** (in-scope clarification): Mockup `ChatHeader` (page-chat.jsx L93-121) has chat-specific elements NOT covered by Sprint 57.20 NEW global Topbar:
- Severity icon (gradient red→orange)
- Session title + agent badge + model badge + "provider: neutral" + N turns label
- Streaming live dot
- Loop / Audit buttons (right-side ghost buttons)
- Panel-toggle buttons (left: toggle SessionList; right: toggle Inspector)

Plan §Technical Spec ChatLayout.tsx 3-col rewrite (Day 3) **includes ChatHeader** within ChatLayout — NOT in global Topbar. Update plan §File Change List to explicitly list ChatHeader component (NEW or inlined into ChatLayout.tsx).

**D-PRE-3** (in-scope addition): Mockup `HITLTurn` uses `<RiskBadge level="high" />` (page-chat.jsx L291) — does not exist in current chat_v2 codebase. STYLE.md §3 shows pattern `<span className={cn("font-bold", RISK_TEXT_CLASS[risk] ?? "text-muted-foreground")}>{risk}</span>` (L87). Day 2 HITLTurn either:
- (a) Create `components/ui/RiskBadge.tsx` (~30 lines) reusable across HITL + governance pages, OR
- (b) Inline the styling pattern from STYLE.md §3 within HITLTurn.tsx

Decision at Day 2 time — preference (a) for reusability if governance/ApprovalList also benefits.

**D-PRE-4** (env / out-of-scope but noted): Day 0 Playwright MCP attempts to capture authenticated `/chat-v2` repeatedly redirected to `/auth/login` despite valid JWT in `localStorage.ipa-auth-storage`. Likely cause: RequireAuth's async `/auth/me` check fails (backend `/auth/me` returns 401 → handleAuthExpired → redirect). NOT a Sprint 57.21 scope issue — it's an env setup issue. Day 0 baseline screenshots show login page; mockup capture (`mockup-chat-v2-1440x900.png`) is the critical visual target. Day 4 post-state capture will need fresh dev-login + immediate screenshot, OR `await page.waitForSelector('[data-testid="chat-v2-root"]')` to bypass race condition. Document in DRIFT-REPORT-PHASE1 §Verification table.

**Go/no-go**: Scope shift verdict = **0%** (all 4 findings are clarifications, in-scope additions, or env notes; no scope reduction or expansion). → **GO Day 1**.

### Playwright MCP reference captures (Day 0.4) — completed

| Artifact | Path |
|----------|------|
| ✅ **Mockup chat 1440×900 (CRITICAL)** | `claudedocs/4-changes/sprint-57-21-chatv2-fidelity-phase-1/screenshots/mockup-chat-v2/mockup-chat-v2-1440x900.png` |
| ⚠️ Prod-pre attempt 1 (redirect to login) | `screenshots/prod-chat-v2-pre/prod-chat-v2-pre-attempt1-redirect-to-login.png` |
| ⚠️ Prod-pre attempt 2 (redirect to login after dev-login) | `screenshots/prod-chat-v2-pre/prod-chat-v2-pre-attempt2-redirect-to-login.png` |
| ✅ Prod root post-dev-login (authenticated home page baseline) | `screenshots/prod-chat-v2-pre/prod-root-post-dev-login.png` |
| ⚠️ Prod chat-v2 attempt 3 (race redirect) | `screenshots/prod-chat-v2-pre/prod-chat-v2-attempt3-race-redirect.png` |

The mockup screenshot is the canonical visual target for Day 1-4 fidelity verification.

### Notes / decisions

- **Anti-stop rule**: Per `memory/feedback_tool_result_is_not_turn_boundary.md`, tool result is progress signal NOT turn boundary. Day 0 will batch sub-tasks where possible.
- **Mockup-Fidelity Hard Constraint**: All UI work must 1:1 mockup; functional gaps via fixture + AP-2 demo banner; backend gaps deferred per Sprint 57.21 plan §Out of Scope.

### Estimate vs actual

(populated at Day 0 EOD)

---

## Day 1 — _pending_

## Day 2 — _pending_

## Day 3 — _pending_

## Day 4 — _pending_
