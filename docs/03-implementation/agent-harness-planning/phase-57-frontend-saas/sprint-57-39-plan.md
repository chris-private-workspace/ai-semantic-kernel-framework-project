# Sprint 57.39 — AD-Governance-Category-Multipage-Phase-2

**Phase**: 57 (Frontend SaaS)
**Sprint id**: 57.39
**Drafted**: 2026-05-24 (Day 0)
**Branch**: `feature/sprint-57-39-governance-multipage-phase2`
**Class**: 4-domain batched all-`-with-extras` — `frontend-verbatim-css-repoint -with-extras` (1st **deliberate-test** sprint of the 0.65 baseline post Sprint 57.38 Option 2 class-split; previous 4 data points 57.35/57.36/57.37B/57.38B were retroactively classified). 2 domains are pure re-point (existing real pages) + 2 domains are PROP→real promotion (ComingSoonPlaceholder → mockup port).
**Mirror template**: Sprint 57.38 plan (3-domain batched precedent; § structure 0-9, 10 main sections)

---

## 0. Sprint Goal

Four-domain batched sprint to **complete the `governance` route-category Phase-2 epic** (excluding `/audit-log` DRAFT-promote which requires Cat 9 backend pair, deferred per next-phase-candidates Round 4). All 4 routes adopt verbatim mockup CSS classes per Sprint 57.28 4-layer foundation; 2 routes promote from PROP stub to real mockup port. Empirically validates the Sprint 57.38 NEW `-with-extras` 0.65 baseline across a distinct 4-route batched shape.

### Domain A — `/governance` Phase-2 Verbatim CSS Re-Point (Approvals view)

`frontend/src/pages/governance/index.tsx` (75 lines) currently uses Sprint 57.5/57.9 vintage HSL-translated Tailwind utility classes (`bg-card`, `text-card-foreground`, etc.). Re-point to mockup verbatim per `reference/design-mockups/page-governance.jsx:283 Approvals` block (queue + filters + approval-card list).

### Domain B — `/verification` Phase-2 Verbatim CSS Re-Point

`frontend/src/pages/verification/index.tsx` (77 lines) re-pointed to verbatim per `reference/design-mockups/page-extras.jsx:829 VerificationPage`. Sprint 57.33 (`AD-Page-Bug-Fix-Sweep`) defensive `(query.data.entries ?? []).length` crash-fix guards must be **preserved**.

### Domain C — `/redaction` PROP-stub → Real Mockup Port

`frontend/src/pages/redaction/index.tsx` (1-line ComingSoonPlaceholder re-export) → real implementation per `reference/design-mockups/page-platform2.jsx:254 RedactionPage`. Removes 1 PROP stub from the sidebar's "Coming Soon" badge count.

### Domain D — `/error-policy` PROP-stub → Real Mockup Port

`frontend/src/pages/error-policy/index.tsx` (1-line ComingSoonPlaceholder re-export) → real implementation per `reference/design-mockups/page-platform.jsx:426 ErrorPolicyPage`. Removes 1 PROP stub from the sidebar.

---

## 1. Background

### 1.1 Why 4-domain batched

Sprint 57.38 demonstrated 3-domain batching works when domains share Day 0/2.5/3 overhead and Day 1 ship cost is agent-delegable. Sprint 57.39 batches **4 ship domains** (no meta-only or audit-only domain this time — all 4 produce production code) because they share:

- Same target route-category (`governance` per `routes.config.ts`)
- Same baseline class (`-with-extras` 0.65) — no HYBRID blend needed (vs Sprint 57.38's 3-class blend)
- Same Day 0 三-prong / Day 2.5 sweep / Day 3 closeout overhead
- Day 1-2 ship work is parallelizable (agent-delegated per recent 5-consecutive code-implementer pattern)

Effective shape ≈ 2-domain Day-1-2 ship cost (re-point pair Day 1 + PROP→real pair Day 2) split across 2 work days.

### 1.2 Mockup source mapping (Day 0 Prong 2 confirmed)

| Domain | Production file (current state) | Mockup source | Mockup symbol line |
|--------|--------------------------------|---------------|--------------------|
| A `/governance` | `frontend/src/pages/governance/index.tsx` (75 lines, real content, Tailwind utility classes) | `reference/design-mockups/page-governance.jsx` | `const Approvals = () =>` @ L283 (data table `const APPROVALS` @ L273) |
| B `/verification` | `frontend/src/pages/verification/index.tsx` (77 lines, real content, post-57.33 defensive guards) | `reference/design-mockups/page-extras.jsx` | `const VerificationPage = () =>` @ L829 |
| C `/redaction` | `frontend/src/pages/redaction/index.tsx` (1-line ComingSoonPlaceholder re-export) | `reference/design-mockups/page-platform2.jsx` | `const RedactionPage = () =>` @ L254 |
| D `/error-policy` | `frontend/src/pages/error-policy/index.tsx` (1-line ComingSoonPlaceholder re-export) | `reference/design-mockups/page-platform.jsx` | `const ErrorPolicyPage = () =>` @ L426 |

Domain A + B = **re-point** (touch existing 75/77-line TSX). Domain C + D = **PROP→real** (replace 1-line stub with full mockup port; ~3-5 hr each; similar shape to a strict-rebuild but using verbatim mockup CSS so no fresh design pass).

### 1.3 Scope boundaries

**In scope**:
- Domain A: `/governance` verbatim CSS swap (production code)
- Domain B: `/verification` verbatim CSS swap (production code) + Sprint 57.33 defensive guard preservation
- Domain C: `/redaction` PROP→real mockup port (replace ComingSoonPlaceholder)
- Domain D: `/error-policy` PROP→real mockup port (replace ComingSoonPlaceholder)
- Day 0 三-prong verify + Day 2.5 22-route sweep + Day 3 closeout

**Out of scope** (defer per next-phase-candidates.md):
- `/audit-log` DRAFT→active promote (needs Cat 9 backend pair per Round 4 carryover; deferred)
- Backend API changes (frontend-only sprint)
- `AD-Inline-Font-Baseline-Alignment` (FIX-011 follow-up; deferred to typography audit sprint)
- `AD-Shadcn-Border-Token-Visual-Audit-Or-Align-To-Mockup` Path A vs B decision (parallel track; not blocked by this sprint)
- `AD-Day0-Prong-Test-Dir-Convention` codification (sprint-meta; defer to dedicated rules sprint)

### 1.4 Class baselines — all 4 domains share `-with-extras` 0.65

| Domain | Class | Baseline | Weight (est) |
|--------|-------|----------|--------------|
| A — `/governance` re-point | `frontend-verbatim-css-repoint -with-extras` | 0.65 | ~25% |
| B — `/verification` re-point | same | 0.65 | ~20% |
| C — `/redaction` PROP→real | same (treated as `-with-extras` because new mockup port introduces many new oklch literals + structural elements) | 0.65 | ~20% |
| D — `/error-policy` PROP→real | same | 0.65 | ~25% |
| Day 0/2.5/3 overhead | `sprint-meta` | 0.80 | ~10% |

**HYBRID blended baseline**: 0.65×0.90 + 0.80×0.10 = **~0.67**

This sprint's primary calibration value: **5th overall `-with-extras` data point** (extending 57.35/36/37B/38B; 57.38B reclassified `-simple` 2nd app at Day 3, so 57.35/36/37B are the only existing `-with-extras` retroactive data; this sprint is the 4th `-with-extras` data point post-split classification).

### 1.5 4-domain calibration evaluation criteria

#### All 4 ship domains — `frontend-verbatim-css-repoint -with-extras` (1st deliberate-test sprint of 0.65 baseline)
- Per Sprint 57.38 Day 3 retro decision, `-with-extras` baseline 0.65 was derived from historical 57.35 (1.7) + 57.36 (1.42) + 57.37B (1.33) mean 1.48 at the prior 0.50 baseline → equivalent ~1.14 at 0.65 (in-band middle expected).
- Sub-class evaluation criteria:
  - **PASS**: per-domain ratio actual/committed in [0.85, 1.20] band → 0.65 baseline validates against the 4-route batched shape with mixed re-point + PROP→real structure.
  - **ABOVE band ≥ 2 of 4 domains**: log AD `AD-Sprint-Plan-frontend-verbatim-css-repoint-with-extras-sub-classify-prop-to-real` (suggesting PROP→real domains warrant their own sub-class).
  - **BELOW band ≥ 2 of 4 domains**: opposite signal — propose 0.65 → 0.55-0.60 lift validation in next sprint.
  - **In band**: confirms `-with-extras` baseline correctly scoped for 4-route batched mixed shape; next iteration keeps 0.65.

#### Day 0/2.5/3 overhead — `sprint-meta` (0.80)
- Drift catalog + 22-route sweep + retrospective + memory subfile + matrix update
- Expected ratio: `actual / committed ≈ 0.9-1.1` (stable per recent sprint precedent)

### 1.6 Phase-2 epic progress impact

- **Pre-sprint**: 11/17 Phase-2 routes shipped / 6 🟡 routes remaining (per Sprint 57.38 next-phase-candidates.md update)
- **Post-sprint (if all 4 domains ship)**: **15/17 Phase-2 routes shipped / 2 🟡 routes remaining** (only Phase 58+ STRUCTURAL: /memory + /tenant-settings; non-structural Phase-2 epic effectively complete after Sprint 57.39 except `/audit-log` DRAFT-promote which requires Cat 9 backend pair, deferred)

This sprint is the **second-to-last main-line Phase-2 epic sprint**. Next non-Phase-58+ candidate after 57.39 is /audit-log (paired with Cat 9 backend) or /admin-tenants (Phase-2 `-simple` 3rd validation; counted as separate from `governance` category).

---

## 2. User Stories

### Domain A — /governance re-point

#### US-A1 — Verbatim mockup CSS classes adopted
As the operator, I want `/governance` (Approvals queue) visual to match mockup `localhost:8080/#approvals` so the production page uses verbatim CSS classes (`.page-head`, `.card`, `.table`, `.btn`, etc.) instead of HSL-translated Tailwind utility classes.

#### US-A2 — Existing real content + service wiring preserved
As a current `/governance` user, the existing `useApprovals` / `useApproval` / `useApprovalDecision` mutation hooks + ApprovalList + ApprovalCard wiring must NOT regress — production must continue to fetch + render + mutate approvals correctly.

### Domain B — /verification re-point

#### US-B1 — Verbatim mockup CSS classes adopted
As the operator, I want `/verification` visual to match mockup `localhost:8080/#verification` so the production page uses verbatim CSS classes per `page-extras.jsx:829 VerificationPage`.

#### US-B2 — Sprint 57.33 defensive-guard behavior preserved
As a current `/verification` user, the crash-fix `(query.data.entries ?? []).length` defensive guards from Sprint 57.33 must NOT regress — production must continue to render empty state when API returns null/undefined.

### Domain C — /redaction PROP→real

#### US-C1 — ComingSoonPlaceholder replaced with mockup port
As the operator, I want `/redaction` to show real visual content per mockup `localhost:8080/#redaction` instead of "Coming Soon" placeholder. Implementation uses verbatim mockup CSS classes per Sprint 57.28 foundation.

#### US-C2 — Sidebar PROP badge removed
After the port, `routes.config.ts` `/redaction` entry should drop the `proposed: true` flag → sidebar no longer renders the "PROP" badge.

### Domain D — /error-policy PROP→real

#### US-D1 — ComingSoonPlaceholder replaced with mockup port
As the operator, I want `/error-policy` to show real visual content per mockup `localhost:8080/#error-policy` instead of "Coming Soon" placeholder. Implementation uses verbatim mockup CSS classes per Sprint 57.28 foundation.

#### US-D2 — Sidebar PROP badge removed
After the port, `routes.config.ts` `/error-policy` entry should drop the `proposed: true` flag → sidebar no longer renders the "PROP" badge.

### Cross-domain

#### US-E1 — Vitest baseline preserved (≥464/464)
After all sprint changes, Vitest must remain green at or above the 464 baseline (Sprint 57.38 close). Domain C + D PROP→real may add NEW Vitest specs (recommended 1-2 per new page; +2-4 specs budget).

#### US-E2 — 22-route sweep clean
22-route Playwright sweep `before` vs `after`: 0 unintended regressions; only expected diffs (`/governance` + `/verification` + `/redaction` + `/error-policy`).

#### US-E3 — mockup-fidelity guard preserved
`node frontend/scripts/check-mockup-fidelity.mjs` exit 0; HEX_OKLCH_BASELINE may bump +6-12 (4 routes × 1.5-3 oklch literals each from KPI strips, status badges, policy mode borders).

---

## 3. Technical Specifications

### 3.1 Domain A: `/governance` Approvals CSS swap

Production file: `frontend/src/pages/governance/index.tsx` (75 lines). Maps to mockup `Approvals` component (page-governance.jsx:283-410 ~125 lines).

Swap pattern (mirrors Sprint 57.34 `/orchestrator` precedent + Sprint 57.38 `/subagents`):
- Tailwind utility classes (`bg-card`, `text-card-foreground`, `rounded-[12px]` etc.) → mockup verbatim CSS class names (`.card`, `.page-head`, `.btn`, `.table`, etc.)
- Inline `style={{ color: var(--xxx) }}` literals preserved verbatim from mockup (per `AD-Inline-Style-Rule-vs-Verbatim-Method`; file-level `eslint-disable no-restricted-syntax` with rationale comment if needed)
- Preserve `useApprovals` / `useApprovalDecision` mutation wiring + `ApprovalCard` import (NOT touched — Domain A is page-shell only)
- Risk-level color hints (medium / high / critical) from mockup palette literals

### 3.2 Domain B: `/verification` CSS swap

Production file: `frontend/src/pages/verification/index.tsx` (77 lines). Maps to mockup `VerificationPage` (page-extras.jsx:829-991 ~160 lines).

Swap pattern (same as Domain A):
- Tailwind utility → mockup verbatim CSS class names
- **Preserve Sprint 57.33 defensive `(query.data.entries ?? []).length` optional chain on entries** (per `AD-Page-Bug-Fix-Sweep` carryover); Day 1 spec stability check: empty state still renders when entries is null/undefined.
- HEX_OKLCH_BASELINE bump: +0-2 expected (verification mostly text + table; few mode literals)

### 3.3 Domain C: `/redaction` PROP→real mockup port

Production file: `frontend/src/pages/redaction/index.tsx` (currently 1-line ComingSoonPlaceholder re-export). Maps to mockup `RedactionPage` (page-platform2.jsx:254 — line range to confirm Day 1 first read).

Build pattern (parallel to Sprint 57.20 `/chat-v2` token migration + Sprint 57.29 verbatim re-point):
- Replace 1-line ComingSoonPlaceholder import with full mockup port
- Add feature components under `frontend/src/features/redaction/` if mockup has multi-component structure (TBD on Day 1 first read)
- Use verbatim CSS classes per Sprint 57.28 foundation; NO Tailwind utility class invention
- Backend data: per CLAUDE.md §Frontend Mockup-Fidelity Hard Constraint "後端尚未支援的 widget → 仍依 mockup 視覺實作，data 用 fixture" — accept fixture/mock data for now; AP-2 BackendGapBanner expected
- Edit `routes.config.ts` `/redaction` entry: drop `proposed: true` flag

### 3.4 Domain D: `/error-policy` PROP→real mockup port

Production file: `frontend/src/pages/error-policy/index.tsx` (currently 1-line ComingSoonPlaceholder re-export). Maps to mockup `ErrorPolicyPage` (page-platform.jsx:426 — line range to confirm Day 1 first read; estimated ~245 lines mockup).

Build pattern (same as Domain C):
- Replace 1-line ComingSoonPlaceholder import with full mockup port
- Feature components under `frontend/src/features/error-policy/` if mockup has multi-component structure
- Verbatim CSS classes per Sprint 57.28 foundation
- Backend data: fixture; AP-2 BackendGapBanner expected
- Edit `routes.config.ts` `/error-policy` entry: drop `proposed: true` flag

### 3.5 HEX_OKLCH_BASELINE envelope

Current baseline 51 (post Sprint 57.38). 4-route bump estimate:
- Domain A: +2-4 (risk-level color hints + status badges)
- Domain B: +0-2 (mostly text + table)
- Domain C: +1-3 (redaction-mode color borders)
- Domain D: +2-4 (policy-class color borders + status badges)

Total expected: **+5-13** → target ≤64 after sprint (set `check-mockup-fidelity.mjs` `HEX_OKLCH_BASELINE` to 64 max).

---

## 4. File Change List

### Domain A (`/governance` re-point)

- `frontend/src/pages/governance/index.tsx` — verbatim CSS swap (Tailwind utility → mockup verbatim per §3.1)
- (optional) `frontend/src/features/governance/components/ApprovalCard.tsx` — only if mockup `.approval-card` class drift forces touch; assume NOT touched

### Domain B (`/verification` re-point)

- `frontend/src/pages/verification/index.tsx` — verbatim CSS swap per §3.2
- (optional Vitest spec) `frontend/tests/unit/pages/verification/*.test.tsx` — adapt if class selectors changed; D-DAY3-1 class-swap-resilience expected

### Domain C (`/redaction` PROP→real)

- `frontend/src/pages/redaction/index.tsx` — replace 1-line re-export with full mockup port
- `frontend/src/features/redaction/components/*.tsx` — NEW component(s) if mockup has multi-component structure (TBD Day 1)
- `frontend/src/routes.config.ts` — `/redaction` row: drop `proposed: true`
- (optional NEW Vitest spec) `frontend/tests/unit/pages/redaction/RedactionPage.test.tsx` — render verify; +1 spec

### Domain D (`/error-policy` PROP→real)

- `frontend/src/pages/error-policy/index.tsx` — replace 1-line re-export with full mockup port
- `frontend/src/features/error-policy/components/*.tsx` — NEW component(s) if mockup has multi-component structure (TBD Day 1)
- `frontend/src/routes.config.ts` — `/error-policy` row: drop `proposed: true`
- (optional NEW Vitest spec) `frontend/tests/unit/pages/error-policy/ErrorPolicyPage.test.tsx` — render verify; +1 spec

### Cross-domain

- `frontend/scripts/check-mockup-fidelity.mjs` — `HEX_OKLCH_BASELINE` bump per §3.5; current 51 → target ≤64
- `frontend/scripts/route-sweep.mjs` — re-point `OUT_DIR` to `sprint-57-39-governance-multipage-phase2`
- `memory/project_phase57_39_*.md` — sprint subfile (4-domain pointer)
- `memory/MEMORY.md` — quality pointer (~300 char)
- Sprint plan + checklist + progress.md + retrospective.md (this file + checklist + execution files)
- `.claude/rules/sprint-workflow.md` — §Scope-class multiplier matrix `-with-extras` row: append Sprint 57.39 as 1st deliberate-test data point

---

## 5. Acceptance Criteria

| # | Criterion | Verification |
|---|-----------|--------------|
| AC1 | `/governance` visual matches mockup `localhost:8080/#approvals` | Day 2.5 fidelity verdict PARITY for /governance |
| AC2 | `/verification` visual matches mockup `localhost:8080/#verification` | Day 2.5 fidelity verdict PARITY for /verification |
| AC3 | `/redaction` no longer shows ComingSoonPlaceholder; mockup port visible | route-sweep PNG diff: PROP stub → real |
| AC4 | `/error-policy` no longer shows ComingSoonPlaceholder; mockup port visible | route-sweep PNG diff: PROP stub → real |
| AC5 | Sprint 57.33 defensive `(entries ?? []).length` guard preserved in /verification | grep `\?\? \[\]` in `pages/verification/index.tsx` returns ≥1 site |
| AC6 | `routes.config.ts` /redaction + /error-policy `proposed: true` dropped | grep `path: "/redaction"` block: no `proposed:` line; same for /error-policy |
| AC7 | Vitest ≥464/464 (+0-4 NEW specs allowed for PROP→real) | `npm test -- --reporter=dot` last line |
| AC8 | 22-route sweep 0 unintended regressions (4 expected CHANGED + 18 IDENTICAL) | progress.md Day 2.5 entry |
| AC9 | mockup-fidelity guard exit 0 (HEX_OKLCH_BASELINE ≤64) | `node frontend/scripts/check-mockup-fidelity.mjs` exit 0 |
| AC10 | Plan-vs-repo Day 0 三-prong with drift findings catalogued (if any) | progress.md Day 0 "Drift findings" header |
| AC11 | Per-domain calibration ratio recorded in retrospective.md §Q2 | 4 ratios + sprint-aggregate ratio + matrix update note |

---

## 6. Deliverables

- [ ] Domain A: `/governance` verbatim CSS re-point shipped
- [ ] Domain B: `/verification` verbatim CSS re-point shipped + Sprint 57.33 defensive guard preserved
- [ ] Domain C: `/redaction` PROP→real mockup port shipped + routes.config.ts flag dropped
- [ ] Domain D: `/error-policy` PROP→real mockup port shipped + routes.config.ts flag dropped
- [ ] 22-route sweep before/after diff reviewed; verdict logged
- [ ] retrospective.md Q1-Q7 with per-domain + sprint-aggregate calibration ratios computed
- [ ] `.claude/rules/sprint-workflow.md` §matrix `-with-extras` row updated with Sprint 57.39 1st deliberate-test data point
- [ ] Memory subfile + MEMORY.md pointer entry per Sprint Closeout Update Policy
- [ ] PR opened against main; CI green; squash-merge ready

---

## 7. Risks & Mitigations

| Risk | Class | Mitigation |
|------|-------|-----------|
| Domain C + D mockup line range larger than estimated → scope blowout | PROP→real mockup port unknowns (Day 1 first read) | Hard cap: if mockup port exceeds 5 hr per domain, defer second PROP→real to next sprint; ratio re-eval per actual scope |
| Domain B Sprint 57.33 defensive guards regress | Functional regression | Day 0 Prong 2 already confirmed defensive pattern; Day 1 spec stability check verifies empty state still renders |
| 4-domain batched introduces visual-regression baseline drift on `app-shell.png` | Visual-regression baseline (Risk Class — recurring from FIX-010 fix-cycle) | Same AD-CI-7 manual PR fallback; baseline regen workflow_dispatch on feature branch if needed |
| Domain C or D requires backend wire to be useful | Feature-completeness risk | Accept fixture data per CLAUDE.md §Frontend Mockup-Fidelity Hard Constraint; render AP-2 BackendGapBanner; carryover for next backend-pair sprint |
| HEX_OKLCH_BASELINE bump exceeds +13 envelope | Mockup-fidelity guard | Update guard threshold to actual count; document in commit; bump >13 = signal for token consolidation review (carryover AD candidate) |
| Day 0 Prong 1 mockup symbol line range search returns nothing | Plan-vs-repo drift (Sprint 53.7 D4-D12 class) | Drift catalogue + plan §1.2 amend in progress.md; scope confirm with user before Day 1 (already done Day 0 — see progress.md initial entry) |
| Risk Class A: paths-filter vs `required_status_checks` | CI infra (recurring per sprint-workflow §Common Risk Classes A) | Touch `.github/workflows/backend-ci.yml` header comment if backend-ci skips on PR |
| 4-domain Day 1+2 ship work overruns single-agent budget | Agent-delegation scope | Split Day 1 = re-point pair (Domains A + B) / Day 2 = PROP→real pair (Domains C + D); each via separate code-implementer agent invocation |

---

## 8. Workload

**Bottom-up est** ~14.5 hr → **calibrated commit ~9.5 hr** (multiplier ~0.67 HYBRID blend per §1.4)

### Day-by-day allocation

| Day | Focus | Bottom-up | Calibrated |
|-----|-------|-----------|------------|
| Day 0 | Plan/checklist drafted (mirror 57.38) + 三-prong (Prong 1 path + Prong 2 content already done; catalog any drift) + before baseline | ~2 hr | ~1.5 hr |
| Day 1 | Re-point pair (Domain A `/governance` + Domain B `/verification`; agent-delegated; 6th consecutive code-implementer pattern). 2 single-file swaps; bottom-up ~5.5 hr | ~5.5 hr | ~3.6 hr |
| Day 2 | PROP→real pair (Domain C `/redaction` + Domain D `/error-policy`; agent-delegated). 2 mockup ports; bottom-up ~6 hr; +0-4 NEW Vitest specs | ~6 hr | ~3.9 hr |
| Day 2.5 | Capture after baseline + 22-route sweep diff review + fidelity verdict (4 routes) | ~1.5 hr | ~1.0 hr |
| Day 3 (closeout) | Retro Q1-Q7 + per-domain + sprint-aggregate calibration ratios + matrix `-with-extras` 1st deliberate-test data point + memory subfile + push + PR | ~1.5 hr | ~1.0 hr |

---

## 9. Dependencies

- Sprint 57.38 merged main `44489aba` (closed by PR #176) — `-with-extras` 0.65 baseline class-split decision is the precondition for this sprint's calibration evaluation
- FIX-011 merged main `25dc64db` (closed by PR #177) — 3 systematic Phase-2 re-point anti-patterns (AP-Phase2-A/B/C) codified in `docs/rules-on-demand/frontend-mockup-fidelity.md` — applies to all 4 domains' Day 1-2 work
- REFACTOR-002 (PR #178 `abf3b82d`) — SITUATION-V2-SESSION-START navigator cleanup — no direct sprint dependency, but session-start context cost reduced
- Sprint 57.33 merged main — `/verification` crash-fix baseline (PRE-CONDITION for Domain B viability)
- Sprint 57.28 merged main `05d7f48f` — verbatim-CSS 4-layer foundation (PRE-CONDITION for verbatim CSS class adoption)
- next-phase-candidates.md — Sprint 57.39 selected as A1 per user 2026-05-24 confirmation
- mockup sources: `reference/design-mockups/{page-governance.jsx, page-extras.jsx, page-platform2.jsx, page-platform.jsx}` — 4 mockup files (Day 0 Prong 1 confirmed all 4)
- 4-layer mockup-fidelity protocol (Sprint 57.28 foundation) intact: `styles-mockup.css` byte-identical; tailwind bridge; theme toggle; CI guard

---

**Status**: drafted Day 0; awaiting user review of plan + checklist before Day 1 code start

**Modification History**:
- 2026-05-24: Initial draft Day 0 (Sprint 57.39)
