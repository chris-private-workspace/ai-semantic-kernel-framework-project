# Next Phase 候選 (Phase 57.22+)

**Purpose**: Open items / pending decisions / carryover ADs accumulated from prior sprint retrospectives. Single-source for "what could be next sprint". CLAUDE.md / MEMORY.md no longer carry this list per §Sprint Closeout policy ([`.claude/rules/sprint-workflow.md`](../../.claude/rules/sprint-workflow.md)).

**Selection Rule**: User explicitly selects → draft plan kicks off Sprint XX.Y; otherwise items wait here indefinitely until selected or archived.

**Updated**: 2026-05-18 (Sprint 57.21 closeout — extracted from CLAUDE.md V2 Refactor Status table per REFACTOR-001 Step 3)

---

## 🔴 Top Candidates (User-Aligned Priority)

### 1. AD-ChatV2-Full-Mockup-Fidelity Phase-2

Multi-sprint epic continuation. Sprint 57.21 Phase-1 already shipped:
- Turn Block Model
- SessionList fixture
- Inspector 4-tab frame
- Composer visual scaffolding

**Phase-2 carryover ADs** (from Sprint 57.21 retro):
- AD-ChatV2-Memory-Block-Phase2
- AD-ChatV2-HITL-FourAction-Phase2
- AD-ChatV2-Composer-Richness-Phase2
- AD-ChatV2-Composer-Wire-Phase2
- AD-ChatV2-Inspector-{Trace, Memory, SubagentTree}-Phase2
- AD-ChatV2-SessionList-Backend
- AD-Cat12-SSE-Trace-Id-Phase2

**Mode**: Pick subset for Phase-2 first sprint depending on backend dependency ordering. Likely structural-rewrite mode → `frontend-mockup-direct-port` ratio ~1.0-1.2 predicted.

### 2. 🆕 AD-Mockup-Direct-Port-Round-2

NEW Sprint 57.20 Day 4 DRIFT-REPORT-ROUND-2 (16 R2 findings).

**Scope** — Token migration sweep for **8 remaining ship pages**:
- cost-dashboard / memory / verification / governance + 4 governance sub-routes / sla-dashboard / admin-tenants / tenant-settings

Plus:
- 3 overlay backend wiring
- R2-A 5 cosmetic Card visual polish

**Class**: Same `frontend-mockup-direct-port` 0.55 class likely.

### 3. AD-Mockup-Existing-Pages-Retrofit Tier 1

Sprint 57.19 US-F1 DRIFT-REPORT; partially closed Sprint 57.20 via `/overview` + `/chat-v2` token migration; **folds INTO Round-2 above**.

**Scope**: 9-page retrofit Tier 1 ~10.5 hr bottom-up = ~5.8 hr calibrated commit at NEW class `mockup-fidelity-retrofit` 0.55 1st app (HYBRID: cosmetic mechanical 0.45 + structural design 0.65 + closeout 0.80).

**5 priority pages**:
- cost-dashboard (3 hr)
- chat-v2 (3 hr)
- memory (2 hr)
- verification (2 hr)
- governance (1.5 hr)

**Tier 2**: ~5.5 hr → Sprint 57.21+
**Tier 3**: ~1 hr + Round 3 epic

---

## 🟡 Mockup-Page-Port Continuation

### 4. AD-Mockup-Page-X-Port Round 3 — Auth 4

Sprint 57.19 carryover. Pages:
- register / invite / mfa / expired

**Pairing**: IAM Block B (WorkOS SCIM/SAML/org-level RBAC) per 用戶 2026-05-16 Q3 alignment「前後端同 sprint」.

### 5. AD-Mockup-Page-X-Port Round 4 — Governance 3

Sprint 57.19 carryover. Pages:
- redaction / error-policy / audit-log (DRAFT → active promote)

**Pairing**: Cat 9 endpoint extensions.

---

## 🟢 Backend Wire Bundle

### 6. AD-Backend-Wire Bundle

Sprint 57.19 4 NEW ADs:
- Subagent-RealList-Phase58
- Loop-Session-Enrich-Phase58
- Overview-Backend-Wire
- Orchestrator-Backend-Wire

**Scope**: Backend persistence + aggregation for Operations 4 pages (current fixture/stub). Can pair with retrofit work.

### 7. 🆕 AD-CommandPalette-Backend-Wire

NEW Sprint 57.19 US-D1. Tenants + sessions groups currently fixture; wire Cat 1 sessions list + Cat 12 tenants index.

### 8. 🆕 AD-NotificationsPanel-Backend-Feed

NEW Sprint 57.19 US-D2. 6 mockup items local state; Cat 12 SSE/poll feed spec TBD.

### 9. 🆕 AD-UserMenu-Tenant-Switch

NEW Sprint 57.19 US-D3. Wire tenant switching paired with Round 2 WorkOS SCIM.

---

## 🛠️ Tooling / Infrastructure / Style

### 10. AD-Tailwind-v4-Config-Migration

Sprint 57.17 carryover. Full v4 idiomatic `@theme inline {}` block 取代 `@config "../tailwind.config.ts"` + 刪 legacy v3 config file. ~6-8 hr standalone sprint, same class `frontend-css-engine-hotfix`.

### 11. AD-Post-Hotfix-Token-Audit

NEW Sprint 57.17 contrast-ratio portion. **Folds INTO** AD-Mockup-Existing-Pages-Retrofit Tier 1 work (same shadcn slate base sub-AA pairs).

### 12. 🆕 AD-Brand-Primary-Color-Decision

Sprint 57.18 D-PRE-1. Partially actioned by Sprint 57.19 US-A1 mockup indigo; finalization decision pending.

### 13. 🆕 AD-Theme-Variant-Mechanism

Sprint 57.18 D-PRE-2.

### 14. 🆕 AD-Density-Variant-Mechanism

Sprint 57.18 D-PRE-3.

### 15. AD-CI-7-GHA-PR-Permission

Sprint 57.17 carryover. `playwright-e2e.yml:163-188` auto-PR-create blocked by repo setting.

### 16. AD-Lighthouse-Visual-Hard-Gate

Baselines reliable post-57.17; required CI check.

### 17. AD-Bundle-Size code-split

### 18. AD-i18n-Feature-Namespaces

### 19. AD-A11y-Structural-Nits

Sprint 57.16 carryover. `/chat-v2` 的 `heading-order` + duplicate `<main>` landmarks moderate/minor；`/auth/callback?error` `page-has-heading-one`.

---

## 🏢 Enterprise / SaaS Stage 2

### 20. IAM Block B Spike

~12-18 hr — WorkOS SCIM/SAML/org-level. Pairs with #4 Auth 4.

### 21. Tier 1 IaC + DR Drill

~15-20 hr.

### 22. SOC 2 + SBOM

~12-15 hr.

---

## 🟣 Sprint 57.23 Auth Page Rebuild Carryovers (NEW 2026-05-18)

7 ADs from Sprint 57.23 AD-Auth-Page-Full-Rebuild-Round-2 closeout. Frontend rebuild shipped 8/8 USs with stub-501 demo banners; backend wiring deferred to Phase 58+ IAM Block B/C per Q2 frontend-only decision.

### 23. AD-Auth-Register-Backend-IAM-Block-B-Phase58
`POST /api/v1/tenants/register` real implementation. Currently 501 stub. Frontend `/auth/register` 4-step wizard fully shipped + i18n + Vitest 5 cases. Phase 58+ IAM Block B scope.

### 24. AD-Auth-Invite-Backend-IAM-Block-B-Phase58
`GET /api/v1/invites/:token` (metadata) + `POST /api/v1/invites/:token/accept`. Currently 501 stubs; frontend falls back to fixture metadata silently for GET, surfaces explicit error for POST. Frontend `/auth/invite/:token` shipped + Vitest 4 cases. Phase 58+ IAM Block B scope.

### 25. AD-Auth-MFA-Backend-IAM-Block-C-Phase58
`POST /api/v1/mfa/verify` + TOTP secret enrollment + WebAuthn credential registration backend. Currently 501 stub. Frontend `/auth/mfa` Roll-own UI shipped (TOTP 6-digit grid + WebAuthn conic ring + Simulate button) + Vitest 7 cases. Phase 58+ IAM Block C scope.

### 26. AD-Auth-MFA-Recovery-Page-Phase58
`/auth/mfa/recovery` page wire — currently displayed as `<span pointer-events-none>` with tooltip "Recovery flow pending Phase 58+ IAM Block C". Backend recovery-code generation + verification. Phase 58+ IAM Block C scope.

### 27. AD-Auth-Callback-Loading-UX-Phase58
Replace static 3-step `setTimeout` (800/1800/2800ms) with real backend SSE per-step events when WorkOS OIDC callback wiring exists. Frontend already has 3-step UI + parallel-bootstrap + min-2800ms-enforce mechanism. Phase 58+ IAM Block B scope.

### 28. AD-WorkOS-Multi-IdP-Phase58
Wire actual SAML / Microsoft / Google SSO via WorkOS. Currently 3 buttons disabled with "Enterprise SSO via WorkOS roadmap" tooltip per mockup. Backend WorkOS Multi-IdP integration. Phase 58+ IAM Block B scope. (Existed pre-57.23 as design intent; now actively blocks Sprint 57.23 login button enablement.)

### 29. AD-Sprint-57-23-Playwright-MCP-Visual-Verify-Followup
Re-run Playwright MCP visual pair-verify on Sprint 57.23 12 page-states. Day 4 closeout encountered stuck browser state from prior Sprint 57.22 session (`Error: Browser is already in use ... use --isolated`). Closure via code-level audit + Sprint 57.22 baseline + visual-regression CI mechanism. Re-run in future session with fresh browser instance. **Low priority** — line-by-line port discipline + DRIFT-REPORT verdicts (all PARITY or COSMETIC; 0 STRUCTURAL/FUNCTIONAL) already cover fidelity gate.

### 30. AD-I18n-Symmetric-Keys-Lint-Phase58
Implement automated symmetric-keys lint at `frontend/tests/unit/i18n/` that runs `jq paths(scalars)` diff between en/<namespace>.json and zh-TW/<namespace>.json on every PR. Sprint 57.23 verified manually for `auth.json`; this AD generalizes for `chat-v2.json` / `governance.json` / `tenant-settings.json` etc. ~2-3 hr.

---

## 🔵 Sprint 57.24 Decision Carryovers (NEW 2026-05-19)

### 31. AD-Memory-Structural-Rebuild-Phase58
`/memory` page rebuild — Sprint 57.22 Unit 10 audit identified STRUCTURAL severity drift: production has simple 2-tab UI (Recent / By Scope) + 3 backend-wired scopes (system/tenant/user); mockup `page-governance.jsx:462-598` has full 5-scope × 3-time-scale matrix grid + time-travel scrubber + memory-ops timeline + per-memory CRUD.

**Scope**: Frontend rebuild ~12-15 hr + backend Cat 3 NEW SSE event `memory_op_emitted` ~3-4 hr + Cat 12 audit log ~2 hr + role/session backend scopes (currently Phase 58+ stubs) ~6-8 hr. **Total ~25-30 hr**.

**Class candidate**: NEW `frontend-mockup-structural-rebuild` (parallel to Sprint 57.23 NEW `frontend-mockup-strict-rebuild` 0.60 1st app; or HYBRID with backend wire).

**Defer rationale (Sprint 57.24 Q2 decision 2026-05-19)**: STRUCTURAL retrofit exceeds Sprint 57.24 `mockup-fidelity-retrofit` 0.55 scope (which is cosmetic-only by class definition). Memory structural rebuild needs dedicated sprint with backend pairing per Sprint 57.22 §Sprint 57.23+ Recommendation Tier 2 priority.

**Phase**: 58+ (after Auth Block B/C IAM backend lands; role/session memory scopes are part of IAM).

---

## 🟢 Sprint 57.24 v2 Cost Dashboard Rebuild Carryovers (NEW 2026-05-19)

7 ADs from Sprint 57.24 v2 AD-Cost-Dashboard-Full-Mockup-Fidelity-Rebuild closeout. Frontend rebuild shipped 6 widget groups + 7 reusable primitives (PageHead/Spark/StatCard/AreaChart/BarTrack/CardShell/BackendGapBanner) for Sprint 57.25-57.28 epic; 3 of 6 widgets ship fixture + visible BackendGapBanner per AP-2 honesty (backend wiring deferred).

### 32. ✅ CLOSED — AD-Mockup-Fidelity-Rebuild-Sla-Dashboard (shipped Sprint 57.25 2026-05-19)
~~Rebuild `/sla-dashboard` per mockup `reference/design-mockups/page-admin.jsx:31-199` (SlaPage).~~ **Shipped Sprint 57.25**: 6 widget groups (page-head + TimeRangeTabs / 4-stat sparkline / 24h LatencyChart 3-series / 5-row SLO status / Top slow ops table / Error rate by service); reused 7 Sprint 57.24 v2 primitives without API change validating Karpathy §2 ROI; 1 NEW feature-scoped LatencyChart inline; SLAMetricsCard Karpathy §3 orphan delete. Class 3rd app ratio 0.88 in-band lower; rich-dashboard 2-pt mean 1.04 in-band middle → sub-class hypothesis NOT confirmed; sub-classification DEFER (see #41). See `memory/project_phase57_25_sla_dashboard_rebuild.md` for detail.

### 33. AD-Mockup-Fidelity-Rebuild-Admin-Tenants-Phase58
Rebuild `/admin/tenants` list per mockup `page-admin.jsx:322-410` (AdminTenants section). Existing filters/table/pagination preserved; mockup-fidelity polish + admin context widgets added (avatar rendering / row-level actions / status badges per mockup). Sprint 57.27 candidate (foundation-fidelity Sprint 57.26 was inserted ahead as a user-directed sprint, shifting this +1).

### 34. AD-Mockup-Fidelity-Rebuild-Verification-Phase58
Rebuild `/verification` per mockup `page-extras.jsx:817-927` (VerificationPage). 2-tab structure (Recent / Correction Trace) preserved; inner widget mockup-fidelity port pending. Sprint 57.28 candidate.

### 35. AD-Mockup-Fidelity-Rebuild-Tenant-Settings-Phase58
Rebuild `/admin/tenants/settings` per mockup `page-admin.jsx:411+` (TenantSettings 6-tab) + lift `/feature-flags` out per Sprint 57.22 Unit 31 architectural finding + page-extras.jsx:928 comment "/feature-flags (lifted out of /tenant-settings)". Architectural-level refactor + new standalone `/feature-flags` route. Sprint 57.29 candidate.

### 36. AD-Cost-Dashboard-Backend-Extensions-Phase58
Backend follow-on for Sprint 57.24 v2 fixture-driven widgets:
- Cross-tenant aggregation endpoint (`GET /api/v1/admin/cost-summary/by-tenant` returning top-N tenant rows; platform-admin-scoped) — drives TenantTopTable
- Cross-provider aggregation endpoint (`GET /api/v1/admin/cost-summary/by-provider`; platform-admin-scoped) — drives ProviderMixCard with LLM-neutrality redacted labels
- 30-day daily history endpoint (`GET /api/v1/admin/cost-summary/history?days=30`) — drives AreaChart
- Harmonize category taxonomy: mockup 6 flat categories (Inference input/output / Thinking tokens / Tool runs / Embeddings / Sandbox compute) ≠ current backend `by_type` 2-level dict shape (cost_type → sub_type → AggregatedSlice); decision: either backend reshape OR define explicit aggregation mapping in spec

Drives Sprint 57.24 BackendGapBanner removal for 3 of 6 widgets + flips fixture data to real. ~8-12 hr backend + ~2-3 hr frontend wire-up. Phase 58+ backend-led; could pair with Sprint 57.25 sla-dashboard rebuild if scope permits.

### 37. AD-Playwright-MCP-Recovery-Phase58
**3-consecutive-sprint blocker** (Sprint 57.22 + 57.23 + 57.24 v2): Playwright MCP browser-stuck on every visual pair-verify attempt. `browser_close` returns "Browser is already in use for ...mcp-chrome-... use --isolated to run multiple instances of the same browser". Root cause: Claude Code session-process management — prior session's chrome instance not released to next session.

**Mitigation today**: code-level audit + Vitest spec coverage + Playwright CLI (separate from MCP) cover verification; visual baselines regen via CI workflow_dispatch + cherry-pick (Sprint 57.14 + 57.23 PR #156 + 57.24 v2 PR pattern).

**Phase 58+ resolution paths**:
- Option A: pass `--isolated` flag to MCP browser per session
- Option B: explicit cleanup hook on Claude Code session end (`process.kill` on chrome PID)
- Option C: contribute fix upstream to Anthropic Playwright MCP plugin

Cost: ~2-4 hr investigation + fix. Phase 58+; meanwhile workaround acceptable.

### 38. AD-Sprint-Plan-Audit-Cross-Ref-Prong5
**Plan-draft discipline addition** (Sprint 57.24 v1 abort lesson):

Sprint 57.24 v1 plan misclassified 3 of 5 retrofit targets (cost / sla / tenant-settings) as "cosmetic-feasible Tier 1" when Sprint 57.22 AUDIT-REPORT had already marked them P0 full-rebuild. Day 0 三-prong (Prong 1 path + Prong 2 content + Prong 3 schema + Prong 4 test selector) didn't catch this because they verify code-vs-plan drift, NOT plan-vs-audit-classification mismatch.

**Proposed Prong 5: Audit Cross-Reference**:
Before drafting Tier-N retrofit/rebuild plan, grep AUDIT-REPORT(s) for each target's prior classification:
```bash
# Example for Sprint 57.24 v1
for target in cost-dashboard sla-dashboard verification admin/tenants tenant-settings; do
  grep -l "Unit.*$target" claudedocs/4-changes/sprint-57-*-audit/AUDIT-REPORT*.md
done
```
If any target is already audit-classified as P0 / structural-rebuild → lift conflicting entries into structural-rebuild scope before drafting cosmetic-retrofit batch.

**Scope**: Add to `.claude/rules/sprint-workflow.md` §Step 2.5 as new Prong 5; ~30 min doc edit. Phase 58+ when next Tier-N retrofit/rebuild batch is drafted.

---

## 🟢 Sprint 57.25 SLA Dashboard Rebuild Carryovers (NEW 2026-05-19)

3 ADs from Sprint 57.25 AD-Mockup-Fidelity-Rebuild-Sla-Dashboard closeout. Frontend rebuild shipped 6 widget groups reusing 7 Sprint 57.24 v2 primitives without API change + 1 NEW feature-scoped LatencyChart (Karpathy §2 inline); SLAMetricsCard Karpathy §3 orphan delete. Class 3rd app ratio 0.88 in-band lower; rich-dashboard 2-pt mean 1.04 in-band middle → sub-class hypothesis NOT confirmed; sub-classification DEFER pending 4th data point.

### 39. AD-SLA-Dashboard-Backend-Extensions-Phase58
Backend follow-on for Sprint 57.25 fixture-driven widgets:
- 24h time-series aggregation endpoint (`GET /api/v1/sla/latency-history?range=24h`) returning per-time-bucket {p50, p95, p99} — drives LatencyChart 24h
- Cross-operation p99 aggregation endpoint (`GET /api/v1/sla/slow-operations?range=24h&limit=N`) — drives TopSlowOpsTable
- Per-service error rate aggregation endpoint (`GET /api/v1/sla/error-rates?range=1h`) — drives ErrorRateByServiceCard
- Dedicated SLO threshold metrics (`tool_success_pct` / `hitl_response_p95_min` / `subagent_depth_max` / `cost_per_run_usd`) — drives SLOStatusCard 4 of 5 fixture rows
- Existing `useSLAReport` SLAReportResponse extension: `latency_p50_ms` + `latency_p95_ms` + `error_budget_pct` fields (currently fixture per D-PRE-2)

Drives Sprint 57.25 BackendGapBanner removal for 3 widgets (LatencyChart 24h / cross-op p99 / per-service error rate) + flips 3 stat cards (p50/p95/error_budget) + 4 of 5 SLO rows from fixture to real. ~10-14 hr backend + ~3-4 hr frontend wire-up. Phase 58+ backend-led; pairs with Sprint 57.26-57.28 backend extensions for cost-dashboard #36.

### 40. AD-LatencyChart-Extraction-Phase58
Extract `LatencyChart` from `frontend/src/features/sla-dashboard/components/` to `frontend/src/components/charts/` as generalizable 3-series multi-line primitive **IF 2nd consumer arises** per Karpathy §2 "extract on 2nd consumer" rule.

Current state (Sprint 57.25): inline feature-scoped (~110 lines); single consumer = SLA dashboard 24h LatencyChart. Sprint 57.26+ may have 2nd consumer if `/admin/tenants` rebuild needs similar multi-series visualization OR Sprint 57.27 `/verification` correction-trace shows latency distribution.

**Extraction trigger criteria**:
- 2 distinct production consumers with comparable 3-series multi-line shape (NOT just any chart need)
- API generalizable beyond hardcoded p50/p95/p99 series → e.g. `<MultiLineChart series={[{key, stroke, width, opacity}]} data />`
- Estimate: ~2 hr extraction + Vitest update

If 4th data point sprint (57.26+) doesn't surface 2nd consumer → DROP this AD entirely (Karpathy §2 rule applied correctly).

### 41. AD-Sprint-Plan-rich-dashboard-sub-class-DEFER — ✅ RESOLVED (Sprint 57.27 — DROPPED)
Sub-classification proposal logged Sprint 57.24 v2 retro Q4 (rich-dashboard ratio 1.19 vs auth-flow 0.59) deferred per Sprint 57.25 3rd data point ratio 0.88. 2-data-point rich-dashboard mean (57.24 v2 + 57.25) = ~1.04 sits in-band middle of [0.85, 1.20] — does NOT justify split.

**Resolution path** (original):
- Sprint 57.27 = 4th data point (admin-tenants list rebuild; rich-dashboard shape — foundation-fidelity Sprint 57.26 was inserted ahead, shifting it +1)
- If 57.27 ratio in band → **DROP** sub-class proposal (3-of-3 rich in band; KEEP 0.60 baseline)
- If 57.27 ratio > 1.20 → reconsider rich sub-class higher (~0.70-0.75); 2-of-3 rich above band
- If 57.27 ratio < 0.85 → drop rich-dashboard pattern entirely; KEEP 0.60 baseline accepts auth-flow + rich mixed

**✅ RESOLVED 2026-05-21 (Sprint 57.27 closeout — DROPPED)**: Sprint 57.27 became the `/overview` full rebuild (user-directed; superseded the planned admin-tenants 57.27 candidate, but `/overview` is itself a rich operator dashboard — 2 charts + 4-stat KPI + 4 cards — so it serves as the 4th rich data point). 57.27 ratio ≈0.95 — **IN BAND**. Rich-subset 57.24=1.19 / 57.25=0.88 / 57.27≈0.95 → 3-pt mean ~1.01 in-band middle → **sub-class proposal DROPPED, no split**; KEEP the single `frontend-mockup-strict-rebuild` 0.60 baseline for the whole class. Matrix row + MHist updated in `.claude/rules/sprint-workflow.md`.

---

## 🟡 Sprint 57.26 Foundation-Fidelity Carryover (NEW 2026-05-21)

1 AD from Sprint 57.26 post-closeout CI investigation. PR #159's first `Frontend E2E` run failed — `visual-regression.spec.ts` 5 `toHaveScreenshot()` baselines (auth-login / cost-dashboard / governance / verification-recent / admin-tenants) mismatched because the foundation-token correction deliberately moved the visuals. Resolved by regenerating baselines via the Sprint 57.14 `playwright-e2e.yml` workflow_dispatch mechanism (baseline commit `f0b24bd2`); CI then green, `state: CLEAN`. The gap is a planning-discipline miss, not a code defect.

### 42. AD-Day0-Prong4-Visual-Baseline-Scope
Sprint 57.26 plan §Risks listed the "22-route blast radius" of changing `html` font-size but scoped it only to the sprint's own route-sweep harness — it missed CI's pre-existing Playwright `visual-regression.spec.ts` screenshot baselines. Day 0 三-prong Prong 4 (test selector verify) checks only **Vitest** specs asserting literal foundation values; it does not cover `tests/e2e/visual/*-snapshots/` PNG baselines, which are a second class of "asserts the visuals" test. Visual-baseline regen is a known pattern (Sprint 57.14 mechanism, used in 57.23 + 57.24) but was not pre-adopted into the 57.26 plan.

**Fix proposal**: extend `.claude/rules/sprint-workflow.md` §Step 2.5 Prong 4 — when a sprint plan touches global CSS / foundation tokens / shell layout / any broad visual change, Day 0 must (a) `Glob tests/e2e/visual/**/*-snapshots/*.png` to confirm baselines exist + assess visual blast radius, and (b) if visuals will move, plan §Risks must pre-list "visual baseline regen via `playwright-e2e.yml` workflow_dispatch" as a known closeout step rather than a post-CI surprise.

**Cross-ref**: AD GHA-PR-create-blocked (line 131 — `playwright-e2e.yml` `gh pr create` step failed for the 3rd time across 57.23 / 57.24 / 57.26; the bot pushes the baseline branch fine but cannot open the PR, so the manual `fetch + ff-merge` is the working path). Effort: ~15 min rule edit; no code change.

---

## 🟢 Sprint 57.27 Overview Rebuild Carryover (NEW 2026-05-21)

2 ADs from Sprint 57.27 `AD-Mockup-Fidelity-Rebuild-Overview` closeout. `/overview` operator dashboard rebuilt 1:1 from `reference/design-mockups/page-overview.jsx` — 9 widgets, OverviewPage 728→~215-line assembly (AP-3 reversal complete), DRIFT-REPORT verdict PARITY. 8 of 9 widgets are fixture-backed (declared via `<BackendGapBanner>`); ActiveLoopsCard targets real data but its endpoint 404s.

### 43. AD-Overview-Backend-Extensions-Phase58
The 9 `/overview` widgets need real backend data. Currently 8 are fixture-backed (HITL Queue / Providers / Incidents / Error Trend / Cost Burn + the 4-stat KPI row), declared honestly via `<BackendGapBanner>`. ActiveLoopsCard targets real data via `useActiveLoops` → `fetchLoops` → `GET /api/v1/loops?status=running` — but that endpoint returns **404 (does not exist)**, so the widget always renders its error state in production (pre-existing; the hook + `loopsService` predate Sprint 57.27). Phase 58 scope: (a) build the `GET /api/v1/loops` list endpoint — closes ActiveLoopsCard live data + folds in D15 (`maxTurns` hardcoded; `Session` ORM enrich = existing `AD-Loop-Session-Enrich-Phase58`); (b) aggregation endpoints for HITL-queue / providers-health / incidents / error-trend / cost-burn / KPI stats. Pairs with cost-dashboard #36 + sla-dashboard #39 backend-extension ADs (same Phase 58+ backend-led batch).

### 44. AD-CardShell-Title-Crossverify-cost-sla
Sprint 57.27 R9 (user decision) changed the shared `CardShell` card-title `text-sm` → `text-[12.5px]` (closes D8 toward mockup `.card-title` 12.5px). `/cost-dashboard` (57.24) + `/sla-dashboard` (57.25) also consume `CardShell` → both shifted toward the mockup (they carried the same D8 drift unnoticed). Pure mockup-fidelity correction, NOT a regression — but a light Playwright pair-verify pass on those 2 pages should confirm the 12.5px title renders right. Fold into the next dashboard-touching sprint, or a small shared-primitive token-audit pass. ~15 min.

---

## Maintenance Notes

- New carryover ADs from each sprint retrospective should be **appended here**, NOT to CLAUDE.md table cells (per §Sprint Closeout policy).
- When a candidate becomes the selected next sprint, leave the entry marked `→ Sprint XX.Y` until that sprint closes; then move to "Closed" section or delete.
- Cross-references: see `memory/MEMORY.md` index + per-sprint memory subfile + retrospective.md for sprint-by-sprint detail.

---

## Modification History

- 2026-05-21: Sprint 57.27 Day 3 closeout — `/overview` rebuild SHIPPED (DRIFT verdict PARITY); +2 ADs (#43 `AD-Overview-Backend-Extensions-Phase58` + #44 `AD-CardShell-Title-Crossverify-cost-sla`); RESOLVED #41 (rich-dashboard sub-class DROPPED — 57.27 `/overview` 4th `frontend-mockup-strict-rebuild` data point ratio ≈0.95 in-band; rich-subset 3-pt mean ~1.01 → no split, KEEP single 0.60 baseline)
- 2026-05-21: Sprint 57.26 post-closeout CI fix — +1 AD #42 (`AD-Day0-Prong4-Visual-Baseline-Scope`); PR #159's first CI run failed on 5 stale `visual-regression.spec.ts` baselines (foundation-token correction deliberately moved the visuals); baselines regenerated via `playwright-e2e.yml` workflow_dispatch (`f0b24bd2`), CI re-run green / `state: CLEAN`
- 2026-05-21: Sprint 57.26 Day 3 closeout — foundation-fidelity sprint (global token correction across 22 routes; user-directed insertion, NOT drawn from this candidate list) shipped with 0 regression; 0 new carryover ADs at closeout (later +1 AD #42 post-closeout CI fix — see entry above); 3 FOUNDATION-APPLIED routes folded into the existing rebuild epic per DRIFT-REPORT §5; #33/#34/#35 candidate sprint numbers shifted +1 (→ 57.27/57.28/57.29) + #41 4th-data-point sprint → 57.27 (foundation-fidelity took the 57.26 slot)
- 2026-05-19: Sprint 57.25 Day 3 closeout — close #32 (sla-dashboard rebuild SHIPPED) + +3 ADs (#39-#41) SLA Dashboard Rebuild carryovers (backend extensions + LatencyChart extraction trigger + rich-dashboard sub-class DEFER decision)
- 2026-05-19: Sprint 57.24 v2 Day 3 closeout — +7 ADs (#32-#38) Cost Dashboard Rebuild carryovers (4 page rebuilds 57.25-57.28 + 1 backend extension + 1 Playwright MCP recovery + 1 plan-draft Prong 5 discipline addition)
- 2026-05-19: Sprint 57.24 Day 0 — +1 AD #31 Memory STRUCTURAL Rebuild carryover (Q2 decision: defer from 57.24 cosmetic retrofit to dedicated Phase 58+ sprint)
- 2026-05-18: Sprint 57.23 Day 4 closeout — +8 ADs (#23-#30) Auth Page Rebuild Round 2 carryovers (Phase 58+ IAM Block B/C + Playwright MCP followup + i18n lint)
- 2026-05-18: Initial creation (REFACTOR-001 Step 3; extracted from CLAUDE.md V2 Refactor Status table 20-bullet `Next Phase 候選` row per §Sprint Closeout policy)
