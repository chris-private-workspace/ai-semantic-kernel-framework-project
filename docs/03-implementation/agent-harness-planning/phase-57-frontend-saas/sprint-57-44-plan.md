# Sprint 57.44 — `/tenant-settings` 6-Tab Full Mockup-Fidelity Rebuild

> **Sprint type**: `frontend-mockup-strict-rebuild` (10th application — class 0.60 baseline)
> **Status**: Draft (pending user approval per `.claude/rules/sprint-workflow.md §6 Rolling Planning`)
> **Closes**: `AD-TenantSettings-6-Tab-Rebuild` (last of 5 original CATASTROPHIC verdicts per drift audit 2026-05-25; **Phase-2 epic full clean** upon merge)
> **Critical role**: **2nd validation data point under newly ACTIVATED `agent_factor = 0.55`** per `.claude/rules/sprint-workflow.md §Active Agent Delegation Factor Modifier` (1st validation = Sprint 57.43 ratio ~0.41 BELOW band by 0.44; rollback rule single-data-point caution KEEP 0.55; if this sprint also < 0.7 → MANDATORY tighten to 0.45 OR escalate to Option B per-class split)

---

## 0. Sprint Goal

Rebuild `/tenant-settings` from current Sprint 57.3 vintage single-card edit form into mockup-fidelity **6-tab architecture** (General / Feature Flags 14 / Quotas / HITL Policies / Members 8 / Danger Zone) per `reference/design-mockups/page-admin.jsx:411-621`. Closes drift-audit 2026-05-25 row 22 verdict 🔴 CATASTROPHIC → ✅ PARITY, **closes Phase-2 epic full clean** (21 PARITY + 1 NEAR-PARITY + 0 CATASTROPHIC), and serves as 2nd validation data point under newly ACTIVATED `agent_factor = 0.55` per Sprint 57.42 retro Q4 structural decision.

---

## 1. Background

### 1.1 Phase-2 epic context (post Sprint 57.43)

- **20 PARITY + 1 NEAR-PARITY + 1 🔴 CATASTROPHIC** routes remaining (`/tenant-settings` only).
- Sprint 57.40 (/governance) + 57.41 (/verification) + 57.42 (/memory) + 57.43 (/admin-tenants) closed 4 of 5 original CATASTROPHIC verdicts.
- **This sprint = last CATASTROPHIC route**. Post-merge Phase-2 epic full clean.
- NEAR-PARITY `/chat-v2` Inspector tab rename (~30 min quick win) deferred as separate `AD-ChatV2-Inspector-Tab-Rename` carryover.

### 1.2 Why CATASTROPHIC (per drift audit 2026-05-25 row 22)

Current production (`frontend/src/features/tenant-settings/components/TenantSettingsView.tsx` + `TenantSettingsEditForm.tsx`) = Sprint 57.3 vintage single-card edit form with Display name / Tenant id / Region / Locale / Retention fields only. Mockup demands **6-tab architecture** with 6 sub-components covering General + Feature Flags + Quotas + HITL Policies + Members + Danger Zone — completely different IA (information architecture). This is the **largest scope of remaining 3 CATASTROPHIC** per `claudedocs/1-planning/next-phase-candidates.md` §Top 3 next-sprint candidates (Sprint 57.42 close).

### 1.3 `agent_factor = 0.55` 2nd validation context

Per `.claude/rules/sprint-workflow.md §Active Agent Delegation Factor Modifier`:

- **Status**: ACTIVATED 2026-05-25 via Sprint 57.42 retro Q4 (5 cross-class data points + 4 consecutive `mockup-strict-rebuild` < 0.7)
- **Formula**: `committed = bottom_up × scope_class_mult × agent_factor` where `agent_factor = 0.55` (mid-band)
- **1st validation** Sprint 57.43 ratio actual/committed-with-agent-factor ~0.41 BELOW band by 0.44 (vs predicted 0.33 bullseye; +0.08 band-relative but -0.44 below lower edge). Single-data-point caution rollback rule → KEEP 0.55.
- **2nd validation = this sprint MANDATORY** per rollback rule: "If activated factor produces 2 sprints with ratio < 0.7 → tighten to 0.45". Retrospective Q4 structural decision REQUIRED.

### 1.4 Backward-compat hooks/services preservation

Unlike Sprint 57.42 §1.4 Option B (outer-tab DROP precedent), this sprint **PRESERVES** the existing `useTenantSettings()` / `useTenantSettingsSave()` hooks + `tenantSettingsService` + `tenantSettingsStore` + `types.ts` — the **General tab** (1st of 6 tabs) integrates these for live backend save action. The 5 non-General tabs use `_fixtures.ts` (AP-2 stubs; backend extension deferred to Phase 58+ per existing `AD-TenantSettings-Backend-Schema-Extension` candidate).

Only `TenantSettingsEditForm.tsx` (Sprint 57.3 vintage single-card form) is orphan-delete per Karpathy §3 — its form fields migrate verbatim into `GeneralTab` 5-field 2-col General Card.

---

## 2. User Stories

- **US-1** (Mockup-fidelity rebuild — full 6-tab IA)
  - As a tenant admin, I want `/tenant-settings` to display the mockup-faithful 6-tab navigation (General / Feature Flags / Quotas / HITL Policies / Members / Danger Zone) so I can manage every tenant-level concern from one screen per mockup design.
- **US-2** (General tab backend-wired)
  - As a tenant admin, I want the General tab to save my edits (Display name / Region / Locale / Retention) through the existing PATCH endpoint so my Sprint 57.3 backend integration continues working uninterrupted.
- **US-3** (5 non-General tabs as AP-2 fixtures)
  - As a tenant admin, I want Feature Flags / Quotas / HITL Policies / Members / Danger Zone tabs to render mockup-faithful UI populated by `_fixtures.ts` so I see the full target IA even though backend wire is deferred (AP-2 banner per BackendGapBanner pattern when applicable).
- **US-4** (Karpathy §3 orphan cleanup)
  - As a maintainer, I want `TenantSettingsEditForm.tsx` Sprint 57.3 vintage component (replaced by GeneralTab) plus its dedicated Vitest spec deleted so no dead code accumulates.
- **US-5** (`agent_factor = 0.55` 2nd validation)
  - As the calibration matrix maintainer, I want Sprint 57.44 retro Q4 to record ratio actual/committed-with-agent-factor as 2nd validation data point and execute the rollback-rule structural decision (KEEP / tighten / Option B escalate).

---

## 3. Technical Specifications

### 3.1 Component decomposition (per mockup `page-admin.jsx:411-621`)

| Component | Location | Lines (est) | Mockup ref |
|-----------|----------|-------------|------------|
| `TenantSettingsView` (rewrite) | `features/tenant-settings/components/TenantSettingsView.tsx` | ~85 | container line 412-474 — `.page-head` + 6-tab nav + tab content router (`useState<TabId>` + dispatch) |
| `TenantSettingsPageHeader` (NEW) | `features/tenant-settings/components/TenantSettingsPageHeader.tsx` | ~75 | `.page-head` line 416-425 — title "Tenant Settings" + sub `acme-prod` (mono) + `route-pill` `tenant_01h9a2` + Badge "Pro · 8 seats"; data sourced from `useTenantSettings()` (backend wire) OR fixture fallback |
| `GeneralTab` (NEW) | `features/tenant-settings/components/tabs/GeneralTab.tsx` | ~140 | 2-col `.grid-main` line 440-465 — General Card (5 fields Display name / Tenant id / Region / Locale / Retention) wired to `useTenantSettingsSave()` PATCH + Identity & SSO sidecar Card (4 spread rows + Configure btn AP-2 stub) |
| `FeatureFlagsTab` (NEW) | `features/tenant-settings/components/tabs/FeatureFlagsTab.tsx` | ~80 | 1 Card + 4-col table line 476-505 — 8 flag rows (Flag / Description / Default Badge / Tenant override Switch-or-numeric-input); data from `_fixtures.ts` FEATURE_FLAGS |
| `QuotasTab` (NEW) | `features/tenant-settings/components/tabs/QuotasTab.tsx` | ~110 | 2-col `.grid-main` line 507-540 — Usage quotas Card (5 bar-track rows w/ pct width) + Rate limits Card (3 spread rows + Request increase btn); data from `_fixtures.ts` QUOTAS / RATE_LIMITS |
| `HITLPoliciesTab` (NEW) | `features/tenant-settings/components/tabs/HITLPoliciesTab.tsx` | ~80 | 1 Card + 5-col table line 542-568 — 4 risk-tier rows (sev-dot + capitalize / Badge tone dispatch / SLA mono / approvers / Off-platform chips); data from `_fixtures.ts` HITL_POLICIES |
| `MembersTab` (NEW) | `features/tenant-settings/components/tabs/MembersTab.tsx` | ~110 | 1 Card (with Invite action btn) + 5-col table line 570-601 — 8 member rows (avatar oklch-gradient initials + name / email mono / role Badge tone / last active / ⋯ icon); data from `_fixtures.ts` MEMBERS |
| `DangerZoneTab` (NEW) | `features/tenant-settings/components/tabs/DangerZoneTab.tsx` | ~70 | 1 Card line 603-620 — 4 left-border sub-boxes (Suspend tenant / Rotate API keys / Tombstone PII / Delete tenant) each with title + description + danger Button; data from `_fixtures.ts` DANGER_OPS |

(Approximate per mockup excerpt Read; Day 0 Prong 2 will verify exact line counts + prop shapes.)

### 3.2 Fixture port

`features/tenant-settings/_fixtures.ts` ~110 lines: verbatim port of mockup data structures per tab:
- `FEATURE_FLAGS` array of 8 entries (k / desc / def / on / ctl?)
- `QUOTAS` array of 5 entries (k / used / max / unit / pct) + `RATE_LIMITS` array of 3 entries
- `HITL_POLICIES` array of 4 entries (risk / policy / sla / approvers / off[])
- `MEMBERS` array of 8 entries (n / e / r / a / c — c = avatar hue seed)
- `DANGER_OPS` array of 4 entries (k / v / btn)
- Tenant header fixture (acme-prod / tenant_01h9a2 / Pro · 8 seats) — fallback if `useTenantSettings()` not yet wired with mockup-shape fields

### 3.3 Backend wire posture

**General tab (1 of 6)**: ✅ live backend wire preserved.
- `<GeneralTab>` calls `useTenantSettings()` (existing Sprint 57.3 hook) + `useTenantSettingsSave()` (existing Sprint 57.9 mutation hook).
- 5 form fields (Display name / Tenant id readonly / Region select / Locale select / Retention days) map to existing `TenantSettings` types.
- Save action posts PATCH via existing `tenantSettingsService.patch()`.
- AP-2 BackendGapBanner shown for **Identity & SSO sidecar Card** only (Provider / SCIM / Allowed domains / MFA — backend identity layer not yet exposed; Phase 58+ AD).

**Non-General 5 tabs**: ⚠️ AP-2 fixtures with BackendGapBanner per tab.
- Phase 58+ backend extension carryover ADs already exist (`AD-FeatureFlags-Backend` / `AD-Quotas-Backend` / `AD-HITL-Policy-Backend` / `AD-Members-Backend` / `AD-DangerZone-Backend` candidates — will be opened or consolidated at Day 3 retro).

### 3.4 Orphan delete (per Karpathy §3)

- `frontend/src/features/tenant-settings/components/TenantSettingsEditForm.tsx` (Sprint 57.3 vintage single-card form; replaced by `GeneralTab` General Card with same 5 fields + identity sidecar)
- Associated Vitest spec(s) for `TenantSettingsEditForm` (TBD Day 0 grep count — estimated ~1-2 spec file)
- Associated e2e if exists (TBD Day 0 grep — `tenant-settings*.spec.ts`); decision per Day 0 finding (delete if testing deleted feature scope; preserve if testing route-level concerns Sprint 57.43 hotfix #1 precedent)

### 3.5 Page restructure

`pages/tenant-settings/index.tsx` (current 30 lines) — **MINIMAL CHANGE**: replace `<TenantSettingsView />` import target with the rewritten `TenantSettingsView` (same export name; outer `<RequireAuth>` + `<AppShellV2 pageTitle="Tenant Settings">` + `<Routes><Route index ...>` wrap unchanged). The rewritten `TenantSettingsView` internally mounts PageHeader + 6 tabs.

### 3.6 Verbatim-CSS protocol

HEX_OKLCH_BASELINE estimated +0-2 bump (consistent with Sprint 57.40-43 cohort; verbatim-CSS protocol +0 actual when components use `var(--*)` refs only). 7 NEW components should reuse existing mockup-ui primitives (Card / Badge / Button / Icon / Field / Switch / Tabs — post 57.40+41+42+43 critical-mass). 0 new primitive lifts predicted (Field / Switch / Tabs all already exist).

**Exception**: `MembersTab` avatar gradient is mockup-inline `style={{...background: linear-gradient(135deg, oklch(...) ...) }}`. Per STYLE.md §3 escape hatch + verbatim-CSS protocol, port inline-style verbatim with `eslint-disable-next-line no-restricted-syntax` comment (Sprint 57.42 cohort pattern).

### 3.7 Vitest spec additions

Estimate **+8-12 NEW spec files** (largest of `mockup-strict-rebuild` class cohort — consistent with 57.40+15 / 57.41+9 / 57.42+12 / 57.43+33 envelope; this sprint has 7 NEW components + GeneralTab integration). Each NEW component gets dedicated spec (~5-10 tests each); GeneralTab adds integration spec for backend-wired save flow.

### 3.8 Audit report update

`claudedocs/5-status/drift-audit-2026-05-25/audit-report.md` 8 edits per Sprint 57.40-43 pattern: row 22 verdict 🔴 → ✅ PARITY + summary 20→21 PARITY / 1→0 CATASTROPHIC + Key findings post-57.44 paragraph **🎉 Phase-2 epic full clean** + Effort estimate strike (`/tenant-settings rebuild` line) + Recommendations renumber + Carryover #1 CLOSED + footer status update + (optional 8th edit: epic closure milestone marker).

### 3.9 route-sweep before/after

`frontend/scripts/route-sweep.mjs` re-point OUT_DIR to `sprint-57-44-tenant-settings-rebuild` slug. Day 0 + Day 2.5 sweep before/after with sha256 diff per Sprint 57.40-43 precedent. 24-route sweep — `/tenant-settings` is the expected CHANGED route. Anticipated +90-150% page size shift (mockup 6-tab IA significantly larger than Sprint 57.3 single-card form; estimated by-byte similar to /admin-tenants +98.9% Sprint 57.43 precedent).

---

## 4. File Change List

### NEW files (1 rewrite + 6 NEW components + 1 fixtures + ~8-12 Vitest)

- `frontend/src/features/tenant-settings/components/TenantSettingsView.tsx` (**REWRITE** — preserves filename but replaces content from Sprint 57.3 single-card wrapper to 6-tab container)
- `frontend/src/features/tenant-settings/components/TenantSettingsPageHeader.tsx`
- `frontend/src/features/tenant-settings/components/tabs/GeneralTab.tsx`
- `frontend/src/features/tenant-settings/components/tabs/FeatureFlagsTab.tsx`
- `frontend/src/features/tenant-settings/components/tabs/QuotasTab.tsx`
- `frontend/src/features/tenant-settings/components/tabs/HITLPoliciesTab.tsx`
- `frontend/src/features/tenant-settings/components/tabs/MembersTab.tsx`
- `frontend/src/features/tenant-settings/components/tabs/DangerZoneTab.tsx`
- `frontend/src/features/tenant-settings/_fixtures.ts`
- `frontend/tests/unit/tenant-settings/TenantSettingsView.test.tsx` (rewrite if exists; integration spec)
- `frontend/tests/unit/tenant-settings/TenantSettingsPageHeader.test.tsx`
- `frontend/tests/unit/tenant-settings/tabs/GeneralTab.test.tsx`
- `frontend/tests/unit/tenant-settings/tabs/FeatureFlagsTab.test.tsx`
- `frontend/tests/unit/tenant-settings/tabs/QuotasTab.test.tsx`
- `frontend/tests/unit/tenant-settings/tabs/HITLPoliciesTab.test.tsx`
- `frontend/tests/unit/tenant-settings/tabs/MembersTab.test.tsx`
- `frontend/tests/unit/tenant-settings/tabs/DangerZoneTab.test.tsx`
- (optional) `frontend/tests/unit/tenant-settings/_fixtures.test.ts` (if shape helpers warrant)

### MODIFIED files

- `frontend/src/pages/tenant-settings/index.tsx` (no functional change; import target unchanged — only the underlying TenantSettingsView rewrites — but verify after-rewrite tree includes new components)
- `frontend/scripts/route-sweep.mjs` (re-point OUT_DIR to sprint-57-44-tenant-settings-rebuild slug; Day 2.5)
- `claudedocs/5-status/drift-audit-2026-05-25/audit-report.md` (8 edits per Sprint 57.40-43 pattern — closes Phase-2 epic)
- `.claude/rules/sprint-workflow.md` (matrix MHist + `agent_factor` 2nd validation entry in §Active block "Activation history"; Day 3 closeout; **rollback rule structural decision documented**)
- `claudedocs/1-planning/next-phase-candidates.md` (carryover ADs grow with non-General-tab backend extensions if not consolidated; Phase-2 epic full clean milestone marker)

### DELETED files (Karpathy §3 orphan delete)

- `frontend/src/features/tenant-settings/components/TenantSettingsEditForm.tsx`
- Associated Vitest specs (TBD Day 0 grep — estimated 1-2 files)
- Associated e2e if found (TBD Day 0 grep; per Sprint 57.43 hotfix #1 precedent)

**Net Day 1 delta estimate**: +~840 / -~150 ≈ **NET +690 lines** (largest of Phase-2 mockup-strict-rebuild epic; consistent with mockup IA expansion 1-card → 6-tab + 8 NEW components vs Sprint 57.43 NET +1142 from squash merge for 5 components context).

---

## 5. Acceptance Criteria

- **AC1**: All 7 NEW components + 1 rewritten View render per mockup excerpts (`page-admin.jsx:411-621`). Mockup-fidelity guard exit 0 (HEX_OKLCH_BASELINE ≤ +2 bump per §3.6 estimate). 6 tabs switchable via Tabs primitive.
- **AC2**: `/tenant-settings` drift audit verdict 🔴 → ✅ PARITY (audit-report.md row 22 update); summary 20→21 PARITY / 1→0 CATASTROPHIC remaining. **🎉 Phase-2 epic FULL CLEAN milestone**.
- **AC3**: Vitest 514 → ≥ 522 (+8 minimum, +12 target — within 57.40-43 cohort range +9 to +33). All GREEN.
- **AC4**: 24-route sweep 0 unintended regressions; only `/tenant-settings` intentional CHANGED; ≤ 3 sub-300-byte noise (consistent with Sprint 57.40-43 envelope).
- **AC5**: 3-way evidence pair (BEFORE / AFTER / MOCKUP) staged in `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-44/artifacts/tenant-settings-rebuild/before-after/`. AFTER ≥ 75% of MOCKUP size (structural fidelity threshold per Sprint 57.40-43 pattern). Note Sprint 57.43 MOCKUP-screenshot deferral pattern — may apply Option C estimated-via-byte-proxy if Python http.server flow remains blocked.
- **AC6**: Karpathy §3 orphan delete completed (`TenantSettingsEditForm.tsx` + associated specs/e2e).
- **AC7**: Backend wire preservation verified — `<GeneralTab>` consumes `useTenantSettings()` + `useTenantSettingsSave()` (Sprint 57.3 + 57.9 hooks); PATCH endpoint integration untouched; 5 non-General tabs render AP-2 fixtures with BackendGapBanner where applicable.
- **AC8**: Sprint plan §Workload retro records `agent-delegated: yes` + `actual/committed-with-agent-factor` ratio as **2nd validation data point** under `agent_factor = 0.55`. **MANDATORY structural decision per rollback rule**: if ratio < 0.7 (combined with 57.43 ratio 0.41 < 0.7) → tighten `agent_factor` to 0.45 OR escalate to Option B per-class split. Decision documented in `.claude/rules/sprint-workflow.md §Active block` Activation history + Sprint 57.44 retro Q4.

---

## 6. Deliverables

- [ ] **US-1** 6-tab IA rebuilt — 7 NEW components + 1 rewritten View per mockup `page-admin.jsx:411-621`
- [ ] **US-2** General tab backend-wired — `<GeneralTab>` integrates `useTenantSettings()` + `useTenantSettingsSave()`; PATCH save flow preserved
- [ ] **US-3** 5 non-General tabs as AP-2 fixtures — FeatureFlags / Quotas / HITLPolicies / Members / DangerZone all rendered from `_fixtures.ts`; BackendGapBanner where applicable
- [ ] **US-4** Karpathy §3 orphan cleanup — `TenantSettingsEditForm.tsx` + associated specs/e2e deleted
- [ ] **US-5** `agent_factor = 0.55` 2nd validation data point recorded + rollback-rule structural decision executed in retro Q4

---

## 7. Dependencies & Risks

### Dependencies

- Existing Sprint 57.3 + 57.9 hooks/services/store (preserved; not refactored this sprint)
- Mockup-ui primitives critical-mass post Sprint 57.40+41+42+43 (Card / Badge / Button / Icon / Field / Switch / Tabs all available; 0 new primitive lifts predicted)
- Verbatim-CSS protocol (Sprint 57.28+ foundation; HEX_OKLCH_BASELINE 46 unchanged via Sprint 57.43 — predicted +0-2 bump)
- `agent_factor = 0.55` ACTIVATED 2026-05-25 per Sprint 57.42 retro Q4

### Risks

| Risk class (per `.claude/rules/sprint-workflow.md §Common Risk Classes`) | Symptom | Workaround | Long-term fix |
|--------------------------------------------------------------------------|---------|------------|---------------|
| **A: Paths-filter vs required CI checks** | Frontend-only PR; backend-ci paths-filter may not fire | Per Sprint 53.2.5 doc — touch `.github/workflows/backend-ci.yml` header comment if BLOCKED at PR merge | AD-CI-5 long-term |
| **B: TenantSettingsEditForm spec delete causes e2e failure** | If e2e tests deleted UI form fields directly, they'll fail when component removed | Day 0 Prong 2.5 child-component tree depth audit + grep `tenant-settings*.spec.ts` to identify scope; consider Karpathy §3 e2e orphan delete (Sprint 57.43 hotfix #1 precedent) | N/A — orphan-delete is correct posture |
| **D: agent_factor = 0.55 2nd validation < 0.7 again** | Per Sprint 57.42 retro: "If activated factor produces 2 sprints with ratio < 0.7 → tighten to 0.45" | Sprint 57.44 retro Q4 MANDATORY structural decision; tighten or escalate to Option B per-class split; document in `.claude/rules/sprint-workflow.md §Active block` | Open `AD-Sprint-Plan-Agent-Delegation-Factor-Recalibration` for Sprint 57.45+ tracking |
| **E: AFTER/MOCKUP byte-proxy threshold not met** | If AFTER < 75% of MOCKUP size — structural fidelity question | Per Sprint 57.43 MOCKUP-screenshot deferral pattern — byte proxy may be sufficient evidence given 6-tab IA expansion is by-design; Day 2.5 staging notes preserved | N/A — by-design |

### Carryover from Sprint 57.43

- 🔴 `AD-AdminTenants-Backend-Schema-Extension` BLOCKING Phase 58+ (5 of 9 TenantListItem schema columns still missing — independent track; not this sprint)
- `AD-Day0-Prong1-E2E-Glob-Pattern-Broaden` — fold-in to Day 0.2 Prong 1 e2e check (broaden glob from single path to `frontend/{tests/e2e,e2e}/**/*<feature>*`)
- `AD-VisualBaselineRegen-PR-Permission-Workaround` — fold-in to Day 2.5 if visual-regression baseline regen needed (artifact-pull pattern documented Sprint 57.43)
- `AD-Day0-Prong4-Visual-Baseline-Scope #42` — fold-in to Day 0.2 Prong 1 (grep `visual-regression.spec.ts` for affected baselines pre-rebuild)
- `AD-Sprint-Plan-Agent-Delegation-Factor-Modifier-Recalibration` — Sprint 57.44 retro 2nd validation 強制 — see Risk D + AC8

---

## 8. Workload Calibration (four-segment form per Sprint 57.43+ `agent_factor` activation)

> **Bottom-up est ~15-20 hr → class-calibrated commit ~9-12 hr (mult 0.60) → agent-adjusted commit ~5-6.6 hr (agent_factor 0.55)**

### Bottom-up estimate (~15-20 hr, human-rewrite cadence)

- 7 NEW components × ~1.5-2 hr each (incl. mockup-faithful port + 5-10 Vitest tests) = ~10.5-14 hr
- 1 component rewrite (`TenantSettingsView`) = ~1-1.5 hr
- `_fixtures.ts` ~110 lines verbatim port = ~1 hr
- Orphan delete + grep verify = ~0.5 hr
- Page restructure + Vitest spec rewrites = ~1 hr
- 3-way evidence + audit-report + Day 2.5 sweep + Day 3 retro/closeout overhead = ~2-3 hr
- Total bottom-up = ~16-21 hr → **~15-20 hr after rounding** (per `next-phase-candidates.md` candidate doc)

### Class calibration (`frontend-mockup-strict-rebuild` 0.60 mid-band)

15-20 × 0.60 = **9-12 hr class-calibrated commit**.

8-pt class history (post Sprint 57.42): 0.59 / 1.19 / 0.88 / 0.95 / 1.18 / 0.36 / 0.18 / 0.33 → 8-pt mean 0.71 lower band edge; last 3 = 3 of 3 < 0.7 → lower-trigger MET → Sprint 57.43 retro proposed baseline lift 0.60 → 0.40-0.45 but **deferred to `agent_factor` activation supersession** per Sprint 57.43 §Active block note (`AD-Sprint-Plan-frontend-mockup-strict-rebuild-baseline-lift` SUPERSEDED). KEEP 0.60 class baseline.

### Agent-delegation calibration (`agent_factor = 0.55` ACTIVE)

9-12 × 0.55 = **5-6.6 hr agent-adjusted commit**.

Code-implementer agent will own Day 1 + Day 2 (component creation + Vitest specs + audit report — same delegation pattern as Sprint 57.40-43; 12th+13th+14th+15th consecutive agent-delegated days for `mockup-strict-rebuild` class).

### 2nd validation data point recording (MANDATORY at Day 3 retro Q4)

Per `.claude/rules/sprint-workflow.md §Active Agent Delegation Factor Modifier`:

- Sprint 57.44 ratio actual/committed-with-agent-factor will be recorded.
- Sprint 57.43 ratio 0.41 + Sprint 57.44 ratio TBD = 2-point window.
- **Rollback rule**: if Sprint 57.44 ratio < 0.7 (combined with 57.43 ratio < 0.7) → tighten `agent_factor` 0.55 → 0.45.
- **Escalation rule**: if 2nd validation also undershoots AND specific class signal divergent → consider Option B per-class split (`mockup-strict-rebuild + agent-delegated` sub-class baseline ~0.30 matching observed mean 0.36 / 0.18 / 0.33 / 0.41).
- Decision documented in `.claude/rules/sprint-workflow.md §Active block` Activation history Sprint 57.44 entry.

---

## 9. Carryover Audit Debt (anticipated; finalized at Day 3 retro)

### Anticipated NEW carryovers from this sprint

- **`AD-FeatureFlags-Backend-Wire-Phase-58+`** — 5 non-General tabs are AP-2 fixtures this sprint; backend extension Phase 58+. Possibly consolidated as single `AD-TenantSettings-NonGeneral-Backend-Wire-Phase-58+` covering FeatureFlags / Quotas / HITL / Members / DangerZone or split into 5 sub-ADs at Day 3 finalization.
- **`AD-Members-Avatar-Gradient-Inline-Style-Verbatim`** — fold-in note that mockup avatar gradient uses inline `style={{}}` per STYLE.md §3 escape hatch; documented in Day 1 commit message.
- **`AD-Sprint-Plan-Agent-Delegation-Factor-Recalibration` (Sprint 57.45+ ongoing)** — depends on retro Q4 outcome; rollback rule structural decision drives next-sprint matrix.
- **`AD-ChatV2-Inspector-Tab-Rename`** — 1 remaining NEAR-PARITY (Phase-2 epic full clean targeting requires this 30-min quick win; deferred to next sprint as separate scope).

### Carried from Sprint 57.43 (still open)

- 🔴 `AD-AdminTenants-Backend-Schema-Extension` BLOCKING Phase 58+ (independent track)
- `AD-Day0-Prong1-E2E-Glob-Pattern-Broaden` (folded into this plan §0.2)
- `AD-VisualBaselineRegen-PR-Permission-Workaround` (folded into this plan §2.5 contingency)
- `AD-Day0-Prong4-Visual-Baseline-Scope #42` (folded into this plan §0.2 Prong 1 visual-regression baseline grep)
- 🔴 `AD-Sprint-Plan-Agent-Delegation-Factor-Modifier-Recalibration` (executed in this sprint Q4 retro)

### Closing milestone

🎉 **Phase-2 epic FULL CLEAN** upon merge — 21 PARITY + 1 NEAR-PARITY (`/chat-v2` tab rename) + 0 CATASTROPHIC. All 5 original drift-audit 2026-05-25 CATASTROPHIC verdicts closed (governance / verification / memory / admin-tenants / tenant-settings).
