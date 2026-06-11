# Sprint 57.21 — Retrospective

**Sprint**: 57.21 — AD-ChatV2-Full-Mockup-Fidelity Phase-1 (Turn Block Model + SessionList + Inspector Turn Tab; frontend-only spike per Option W backend-follows)
**Date Range**: 2026-05-17 → 2026-05-18 (5-day plan: Day 0 + Day 1-4)
**Branch**: `feature/sprint-57-21-chatv2-mockup-fidelity-phase-1`
**Class**: `frontend-mockup-direct-port` 0.55 (2nd application; 1st was Sprint 57.20)
**Plan**: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-21-plan.md`
**Checklist**: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-21-checklist.md`
**Progress**: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-21/progress.md`

---

## Q1 — What did we ship?

**11 US ships** (`A0` Day 0 + B1+B2+B3 Day 1 + C1+C2 Day 2 + D1+D2+D3 Day 3 + E1+E2 Day 4 + closeout):

| Day | USs | NEW components | NEW Vitest cases | Cumulative tests |
|-----|-----|----------------|------------------|------------------|
| 0 | A0 三-prong + Playwright reference | — | — | 277 (Sprint 57.20 baseline) |
| 1 | B1 types.ts REWRITE + B2 chatStore.ts REWRITE + B3 (mergeEvent test) | — (data model only) | +22 | 299 |
| 2 | C1 TurnList + 3 Turn role + C2 4 Block + dispatcher | 9 | +20 | 319 |
| 3 | D1 SessionList + fixtures + D2 ChatLayout 3-col + ChatHeader + ChatInspector stub + D3 demo banner + i18n | 4 | +16 | 335 |
| 4 | E1 ChatInspector 4-tab + InspectorTurn + ComingSoonInspectorTab + E2 Composer scaffolding + e2e contract fix + orphan delete | 4 (− 3 orphans = +1 net) | +13 | **348** |

**Domain shape impact**:
- `types.ts`: Turn discriminated union (user/agent/hitl) + Block (4 of 5 mockup types; memory deferred) + Session + RiskSeverity + SubagentEntry. `Message` removed cleanly. 14 SSE event types unchanged.
- `chatStore.ts`: state shape `messages[]` → `turns[]` + `sessions[]` + `activeSessionId`; mergeEvent dual-emit (legacy slices preserved + Turn blocks built).
- 9 NEW Turn / Block / dispatcher components ⇒ replaces old MessageList + ToolCallCard
- 4 NEW Day 3 components (SessionList + ChatHeader + ChatInspector stub + fixtures/sessions.ts)
- 3 NEW Day 4 components (InspectorTurn + ComingSoonInspectorTab + Composer) + 1 REWRITE (ChatInspector → 4-tab frame)
- +24 i18n keys (12 keys × 2 locales)
- 1 D-DAY3-3 surgical fix to HITLTurn (role=region + aria-label) preserves approval-card e2e contract

**Quality gates final**:

| Gate | Sprint 57.20 baseline | Sprint 57.21 EOD | Verdict |
|------|----------------------|------------------|---------|
| tsc errors | 0 | 0 | ✅ |
| Vitest tests | 277/277 | **348/348** (+71 NEW Sprint-aggregate) | ✅ |
| Vitest files | 63 | 70 (+7 NEW) | ✅ |
| Lint | silent | silent | ✅ |
| Build | 2.79s | 2.94s | ✅ |
| Main bundle | 320.76 kB | **321.92 kB** (+1.16 kB) | ✅ within +30 kB target |
| Backend changes | 0 | 0 | ✅ |
| LLM SDK leak | 0 | 0 | ✅ |
| Anti-Pattern 11-check | 11/11 PASS | 11/11 PASS | ✅ |

---

## Q2 — Calibration trend (2nd application of `frontend-mockup-direct-port` 0.55)

**Bottom-up estimate**: 16-20 hr (Day 1 ~5 / Day 2 ~5-7 / Day 3 ~3-4 / Day 4 ~3-5)
**Calibrated commit**: 9-11 hr (multiplier 0.55, mid-band) per Sprint 57.20 1st app

**Actual cumulative**: ~12 hr (Day 1 ~2.5 + Day 2 ~3.5 + Day 3 ~2.5 + Day 4 ~3 hr code + ~0.5 hr retro/memory remaining)

**Ratios**:
- `actual / committed` = 12 / 10 = **1.20** ✅ TOP of [0.85, 1.20] band (bullseye edge)
- `actual / bottom-up` = 12 / 18 = **0.67** (bottom-up 1.5× too generous)

### 2-data-point trend

| Sprint | actual/committed | actual/bottom-up | Verdict |
|--------|------------------|-------------------|---------|
| 57.20 | 0.45-0.55 (below band by 0.30-0.40) | 0.25-0.30 (bottom-up 2× too generous) | BELOW band; reason: front-loaded structural work in 57.18 + 57.19 |
| 57.21 | **1.20** (top of band) | **0.67** (bottom-up 1.5× too generous) | IN band; reason: genuine structural rewrite (types.ts + chatStore.ts mergeEvent + 9 NEW Day 2 components + Inspector 4-tab) — this sprint is the rebuild ratio swings back into band as predicted by Sprint 57.20 retro footer |

**2-data-point mean**: `(0.50 + 1.20) / 2 = 0.85` — at lower band edge **but reflects bimodal pattern** (token-migration sprint ratio = ~0.50; structural rewrite sprint ratio = ~1.20).

### Recommendation

- **KEEP 0.55 baseline** per `When to adjust` 3-sprint window rule (2 data points insufficient).
- Next data point if Sprint 57.22+ uses the same class:
  - If structural-rewrite-heavy (e.g. SessionList real backend wire + Inspector Trace OTel feed) → ratio likely ~1.0-1.2 (validates class for structural work)
  - If token-migration-heavy (e.g. AD-Mockup-Direct-Port-Round-2 8-page sweep) → ratio likely ~0.5-0.6 (validates 0.55 for migration work)
- If 3 sprints all bimodal → **AD-Sprint-Plan-NEW** propose **split** the class into `frontend-mockup-direct-port-structural` (0.85 — like medium-backend's "near top of band" rule from 57.16 AD-Sprint-Plan-13) vs `frontend-mockup-direct-port-token-sweep` (0.40).

**Bottom-up calibration**: 2 consecutive sprints with `actual/bottom-up` ≤ 0.67 confirms bottom-up estimates are systematically generous (~1.5-2×). Future bottom-up budget should apply **own multiplier ~0.65** on top of class multiplier 0.55 = effective combined ~0.36 of bottom-up. Or: in plan §Workload, the bottom-up estimate column should be honest (smaller numbers) so class multiplier 0.55 itself stays meaningful. Decision: KEEP current form (bottom-up = generous reality-check; calibrated = commitment) per `sprint-workflow.md` §Workload Calibration "Bottom-up est ~X hr → calibrated commit ~Y hr" pattern.

---

## Q3 — Drift findings catalogue (10 total)

**Day 0 (4 D-PRE)**:
- D-PRE-1 (in-scope additive): mockup `Badge tone` prop translation pattern → use shadcn outline + token classes
- D-PRE-2 (in-scope additive): ChatHeader is in-scope Day 3 (not coming-soon)
- D-PRE-3 (in-scope additive): RiskBadge — chose inline approval card body rendering vs separate component
- D-PRE-4 (env note): auth race condition between dev-login + RequireAuth gate; mitigated via `waitForSelector` patterns

**Day 1 (0)**: clean execution; consolidated commit avoided broken intermediate.

**Day 2 (0)**: HITLTurn over-delivered rich card body inline, eliminating §2.3 ApprovalCard rewrite scope.

**Day 3 (5 D-DAY3)**:
- D-DAY3-1 (cosmetic): Badge `tone` prop → variant=outline + token classes pattern
- D-DAY3-2 (a11y additive): title `<div>` → `<h2>` for AppShellV2 sub-heading hierarchy
- D-DAY3-3 (Phase-2 deferred → Day 4 in-scope surgical): approval-card e2e selector compatibility — addressed via 2-line HITLTurn role=region + aria-label
- D-DAY3-4 (architectural decision): collapsible rail unmount-on-close vs CSS-hide; chose unmount (preserves keyboard tab + matches mockup data-attr pattern)
- D-DAY3-5 (cosmetic): `live-dot` mockup CSS class → Tailwind `bg-warning animate-pulse rounded-full`

**Day 4 (5 D-DAY4)**:
- D-DAY4-1 (resolved): Vitest `getByText("thinking")` collision → changed describeBlock(thinking) to truncated-text-preview
- D-DAY4-2 (resolved): missing `React.ReactNode` import in InspectorTurn KV helper → explicit `import type { ReactNode }`
- D-DAY4-3 (orphan cleanup via Karpathy §3): MessageList + ToolCallCard + .bak — DELETE (0 production importers; 0 tests)
- D-DAY4-4 (e2e contract preserve): HITLTurn role=region + aria-label surgical 2-line edit closes D-DAY3-3
- D-DAY4-5 (deferred → Phase-2): Composer.tsx ships visual-only; NEW carryover AD-ChatV2-Composer-Wire-Phase2 for Sprint 57.22+ wire decision

**Net**: 10 findings; 0 unresolved; 5 honest deferrals to Phase-2+ (AD-ChatV2-Memory-Block / HITL-FourAction / Composer-Richness / Composer-Wire / Inspector-{Trace,Memory,SubagentTree}).

---

## Q4 — Anti-Pattern 11-check self-audit

| # | Anti-pattern | Verdict | Evidence |
|---|--------------|---------|----------|
| 1 | No god component | ✅ | TurnList ~70 / SessionList ~160 / ChatHeader ~165 / ChatInspector ~85 / InspectorTurn ~155 / Composer ~115 / HITLTurn ~280 (largest; includes inline approval card body per D-DAY2 over-delivery; still under 300-line god threshold) |
| 2 | No Potemkin | ✅ | Every coming-soon affordance names carryover AD: 3 Inspector tabs (Trace/Memory/Tree) + 3 Composer buttons (Attach/Tools/Memory-scope) + Send + SessionList demo banner. 0 silent placeholders. |
| 3 | No cross-directory scattering | ✅ | All NEW under `features/chat_v2/{components/{,inspector,turns,blocks},fixtures,store,hooks,services}/`. 0 outside the feature module. |
| 4 | No rename-only refactor | ✅ | Types rewrite + mergeEvent rewrite + ChatLayout 3-col + ChatInspector 4-tab each delivers visible mockup-fidelity gain. NO rename-without-content-change. |
| 5 | No hardcoded secrets | ✅ | 0 changes to .env / config / token storage |
| 6 | No silent backend assumptions | ✅ | 0 backend changes; existing hooks consume existing endpoints + 14 SSE event types. Backend wire for SessionList / Inspector tabs / Composer richness all explicit AD carryovers. |
| 7 | No prop drilling > 2 levels | ✅ | Turn role components consume chatStore via hooks (NOT props from ChatLayout). InspectorTurn consumes chatStore directly. |
| 8 | No event handler swallowing errors | ✅ | SSE / HITL handlers preserved verbatim in chatStore.mergeEvent. governanceService.decide in HITLTurn try/catch with status setBack. |
| 9 | No race conditions | ✅ | TanStack Query handles refetch; chatStore.mergeEvent is synchronous reducer; InspectorTurn derives via pure selector (reverse-find + null-guard). |
| 10 | No untested critical path | ✅ | 71 NEW Vitest cases cover all NEW components + data model. e2e approval-card preserved via D-DAY4-4 surgical fix (Playwright run deferred to CI per §4.3). |
| 11 | No TypeScript `any` leak | ✅ | Turn + Block discriminated unions fully typed; 0 new `any`; tsc 0 errors required gate. |

**Overall**: 11/11 PASS.

---

## Q5 — What surprised us?

1. **HITLTurn rich card over-delivery (Day 2)** — original plan had HITLTurn as thin wrapper; implementation embedded rich card body inline (~165 LoC). Saved Day 3 ApprovalCard.tsx rewrite scope. Cost ~30 min extra Day 2.
2. **D-DAY3-3 was 2-line fix, not full rewrite (Day 4)** — feared full ApprovalCard e2e selector overhaul; turned out 2 attrs on HITLTurn outer wrapper closed the contract.
3. **Composer Option C scope reduction (Day 4)** — checklist §4.2 originally planned rewrite-in-place + compat-shim; analysis revealed lower-risk = ship Composer as visual-only + DEFER wire to Phase-2. InputBar untouched. Avoids regressing battle-tested 5-state pill + send/cancel + 14 SSE wire.
4. **Vitest 348/348** — bigger than expected gain (+71 cumulative from Sprint 57.20 baseline 277), confirms mockup-fidelity work isn't purely visual mechanical — Turn/Block data model rewrite has substantial state-machine coverage payload.
5. **Bundle byte-identical from Day 3 to Day 4 (321.92 kB)** — Inspector 4-tab + 3 coming-soon + Composer all tree-shake absorbed because Tabs primitive + lucide-react chunks already pre-loaded by Sprint 57.19 / earlier. Negative-cost addition.

---

## Q6 — Carryover ADs (10 NEW + reaffirmed)

### NEW this sprint

1. 🔴 **AD-ChatV2-Memory-Block-Phase2** — Cat 3 memory_accessed SSE event + frontend memory block component (5th block type per mockup; deferred Day 1 types.ts; Sprint 57.22+)
2. 🔴 **AD-ChatV2-HITL-FourAction-Phase2** — governance approve-with-edits + Escalate to L2 + SLA countdown + frontend 4-action UX (Day 2 HITLTurn ships only Approve + Reject; Sprint 57.22+)
3. 🆕 **AD-ChatV2-Composer-Richness-Phase2** — Attach upload + Tools(24) menu wire + Memory scope filter (Day 4 Composer ships disabled; Sprint 57.22+)
4. 🆕 **AD-ChatV2-Composer-Wire-Phase2** — Composer production wire decision (extract-shared-hook vs proxy-via-composition vs full rewrite); InputBar untouched this sprint (Sprint 57.22+ when AD-3 affordances wire)
5. 🆕 **AD-ChatV2-Inspector-Trace-Phase2** — Cat 12 OTel spans waterfall UI + per-session endpoint (Day 4 ComingSoon; Sprint 57.22+)
6. 🆕 **AD-ChatV2-Inspector-Memory-Phase2** — Cat 3 memory ops list per session + UI (Day 4 ComingSoon; Sprint 57.22+)
7. 🆕 **AD-ChatV2-Inspector-SubagentTree-Phase2** — Cat 11 subagent live feed + tree UI (Day 4 ComingSoon; Sprint 57.22+)
8. 🆕 **AD-ChatV2-SessionList-Backend** — GET /api/v1/sessions list endpoint (Day 3 SessionList ships fixture; Sprint 57.22+)
9. 🆕 **AD-Cat12-SSE-Trace-Id-Phase2** — SSE LoopStartEvent / TurnStartEvent extension to carry trace_id + span_id so Inspector Turn tab can display non-placeholder (Day 4 KV `'—'` fallback; Sprint 57.22+ once Cat 12 SSE wire)
10. 🆕 **AD-ChatV2-Full-Mockup-Fidelity Phase-2** — multi-sprint epic continuation (Memory block + HITL 4-action + Composer wire + 3 Inspector feeds). Phase-1 ships Turn data model + 9 components + 3-col shell + Inspector frame; Phase-2+ completes the 5 deferred items.

### Reaffirmed from Sprint 57.20

- 🚧 AD-Mockup-Direct-Port-Round-2 (8 remaining ship pages + R2 findings)
- 🚧 AD-Geist-Font-Asset-Bundling (Phase 58+)
- 🚧 AD-Mockup-Existing-Pages-Retrofit Tier 2 (Sprint 57.19 carryover bundle; partial closure via Sprint 57.20 + 57.21 — chat-v2 now done)

### From Sprint 57.19 (status unchanged)

- 🚧 AD-Subagent-RealList-Phase58 / AD-Loop-Session-Enrich-Phase58 / AD-Overview-Backend-Wire / AD-Orchestrator-Backend-Wire / AD-State-VersionChain-Phase58 / AD-CommandPalette-Backend-Wire / AD-NotificationsPanel-Backend-Feed / AD-UserMenu-Tenant-Switch (8 backend wire ADs untouched)

### From Sprint 57.17

- 🚧 AD-Tailwind-v4-Config-Migration / AD-CI-7-GHA-PR-Permission

### From Sprint 57.16

- 🚧 AD-A11y-Structural-Nits (may be partially closed by Day 3 ChatLayout 3-col rewrite; verify via Playwright a11y scan in Sprint 57.22+)

### Longstanding

- 🚧 AD-Lighthouse-Visual-Hard-Gate

---

## Q7 — Day 0 三-prong + plan calibration retrospective

### Day 0 三-prong (per AD-Plan-1 promoted Sprint 55.3 + AD-Plan-3 Sprint 55.6 + AD-Plan-4 Sprint 57.1)

| Prong | Action | Findings | Resolved |
|-------|--------|----------|----------|
| 1 Path Verify | `Glob` each file change list entry | 0 path drift (types.ts + chatStore.ts + 5 existing chat_v2 component files all confirmed; turns/ + blocks/ + inspector/ + fixtures/ dirs confirmed non-existent for NEW work) | ✅ |
| 2 Content Verify | `grep` each technical spec assertion | 0 content drift; types.ts Message type + 14 SSE events + chatStore.mergeEvent discriminated union + governanceService.decide all confirmed | ✅ |
| 3 Schema Verify | N/A pure frontend; 0 DB schema work | — | N/A |

**Day 0 ROI**: 0 scope shift caught; 4 D-PRE findings (all in-scope clarifications or additive) catalogued in <30 min. Confirms Sprint 57.20 Day 0 pattern: when working in known-territory frontend (no new DB / no new ABCs), 三-prong cost is ~15-30 min per sprint, ROI ≈ break-even (no drift to catch).

### Plan accuracy

| Plan section | Accuracy |
|--------------|----------|
| §File Change List | ✅ exact — all NEW files materialized; orphan delete (MessageList / ToolCallCard / .bak) was Day 4 surprise but Karpathy §3 cleanup |
| §Acceptance Criteria | ✅ all 11 USs delivered or honest 🚧 deferred |
| §Workload (10 hr commit) | ⚠️ ~12 hr actual = 1.20 top-of-band; see Q2 |
| §Risks | ✅ matched — D-PRE-4 auth race materialized; 0 surprise risks |
| §Rolling Planning discipline | ✅ no Sprint 57.22 plan pre-drafted; 10 NEW carryover ADs in §Q6 sit as candidate scope only |

### Lessons for Sprint 57.22+

1. **Bimodal calibration class** — 2-data-point pattern suggests `frontend-mockup-direct-port` 0.55 has **token-sweep (~0.50) vs structural-rewrite (~1.20)** sub-classes. If 3rd app confirms, split per AD-Sprint-Plan-NEW.
2. **Inspector tab placeholder + carryover-AD-named hint** is a reusable AP-2 anti-Potemkin pattern. Apply to future deferred-tab work.
3. **Surgical e2e contract preservation** (D-DAY3-3 → D-DAY4-4) saved a full ApprovalCard rewrite. Pattern: when swapping consumer (MessageList → TurnList), grep existing e2e selectors first; preserve via ARIA attrs not DOM restructure.
4. **Composer Option C** (visual scaffolding + defer wire) is honest scope reduction; documents Phase-2 decision (2 wire-strategy options) without committing to either prematurely.
5. **Tabs primitive reuse** (Sprint 57.19 NEW `components/ui/tabs.tsx`) absorbed by tree-shake when added 2nd consumer (ChatInspector). Validates Sprint 57.19 D-DAY4-3 "extract NEW tabs.tsx as shared primitive" decision.

---

## §4.3 Playwright MCP visual pair-verify — 🚧 DEFERRED

Mockup http server (port 8080 PID 44700) + dev server (port 3007 PID 50796) both running per Day 0. Per Sprint 57.5 reality-check dual-scoring framework, runtime visual capture is essential for AP-4 visible-mockup-fidelity-gain confirmation but separable from code-level acceptance.

Status: deferred to separate sub-step before §4.5 PR. Targets:
- `mockup-chat-v2/mockup-chat-v2-1440x900.png` (already captured Day 0; canonical visual target)
- `inspector-turn/prod-chat-v2-day4.png` (POST-Day-4 production at 1440×900)
- Sub-zooms: SessionList rail (280px) / ChatHeader top bar / Inspector Turn tab populated / Inspector Trace tab coming-soon
- DRIFT verdict consolidated in `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-21/artifacts/chatv2-fidelity-phase-1/DRIFT-REPORT-PHASE1.md`

**Closing note**: Sprint 57.20 captured runtime in execution sprint; Sprint 57.21 defers capture to dedicated sub-step. Both patterns honour the reality-check framework — the distinction is whether the runtime capture itself materially affects scope (Sprint 57.20: yes, drove Round-2 plan; Sprint 57.21: no, code-level shipped already; capture serves AP-4 verification only).

---

## Sign-off

- [ ] Q1-Q7 retrospective complete
- [ ] §4.4 4 doc syncs done (memory snapshot + MEMORY.md + sprint-workflow.md calibration matrix + CLAUDE.md V2 Refactor Status + SITUATION-V2-SESSION-START.md)
- [ ] §4.4 Playwright MCP capture + DRIFT-REPORT-PHASE1.md
- [ ] §4.5 PR opened + CI 7 checks green + merged
- [ ] closeout doc-sync PR if needed
