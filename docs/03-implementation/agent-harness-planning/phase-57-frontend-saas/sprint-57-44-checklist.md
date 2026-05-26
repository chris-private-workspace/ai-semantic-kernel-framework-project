# Sprint 57.44 — Checklist

> Plan: [`sprint-57-44-plan.md`](./sprint-57-44-plan.md)
> Scope: `/tenant-settings` 6-tab full mockup-fidelity rebuild — closes Phase-2 epic FULL CLEAN
> Critical: **2nd validation data point under `agent_factor = 0.55`** per `.claude/rules/sprint-workflow.md §Active Agent Delegation Factor Modifier` (rollback-rule structural decision MANDATORY at Day 3 retro)

---

## Day 0 — Three-Prong Verify + Baselines

### 0.1 Plan + checklist draft commit
- [ ] **Commit draft plan + checklist to feature branch**
  - DoD: `git log --oneline -1` shows commit subject `feat(frontend, sprint-57-44): Day 0 — plan + checklist draft`
  - Verify: 2 files committed on `feature/sprint-57-44-tenant-settings-rebuild`; `git diff main --stat` shows 2 files +~600 lines

### 0.2 Prong 1 — Path verify (per `.claude/rules/sprint-workflow.md §Step 2.5 Prong 1`)
- [ ] **Glob 8 NEW component paths return 0 (not yet created)**
  - DoD: Each of `TenantSettingsPageHeader.tsx` / 6 `tabs/*.tsx` / `_fixtures.ts` confirmed absent
  - Verify: `Glob frontend/src/features/tenant-settings/components/tabs/*.tsx` returns 0
- [ ] **Glob `TenantSettingsView.tsx` returns 1 (will rewrite)**
  - DoD: Existing path confirmed for in-place rewrite
- [ ] **Glob `TenantSettingsEditForm.tsx` returns 1 (orphan delete target)**
  - DoD: Existing path confirmed for Karpathy §3 delete
- [ ] **Glob `frontend/{tests/e2e,e2e}/**/*tenant-settings*` (per Sprint 57.43 hotfix #1 AD)**
  - DoD: Comprehensive grep finds all spec files (Vitest + e2e); list captured in progress.md
  - Verify: Broader glob than single-dir search; documents whether e2e spec exists
- [ ] **Grep `visual-regression.spec.ts` for affected baselines (per AD-Day0-Prong4-Visual-Baseline-Scope #42)**
  - DoD: Identify whether `/tenant-settings` is in visual-regression baseline list; if yes → flag for Day 2.5 regen pattern (artifact-pull workaround per Sprint 57.43 hotfix #2)
  - Verify: Grep result documented in progress.md

### 0.3 Prong 2 — Content verify (per `.claude/rules/sprint-workflow.md §Step 2.5 Prong 2`)
- [ ] **Verify mockup line ranges match plan §3.1 references**
  - DoD: Grep `TenantSettings|FeatureFlags|Quotas|HITLPolicies|Members|DangerZone` in `reference/design-mockups/page-admin.jsx` confirms lines 411-621 with 6 sub-components
  - Verify: Each tab section line range documented; mockup excerpt Read covers full 6-tab content
- [ ] **Verify existing hooks/services preserved scope**
  - DoD: Grep `useTenantSettings|useTenantSettingsSave|tenantSettingsService|tenantSettingsStore` in `frontend/src/features/tenant-settings/` confirms 4 files exist + types.ts
  - Verify: All 5 preserved files (hooks/services/store/types) listed for GeneralTab consumer
- [ ] **Verify mockup-ui primitives critical-mass**
  - DoD: Grep `mockup-ui` directory for `Card|Badge|Button|Icon|Field|Switch|Tabs` exports — all 7 primitives present
  - Verify: 0 new primitive lifts predicted (per plan §3.6)

### 0.4 Prong 2.5 — Child component tree depth audit (per `.claude/rules/sprint-workflow.md §Step 2.5 Prong 2.5` AD-Plan-5 fold-in)
- [ ] **Enumerate child component tree from `pages/tenant-settings/index.tsx`**
  - DoD: Grep imports — identify TenantSettingsView + its children
  - Verify: Tree depth N = 2 sufficient (page → View → children); document in progress.md
- [ ] **Per-child anti-pattern grep** (drift class queries per `.claude/rules/sprint-workflow.md` table)
  - DoD: Grep `bg-card|text-foreground|border-border|bg-muted|text-muted-foreground` in `TenantSettingsView.tsx` + `TenantSettingsEditForm.tsx` to detect shadcn-utility token residue
  - DoD: Grep `style=\{\{` patterns + verify escape comments
  - Verify: Residue/escape findings catalogued as D-DAY0-N drift items

### 0.5 Prong 3 — Schema verify (per `.claude/rules/sprint-workflow.md §Step 2.5 Prong 3`)
- [ ] **Read existing `types.ts` to confirm General tab data shape**
  - DoD: Verify `TenantSettings` type has `display_name` / `region` / `locale` / `retention_days` fields matching mockup General Card 5 inputs
  - Verify: If schema gap exists (e.g. retention field missing) → flag as drift finding + decide Option A fixture-first OR Option B backend extension (probable Option A given Sprint 57.43 precedent)
- [ ] **Read existing `tenantSettingsService.ts` to confirm PATCH endpoint signature**
  - DoD: Verify `patch(payload)` exists + maps to `/api/v1/tenant/settings` (or similar) PATCH
  - Verify: Backend wire integration path documented

### 0.6 Mockup excerpt Read for Day 1 components
- [ ] **Read `reference/design-mockups/page-admin.jsx:411-621` excerpt** (already done at plan draft time)
  - DoD: Per-tab port reference saved in progress.md Day 0 entry for Day 1 mechanical port
  - Verify: 7 NEW components + 1 rewritten View have line-range anchors

### 0.7 Before-sweep + baselines
- [ ] **Capture 24-route BEFORE screenshots**
  - DoD: `cd frontend && node scripts/route-sweep.mjs --before --slug sprint-57-44-tenant-settings-rebuild` produces 24 PNGs in `claudedocs/4-changes/sprint-57-44-tenant-settings-rebuild/screenshots/before/`
  - Verify: 24 PNG files generated; sha256 manifest captured
- [ ] **Record HEX_OKLCH_BASELINE pre-sprint baseline**
  - DoD: `node frontend/scripts/check-mockup-fidelity.mjs` reports current HEX_OKLCH_BASELINE count (expected 46 per Sprint 57.43 closeout); recorded in progress.md
  - Verify: Number documented for end-of-sprint compare
- [ ] **Record Vitest + Playwright + build baselines pre-sprint**
  - DoD: `cd frontend && npm test -- --run` reports current Vitest count (expected 514 per Sprint 57.43); `npx playwright test --reporter=line` reports e2e count; `npm run build` reports module count + main bundle KB
  - Verify: Numbers documented for end-of-sprint compare

### 0.8 Drift findings catalog + go/no-go
- [ ] **Catalog all D-DAY0-N findings in progress.md Day 0 entry**
  - DoD: Each drift finding gets `D{N}` ID + Finding + Implication; cross-reference to plan §Risks if applicable
  - Verify: Findings listed under "Day 0 Drift Findings" header
- [ ] **Go/no-go decision for Day 1**
  - DoD: Per `.claude/rules/sprint-workflow.md §Step 2.5 Decide go/no-go` — findings shift scope by ≤ 20% → continue Day 1; 20-50% → revise plan §Acceptance Criteria; > 50% → abort sprint
  - Verify: Decision documented in progress.md; if revise → plan re-commit; if abort → plan rewrite

---

## Day 1 — Components + Rewrite + Orphan Delete (code-implementer agent-delegated)

### 1.1 NEW: `_fixtures.ts` (verbatim port of 5 non-General tab data)
- [ ] **Create `_fixtures.ts` (~110 lines)**
  - DoD: Verbatim port `page-admin.jsx:481-491` (FEATURE_FLAGS 8 entries) + `:512-516` (QUOTAS 5 entries) + `:533-535` (RATE_LIMITS 3 entries) + `:548-551` (HITL_POLICIES 4 entries) + `:576-583` (MEMBERS 8 entries) + `:606-610` (DANGER_OPS 4 entries) + tenant header fixture (acme-prod / tenant_01h9a2 / Pro · 8 seats)
  - Verify: Exports `FEATURE_FLAGS` / `QUOTAS` / `RATE_LIMITS` / `HITL_POLICIES` / `MEMBERS` / `DANGER_OPS` / `TENANT_HEADER_FIXTURE`; TypeScript strict 0 errors

### 1.2 NEW component: `TenantSettingsPageHeader`
- [ ] **Create `TenantSettingsPageHeader.tsx` (~75 lines)**
  - DoD: Verbatim port `page-admin.jsx:416-425` `.page-head` — title "Tenant Settings" + sub block (mono display_name + route-pill tenant_id + Badge "Pro · 8 seats"); data sourced from `useTenantSettings()` OR `TENANT_HEADER_FIXTURE` fallback per Day 0 Prong 3 decision
  - Verify: Browser DOM contains `<div class="page-head">` + `<div class="page-title">` + `<div class="page-sub">` w/ 1 mono span + 1 route-pill span + 1 Badge

### 1.3 NEW component: `GeneralTab` (1 of 6 — backend-wired)
- [ ] **Create `tabs/GeneralTab.tsx` (~140 lines)**
  - DoD: Verbatim port `page-admin.jsx:440-465` 2-col `.grid-main` — General Card (5 Field: Display name / Tenant id mono readonly / Region select / Locale select / Retention `input` + days suffix) + Identity & SSO Card (4 `.spread` rows + Configure Button AP-2 stub); General Card integrates `useTenantSettings()` + `useTenantSettingsSave()` for backend PATCH; Identity & SSO Card shows AP-2 BackendGapBanner above
  - Verify: 2 `<Card>` rendered; 5 `<Field>` in General Card; `<form onSubmit>` calls `useTenantSettingsSave().mutate(payload)`

### 1.4 NEW component: `FeatureFlagsTab` (2 of 6 — AP-2 fixture)
- [ ] **Create `tabs/FeatureFlagsTab.tsx` (~80 lines)**
  - DoD: Verbatim port `page-admin.jsx:476-505` 1 Card + 4-col `<table className="table">` (Flag mono / Description subtle / Default Badge / Tenant override Switch-or-numeric-input dispatch by `ctl` prop); data from `FEATURE_FLAGS` fixture; BackendGapBanner shown
  - Verify: Browser DOM contains `<table>` with 4-col `<thead>` + 8-row `<tbody>`

### 1.5 NEW component: `QuotasTab` (3 of 6 — AP-2 fixture)
- [ ] **Create `tabs/QuotasTab.tsx` (~110 lines)**
  - DoD: Verbatim port `page-admin.jsx:507-540` 2-col `.grid-main` — Usage quotas Card (5 rows w/ `.spread` label + mono used/max + `.bar-track` w/ `width:pct%`) + Rate limits Card (3 `.spread` rows + Request increase Button AP-2 stub); data from `QUOTAS` + `RATE_LIMITS` fixtures; BackendGapBanner shown
  - Verify: 2 `<Card>` rendered; 5 `.bar-track` elements with computed width %

### 1.6 NEW component: `HITLPoliciesTab` (4 of 6 — AP-2 fixture)
- [ ] **Create `tabs/HITLPoliciesTab.tsx` (~80 lines)**
  - DoD: Verbatim port `page-admin.jsx:542-568` 1 Card + 5-col table (Risk tier sev-dot + capitalize / Default policy Badge tone dispatch always_ask=warning, ask_once=info, auto=success / SLA mono / Approvers mono subtle / Off-platform chip-array); data from `HITL_POLICIES` fixture; BackendGapBanner shown
  - Verify: Browser DOM contains `<table>` with 5-col `<thead>` + 4-row `<tbody>`; 4 `<span class="sev-dot sev-*">` elements

### 1.7 NEW component: `MembersTab` (5 of 6 — AP-2 fixture)
- [ ] **Create `tabs/MembersTab.tsx` (~110 lines)**
  - DoD: Verbatim port `page-admin.jsx:570-601` 1 Card (title "Members" + subtitle "8 active · 0 invitations" + Invite Button action) + 5-col table (Avatar 24×24 oklch-gradient + initials / Name fontSize 12.5 / Email mono subtle / Role Badge tone dispatch / Last active subtle / ⋯ Icon); data from `MEMBERS` fixture; inline style escape comment per STYLE.md §3
  - Verify: Browser DOM contains `<table>` with 5-col `<thead>` + 8-row `<tbody>`; 8 avatar spans with `linear-gradient(135deg, oklch(...) ...)` inline style

### 1.8 NEW component: `DangerZoneTab` (6 of 6 — AP-2 fixture)
- [ ] **Create `tabs/DangerZoneTab.tsx` (~70 lines)**
  - DoD: Verbatim port `page-admin.jsx:603-620` 1 Card + 4 sub-boxes each w/ `border-left: 2px solid var(--danger)` + title fontWeight 500 + description muted + danger Button (Suspend / Rotate / Tombstone / Delete); data from `DANGER_OPS` fixture
  - Verify: Browser DOM contains 4 `<div>` with `border-left` danger style + 4 danger `<Button variant="danger">`

### 1.9 REWRITE: `TenantSettingsView.tsx`
- [ ] **Rewrite `TenantSettingsView.tsx` (~85 lines)**
  - DoD: Replace existing single-card form content with 6-tab container — mount `<TenantSettingsPageHeader>` + `<Tabs items={6}>` + tab content router via `useState<TabId>("general")` and switch-case dispatch to 6 tab components per mockup line 427-471
  - Verify: New file mounts 7 NEW components; old single-card form code completely removed; TypeScript strict 0 errors

### 1.10 Orphan delete (Karpathy §3) — TenantSettingsEditForm
- [ ] **Delete `TenantSettingsEditForm.tsx`**
  - DoD: File removed via `git rm`; 0 remaining imports anywhere (`grep -rn "TenantSettingsEditForm" frontend/src/` returns 0)
  - Verify: `git status --short` shows D entry

### 1.11 Orphan delete — associated Vitest specs
- [ ] **Delete Vitest specs for retired component (TBD Day 0 grep count — estimated 1-2)**
  - DoD: For each deleted component, corresponding `*.test.tsx` removed; co-located with parent delete in same commit (per Sprint 57.42 Lesson 2)
  - Verify: `git status --short` D-count matches Day 0 finding

### 1.12 Orphan delete — e2e if exists
- [ ] **Check + delete e2e `tenant-settings*.spec.ts` if exists (per Sprint 57.43 hotfix #1 broader glob)**
  - DoD: If file exists at `frontend/tests/e2e/` or `frontend/e2e/` → delete OR preserve based on testing scope (Karpathy §3 + Sprint 57.43 hotfix #1 precedent: delete if testing deleted feature like EditForm field directly; preserve if testing route-level concerns)
  - Verify: Decision + path documented in progress.md

### 1.13 Day 1 closeout commit
- [ ] **Commit Day 1 (NEW + REWRITE + DELETED via code-implementer agent)**
  - DoD: `git log --oneline -1` shows commit subject `feat(frontend, sprint-57-44): Day 1 — 7 NEW components + TenantSettingsView rewrite + fixtures + orphan delete (code-implementer agent)`
  - Verify: `git diff main --stat` shows NET +~690 lines per plan §4 estimate; LLM SDK leak grep 0 (`grep -rn "from anthropic\|from openai" frontend/src/` returns 0); build green (`cd frontend && npm run build` exit 0)

---

## Day 2 — Vitest Specs + Audit Report PARITY (code-implementer agent-delegated)

### 2.1 Vitest spec NEW files (per NEW component)
- [ ] **Create Vitest spec for `TenantSettingsView` (~6-8 tests; integration data-flow)**
  - DoD: Mock `useTenantSettings()`; renders `TenantSettingsPageHeader` + Tabs + active tab content; tests tab switching + initial state
  - Verify: `(cd frontend && npx vitest run tests/unit/tenant-settings/TenantSettingsView)` passes
- [ ] **Create Vitest spec for `TenantSettingsPageHeader` (~3-5 tests)**
  - DoD: Renders title + sub + route-pill + Badge; tests data prop binding
  - Verify: Spec passes
- [ ] **Create Vitest spec for `GeneralTab` (~5-8 tests; backend integration)**
  - DoD: Tests 5 fields render with initial data; tests Save form submission calls `useTenantSettingsSave().mutate`; tests Identity & SSO sidecar AP-2 banner shown
  - Verify: Spec passes
- [ ] **Create Vitest spec for `FeatureFlagsTab` (~3-5 tests)**
  - DoD: Renders 8-row table from `FEATURE_FLAGS` fixture; Switch toggle for boolean rows; numeric input for `ctl: "num"` rows
  - Verify: Spec passes
- [ ] **Create Vitest spec for `QuotasTab` (~3-5 tests)**
  - DoD: Renders 5 bar-track rows w/ computed width %; renders Rate limits 3-row section
  - Verify: Spec passes
- [ ] **Create Vitest spec for `HITLPoliciesTab` (~3-5 tests)**
  - DoD: Renders 4-row table from `HITL_POLICIES` fixture; tests Badge tone dispatch per policy value
  - Verify: Spec passes
- [ ] **Create Vitest spec for `MembersTab` (~3-5 tests)**
  - DoD: Renders 8-row table from `MEMBERS` fixture; tests avatar gradient inline style; tests role Badge tone
  - Verify: Spec passes
- [ ] **Create Vitest spec for `DangerZoneTab` (~3-5 tests)**
  - DoD: Renders 4 danger sub-boxes from `DANGER_OPS` fixture; tests danger Button variant
  - Verify: Spec passes
- [ ] **(Optional) Create Vitest spec for `_fixtures.ts` if helper functions warrant**
  - DoD: Only if `_fixtures.ts` exports shape helpers needing test coverage; skip if pure data
  - Verify: Decision documented in progress.md

### 2.2 Audit report PARITY update (8 edits per Sprint 57.40-43 pattern — **CLOSES PHASE-2 EPIC FULL CLEAN**)
- [ ] **Edit 1: `audit-report.md` row 22 verdict 🔴 → ✅ PARITY**
- [ ] **Edit 2: Summary update — 20→21 PARITY / 1→0 CATASTROPHIC remaining**
- [ ] **Edit 3: Key findings post-57.44 paragraph — 🎉 Phase-2 epic FULL CLEAN milestone**
- [ ] **Edit 4: Effort estimate strike `/tenant-settings rebuild` line as ✅ DONE**
- [ ] **Edit 5: Recommendations renumber after closing #1**
- [ ] **Edit 6: Carryover #1 CLOSED status update**
- [ ] **Edit 7: Footer status update — Phase-2 epic CLOSED milestone**
- [ ] **Edit 8: (Optional) Epic closure milestone marker — date 2026-05-26 + sprint-57-44**
  - DoD: All 8 edits applied; `audit-report.md` git diff shows verdict + summary + paragraph changes
  - Verify: `grep -n "tenant-settings" audit-report.md` shows ✅ PARITY status

### 2.3 Day 2 closeout commit
- [ ] **Commit Day 2 (Vitest specs + audit-report.md edits via code-implementer agent)**
  - DoD: `git log --oneline -1` shows commit subject `feat(frontend, sprint-57-44): Day 2 — 8 NEW Vitest specs + audit-report PARITY closes Phase-2 epic full clean (code-implementer agent)`
  - Verify: Vitest 514 → ≥ 522 (+8 minimum); all green

---

## Day 2.5 — After Sweep + 3-Way Evidence Pair

### 2.5.1 After-sweep run
- [ ] **Capture 24-route AFTER screenshots**
  - DoD: `cd frontend && node scripts/route-sweep.mjs --after --slug sprint-57-44-tenant-settings-rebuild` produces 24 PNGs in `screenshots/after/`
  - Verify: 24 PNG files generated; sha256 manifest captured

### 2.5.2 sha256 diff vs before
- [ ] **Compute sha256 diff per-route**
  - DoD: Output identifies IDENTICAL vs CHANGED routes; expected = 22 IDENTICAL + 1 INTENDED `/tenant-settings` + ≤ 3 sub-300-byte noise; 0 unintended regressions
  - Verify: Diff results documented in progress.md

### 2.5.3 3-way evidence pair staging
- [ ] **Stage BEFORE + AFTER + MOCKUP screenshots in `claudedocs/4-changes/sprint-57-44-tenant-settings-rebuild/before-after/`**
  - DoD: `/tenant-settings` BEFORE + AFTER PNGs copied + 6 MOCKUP screenshots (one per tab from `python -m http.server`+Playwright OR Sprint 57.43 byte-proxy estimation if blocked)
  - Verify: At least BEFORE + AFTER present; MOCKUP captured if feasible, else byte-proxy estimate documented
- [ ] **Verify AFTER ≥ 75% of MOCKUP byte size (structural fidelity threshold)**
  - DoD: If MOCKUP captured directly → measured ratio; if not → byte-proxy via `ls -la` MOCKUP vs AFTER PNG sizes
  - Verify: Threshold met per AC5; Phase-2 epic precedent satisfied

### 2.5.4 Day 2.5 closeout commit
- [ ] **Commit Day 2.5 (after-sweep + 3-way evidence + progress.md update)**
  - DoD: `git log --oneline -1` shows commit subject `chore(frontend, sprint-57-44): Day 2.5 — 24-route after sweep + 3-way evidence pair`
  - Verify: PNGs committed under `claudedocs/4-changes/sprint-57-44-tenant-settings-rebuild/`

---

## Day 3 — Retro Q1-Q7 + Matrix MHist + Memory + Closeout

### 3.1 Retrospective Q1-Q7 per 6-question format (+ Q7 spike if applicable)
- [ ] **Write `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-44/retrospective.md`**
  - DoD: Q1 What went well / Q2 What didn't / Q3 What we learned / Q4 Audit Debt deferred / Q5 Next steps (rolling candidates) / Q6 Solo-dev policy / Q7 Spike design note (N/A SKIP per Sprint 57.40-43 cohort feature-ship pattern); ~200 lines target per Sprint 57.43 retro length
  - Verify: All 6 mandatory Qs + Q7 disposition documented

### 3.2 Matrix MHist entry + `agent_factor` 2nd validation note (MANDATORY structural decision)
- [ ] **Update `.claude/rules/sprint-workflow.md §Scope-class multiplier matrix` for `frontend-mockup-strict-rebuild` 10th data point**
  - DoD: Add 57.44 ratio to row; recompute mean (10-pt); update decision narrative (KEEP / lift / split)
  - Verify: MHist 1-line ≤ E501 budget per `file-header-convention.md` rules
- [ ] **Update `§Active Agent Delegation Factor Modifier` Activation history with 2nd validation entry**
  - DoD: Sprint 57.44 entry records ratio + decision per rollback rule:
    - If ratio < 0.7: tighten `agent_factor` 0.55 → 0.45 (combined Sprint 57.43 ratio 0.41 + 57.44 ratio < 0.7 = rule MET)
    - If ratio > 1.20: roll back to 0.65 (single-data-point caution from band overshoot)
    - If ratio in [0.7, 1.20]: KEEP 0.55 + note 1-of-2 mixed signal; flag Sprint 57.45 3rd validation
    - If escalation criteria met (≥ 2 classes < 0.7 / > 1.20 in 3-sprint window): consider Option B per-class split
  - Verify: Decision rationale documented; matrix MHist + §Active block both updated

### 3.3 Memory subfile + MEMORY.md update
- [ ] **Create `memory/project_phase57_44_tenant_settings_rebuild.md`**
  - DoD: Per-sprint subfile with full retro Q1-Q7 highlights / calibration / carryover ADs / file change list per `.claude/rules/sprint-workflow.md §Sprint Closeout` quality pointer principle
  - Verify: Subfile follows Sprint 57.40-43 cohort format
- [ ] **Add `memory/MEMORY.md` pointer entry (~300 char quality pointer)**
  - DoD: 1 entry with topic + subfile link + keywords for retrieval; NOT a packed retro summary
  - Verify: Entry quality matches Sprint 57.42/57.43 pointer pattern

### 3.4 CLAUDE.md sync (optional per Sprint Closeout policy)
- [ ] **Update CLAUDE.md `Current Sprint` row + `Last Updated` footer + (optional) Phase-2 epic milestone marker**
  - DoD: Minimal touch per `.claude/rules/sprint-workflow.md §Sprint Closeout` policy; only navigator / principle / rule level; NO sprint-by-sprint detail
  - Verify: `Current Sprint` row updated; if Phase-2 epic full clean → milestone phrase added (1 line max)

### 3.5 Day 3 closeout commit + push + PR
- [ ] **Commit Day 3 (retro + matrix MHist + memory + CLAUDE.md)**
  - DoD: `git log --oneline -1` shows commit subject `docs(frontend, sprint-57-44): Day 3 — retro + matrix MHist + agent_factor 2nd validation + memory + CLAUDE.md sync`
  - Verify: All Day 3 files committed
- [ ] **Push branch + open PR**
  - DoD: `git push -u origin feature/sprint-57-44-tenant-settings-rebuild` succeeds; `gh pr create` opens PR with title `feat(frontend, sprint-57-44): /tenant-settings 6-tab full mockup-fidelity rebuild closes Phase-2 epic FULL CLEAN + agent_factor 0.55 2nd validation`
  - Verify: PR URL captured; required CI checks running
- [ ] **Monitor CI → merge when all green**
  - DoD: 5 active required CI checks pass (per branch protection); squash merge
  - Verify: `git log main --oneline -1` shows Sprint 57.44 merge commit

---

## Pre-Commit Self-Check (per `.claude/rules/sprint-workflow.md §Before Commit Checklist`)

### Each commit
- [ ] Commit message follows Conventional Commits (`feat|fix|chore|docs(frontend, sprint-57-44): ...`)
- [ ] Co-author tag `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>` present
- [ ] Each commit maps to checklist item

### Each pre-push
- [ ] `cd frontend && npm run lint` exit 0 (NO `--silent` per Sprint 57.40 closes AD-Pre-Push-Lint-Silent-Suppression)
- [ ] `cd frontend && npm run build` exit 0
- [ ] `cd frontend && npm test -- --run` all GREEN
- [ ] Backend lint untouched (sprint is frontend-only; backend-ci paths-filter expected to skip — if BLOCKED at PR → workaround per Sprint 57.43 carryover Risk A)

---

## Acceptance criteria verification (Day 3 closeout)

- [ ] **AC1**: 7 NEW components + 1 rewritten View render per mockup; HEX_OKLCH_BASELINE ≤ +2 bump
- [ ] **AC2**: `/tenant-settings` verdict 🔴 → ✅ PARITY; summary 20→21 PARITY / 1→0 CATASTROPHIC; 🎉 Phase-2 epic FULL CLEAN milestone
- [ ] **AC3**: Vitest 514 → ≥ 522 (+8 minimum, +12 target); all GREEN
- [ ] **AC4**: 24-route sweep — 22 IDENTICAL + 1 INTENDED + ≤ 3 noise + 0 unintended regressions
- [ ] **AC5**: 3-way evidence (BEFORE / AFTER / MOCKUP byte-proxy if blocked) staged; AFTER ≥ 75% of MOCKUP size
- [ ] **AC6**: Karpathy §3 orphan delete complete (`TenantSettingsEditForm.tsx` + associated specs/e2e)
- [ ] **AC7**: Backend wire preserved — `<GeneralTab>` integrates `useTenantSettings()` + `useTenantSettingsSave()`; PATCH unchanged
- [ ] **AC8**: `agent_factor = 0.55` 2nd validation data point recorded in `.claude/rules/sprint-workflow.md §Active block` Activation history; rollback rule structural decision executed (KEEP / tighten 0.45 / Option B escalate) + documented in retro Q4
