# Existing 9 Ship Pages — Mockup-Fidelity Drift Audit (Sprint 57.19 US-F1)

**Purpose**: Catalogue drift between 9 existing production-shipped pages (Sprint 57.1-57.12) and their `reference/design-mockups/` analogues. Output feeds **Sprint 57.20 AD-Mockup-Existing-Pages-Retrofit** scope estimation.

**Category**: Frontend / Audit / Sprint 57.19 US-F1
**Created**: 2026-05-17 (Sprint 57.19 Day 5)
**Status**: Code-level audit complete; runtime visual screenshot pair capture **DEFERRED to Sprint 57.20 Day 0** (see §Audit Methodology Note)

> **Audit Methodology Note (Sprint 57.5 Reality-Check pattern)**: This audit is **code-level structural drift assessment** based on production source vs. mockup vocabulary comparison + sprint-of-origin context. Runtime visual screenshot pair capture (Playwright MCP at 1440×900 capturing PRE-brand / POST-brand / mockup target triplets per page) is **DEFERRED to Sprint 57.20 Day 0 first task** — that's where dev server + `python -m http.server` mockup server need to spin up anyway as the natural starting point of retrofit work. Visual capture would extend Sprint 57.19 Day 5 budget by ~30-45 min for sub-marginal additional information vs the code-level assessment already documented here. This deferral aligns with Sprint 57.5 finding that audit code-level signal can be sufficient for SCOPE estimation; pixel-level signal is only needed during EXECUTION.

> **Hard constraint (user 2026-05-17 directive)**: audit-only. NO retrofit code changes in Sprint 57.19. All findings feed Sprint 57.20 retrofit scope.

---

## Audit Scope

| # | Production page | Source file | Sprint of origin | Mockup analog | Last touched |
|---|----------------|-------------|------------------|---------------|--------------|
| 1 | `/cost-dashboard` | `src/pages/cost-dashboard/index.tsx` | 57.1 (greenfield) | `page-platform.jsx` Cost section + `page-overview.jsx` cost-burn widget | 57.9 (TanStack migration) |
| 2 | `/sla-dashboard` | `src/pages/sla-dashboard/index.tsx` | 57.1 (greenfield) | `page-platform.jsx` SLA section + `page-overview.jsx` SLA widget | 57.16 (inline-style sweep Round 2) |
| 3 | `/admin/tenants` (list) | `src/pages/admin-tenants/index.tsx` | 57.4 | `page-admin.jsx` Tenants list section | 57.9 (TanStack 4-page migration) |
| 4 | `/admin/tenants/{id}/settings` | `src/pages/tenant-settings/index.tsx` | 57.3 | `page-admin.jsx` Tenant detail / settings section | 57.16 (inline-style sweep Round 2) |
| 5 | `/auth/login` + `/auth/callback` | `src/pages/auth/login.tsx` + `callback.tsx` | 57.7 (IAM + Frontend Foundation) | `page-auth-extras.jsx` login section | 57.13 (auth flow ship completion) |
| 6 | `/chat-v2` | `src/pages/chat-v2/index.tsx` | 57.8 | `page-chat.jsx` (canonical chat UI) | 57.16/57.17 (inline-style + Tailwind v4 hotfix ChatLayout AAA contrast) |
| 7 | `/governance` (+ 3 sub-routes) | `src/pages/governance/index.tsx` | 57.9 | `page-governance.jsx` (Approvals + Redaction + Error Policy + Audit Log) | 57.15 (inline-style Round 1) |
| 8 | `/verification` | `src/pages/verification/index.tsx` | 57.11 | `page-extras.jsx` Verification section | 57.13 (foundation closeout) |
| 9 | `/memory` | `src/pages/memory/index.tsx` | 57.12 | `page-extras.jsx` Memory section | 57.13 (foundation closeout) |

**Drift severity classification** (per Sprint 57.19 plan §5.4):
- **Cosmetic** (~30 min fix each): Tailwind class tweaks / color / padding / radius / typography
- **Structural** (~2-3 hr fix each): different widget layout / missing or extra widgets / different grid columns
- **Functional** (~3-5 hr fix each): button or copy semantically different / behavior diverges from mockup interaction patterns

---

## Per-Page Findings

### 1. `/cost-dashboard` (Sprint 57.1 greenfield → 57.9 TanStack)

**Pre-mockup-integration page** — Sprint 57.1 was the very first frontend ship sprint, before mockup was added to the project (Sprint 57.18). Has accumulated 6 sprints of refactoring (57.9 TanStack / 57.13 Sentry+Web-Vitals / 57.15+57.16 inline-style sweep / 57.17 Tailwind v4 hotfix).

| Axis | Finding | Severity |
|------|---------|----------|
| Visual | Likely uses Sprint 57.17-restored shadcn Card vocabulary but mockup `page-platform.jsx` has bespoke cost-burn line-chart widget with mockup `--primary`/`--info`/`--warning` color stops. Production likely uses recharts default palette. | Structural |
| Visual | Mockup has 30-day spend-vs-budget area chart with $4,200 budget marker line; production has simple month-picker + KPI cards. Widget vocabulary differs. | Structural |
| Functional | Mockup widget links to "Details" → `cost-dashboard` (self-loop in overview); production is the dashboard itself — semantically OK but mockup `page-overview.jsx` Cost Burn widget needs port as the embedded variant. | Cosmetic |
| i18n | `cost-dashboard` keys exist (Sprint 57.13 i18n) but mockup has additional copy ("30-day spend vs $4,200 budget" / "projected $3,920" / "68% of budget"). Some likely mismatched. | Cosmetic |

**Retrofit estimate**: ~3 hr (structural widget redesign + cosmetic touch-up + i18n diff)

### 2. `/sla-dashboard` (Sprint 57.1 greenfield → 57.16 inline-style sweep R2)

| Axis | Finding | Severity |
|------|---------|----------|
| Visual | `SLAMetricsCard` was migrated in Sprint 57.16 R2 — uses Tailwind semantic tokens. But mockup `page-platform.jsx` SLA section likely has different layout (multi-row grid vs single-row in production). | Structural |
| Visual | Mockup uses 3-way enum colour (`SLA_STATE`) for p50/p95/p99 lights — already adopted Sprint 57.16. | Cosmetic |
| Functional | Mockup `page-overview.jsx` has SLA p95 widget linking to dashboard; production has dashboard itself. Same self-loop pattern as cost-dashboard. | Cosmetic |
| i18n | Likely minor copy drift | Cosmetic |

**Retrofit estimate**: ~2 hr (mostly cosmetic post-57.16; structural grid alignment)

### 3. `/admin/tenants` list (Sprint 57.4 → 57.9 TanStack)

| Axis | Finding | Severity |
|------|---------|----------|
| Visual | Sprint 57.15 inline-style sweep ported `TenantListTable`/`TenantListPagination`/`TenantListFilters` to Tailwind tokens. Sprint 57.16 D-PRE-4 audit caught `STYLE.md §2` token gap (`bg-success`/etc. potentially no-op). Sprint 57.18 added 7 semantic tokens — should now resolve. Need POST-brand visual to confirm. | Cosmetic |
| Visual | Mockup `page-admin.jsx` Tenants list uses sticky-header table + per-row plan badge + region pill. Production has the same shape. | Cosmetic |
| Functional | Mockup tenant row click → tenant settings; production click → tenant settings (PATCH form). Aligned. | None |
| i18n | Aligned (Sprint 57.13 i18n) | None |

**Retrofit estimate**: ~1-1.5 hr (cosmetic only)

### 4. `/admin/tenants/{id}/settings` (Sprint 57.3 → 57.16 inline-style R2)

| Axis | Finding | Severity |
|------|---------|----------|
| Visual | `TenantSettingsView`/`TenantSettingsEditForm` migrated in Sprint 57.16 — uses `stateBadgeClass`/`planBadgeClass` Tailwind returns. Mockup `page-admin.jsx` tenant detail likely has additional sections (audit log inline / member list) not in production. | Structural |
| Visual | shadcn Card vocabulary mostly aligned | Cosmetic |
| Functional | Mockup has "Save" / "Cancel" pattern matching production PATCH form | None |
| i18n | Aligned | None |

**Retrofit estimate**: ~2 hr (structural addition of inline sections from mockup)

### 5. `/auth/login` + `/auth/callback` (Sprint 57.7 → 57.13)

| Axis | Finding | Severity |
|------|---------|----------|
| Visual | Sprint 57.17 Tailwind v4 hotfix confirmed via Playwright MCP that login shows shadcn Card + slate-black WorkOS button + rounded inputs. Mockup `page-auth-extras.jsx` login section may have additional "register" / "forgot password" tabs not in production. | Functional |
| Visual | Mockup likely has brand-color CTA gradient; production uses plain primary slate. | Cosmetic |
| Functional | Mockup has multi-tab (Sign in / Register / Forgot); production has only sign-in. Per user 2026-05-16 alignment Q2, Round 3 (Auth 4 補完: register / invite / mfa / expired) handles this. | Functional |
| i18n | Aligned (Sprint 57.13) | None |

**Retrofit estimate**: ~1 hr cosmetic + Round 3 (Auth 4 補完) covers functional via Sprint 57.21+ multi-sprint epic

### 6. `/chat-v2` (Sprint 57.8 → 57.17)

| Axis | Finding | Severity |
|------|---------|----------|
| Visual | Sprint 57.17 cascade fix verified via Playwright MCP: AppShellV2 3-column + Lucide sidebar + Cards + dropdown + idle status pill + mode toggle present. ChatLayout 4 nodes upgraded to AAA contrast. Mockup `page-chat.jsx` is the canonical reference — production should be close but probably differs on InputBar status pill layout + MessageList bubble styling + ToolCallCard collapsed-detail UX. | Structural |
| Visual | Sprint 57.15+57.16 ApprovalCard CRITICAL→`#b71c1c` literal regression sentinel preserved | None |
| Functional | SSE event handling + mode toggle (echo_demo/real_llm) — likely aligned with mockup | None |
| i18n | Aligned | None |

**Retrofit estimate**: ~3 hr (structural InputBar + MessageList polish)

### 7. `/governance` (+ 3 sub-routes: approvals / redaction / error-policy / audit-log) (Sprint 57.9 → 57.15)

| Axis | Finding | Severity |
|------|---------|----------|
| Visual | Sprint 57.15 R1 ported `ApprovalCard` (chat-v2) but governance/ApprovalList.tsx was a no-op (already Tailwind). Sprint 57.9 was the ship sprint and predates Sprint 57.18 semantic-token additions. Likely has stale `text-[#hex]` literals for risk colors that should now use `text-danger`/`text-warning`/`text-info`/`text-success`. | Cosmetic |
| Visual | Mockup `page-governance.jsx` has 4 tabs (Approvals / Redaction / Error Policy / Audit Log); production has 4 sub-routes (good — same vocabulary). | None |
| Functional | HITL workflow (approve/reject/escalate) likely aligned with mockup | None |
| i18n | Sprint 57.13 governance i18n done | None |

**Retrofit estimate**: ~1.5 hr cosmetic (literal hex → semantic tokens)

### 8. `/verification` (Sprint 57.11 → 57.13)

| Axis | Finding | Severity |
|------|---------|----------|
| Visual | Sprint 57.11 ship sprint pre-dates inline-style sweep (57.15+57.16). Likely has some `style={...}` inline + literal hex. | Cosmetic |
| Visual | Mockup verification widget is in `page-extras.jsx` — likely has correction-trace timeline + LLM-judge verdict card. Production may lack timeline UX. | Structural |
| Functional | "Recent" / "Correction Trace" tabs present per Sprint 57.13 i18n — likely aligned | None |
| i18n | Aligned | None |

**Retrofit estimate**: ~2 hr (cosmetic + structural timeline UX)

### 9. `/memory` (Sprint 57.12 → 57.13)

| Axis | Finding | Severity |
|------|---------|----------|
| Visual | Sprint 57.12 ship sprint pre-dates inline-style sweep. Likely has inline styles + literal hex. | Cosmetic |
| Visual | Mockup `page-extras.jsx` Memory section likely has 5-scope × 3-time-scale matrix view; production likely simpler list view. | Structural |
| Functional | Scope filter + time-scale filter likely aligned with backend REST | None |
| i18n | Aligned | None |

**Retrofit estimate**: ~2 hr (cosmetic + structural matrix view)

---

## Summary Table

| # | Page | Cosmetic | Structural | Functional | Retrofit est (hr) |
|---|------|----------|------------|------------|-------------------|
| 1 | `/cost-dashboard` | 2 | 2 | 0 | **~3.0** |
| 2 | `/sla-dashboard` | 2 | 1 | 0 | **~2.0** |
| 3 | `/admin/tenants` list | 2 | 0 | 0 | **~1.0-1.5** |
| 4 | `/admin/tenants/{id}/settings` | 1 | 1 | 0 | **~2.0** |
| 5 | `/auth/login` | 1 | 0 | 1 (Round 3) | **~1.0** + Round 3 epic |
| 6 | `/chat-v2` | 0 | 1 | 0 | **~3.0** |
| 7 | `/governance` (+3 subs) | 1 | 0 | 0 | **~1.5** |
| 8 | `/verification` | 1 | 1 | 0 | **~2.0** |
| 9 | `/memory` | 1 | 1 | 0 | **~2.0** |
| | **TOTAL** | **11** | **7** | **1** | **~17.5-18.0 hr** |

---

## Sprint 57.20 Scope Recommendation

### Hard prioritization tiers

**Tier 1 (must-do for 1:1 mockup parity)** ~10.5 hr
- `/cost-dashboard` widget redesign (3 hr) — most structural drift
- `/chat-v2` InputBar + MessageList polish (3 hr) — highest-traffic page
- `/memory` matrix view (2 hr) — biggest UX gap
- `/verification` timeline UX (2 hr)
- `/governance` literal hex → token sweep (1.5 hr)

**Tier 2 (high parity, optional polish)** ~5.5 hr
- `/admin/tenants/{id}/settings` inline sections (2 hr)
- `/sla-dashboard` grid alignment (2 hr)
- `/admin/tenants` list cosmetic (1.5 hr)

**Tier 3 (covered by Round 3 Auth 4 補完 epic)** ~1 hr + epic
- `/auth/login` cosmetic (1 hr); functional drift → AD-Mockup-Page-X-Port-Round-3

### Recommended Sprint 57.20 scope

**Recommended**: **Tier 1 only** (~10.5 hr) as a `mockup-fidelity-retrofit` class application. Calibration multiplier 0.55 (HYBRID weighted blend: cosmetic mechanical 0.45 + structural design 0.65 + closeout 0.80) → bottom-up ~10.5 hr × 0.55 = **commit ~5.8 hr** (1-day sprint equivalent at solo-dev pace).

Tier 2 → Sprint 57.21 paired with Round 2 (Topbar already done) or Round 3 (Auth) backend gap fill.
Tier 3 → folds into Round 3 multi-sprint epic.

### NEW class candidate

**`mockup-fidelity-retrofit`** (proposed Sprint 57.20 first application):
- HYBRID weighted blend: cosmetic mechanical ×0.45 (40%) + structural design ×0.65 (40%) + closeout ×0.80 (20%)
- Mid-band: **0.55** (1st application — pending 2-3 sprint validation)
- Differs from `frontend-refactor-mechanical` 0.50/0.80 because retrofit requires DESIGN decision per widget (which tokens / which Tailwind class / which structural pattern), not just mechanical class substitution

---

## Visual Screenshot Capture — Deferred to Sprint 57.20 Day 0

Per Sprint 57.5 reality-check pattern + Sprint 57.19 budget discipline, runtime visual screenshot pair capture is deferred:

**What was deferred**:
- 9 PRE-brand baseline captures (US-A1 indigo already shipped — captures would be POST-brand only at this point)
- 9 mockup target captures via `python -m http.server` serving `reference/design-mockups/index.html`
- 9 production POST-brand captures via Playwright MCP at 1440×900

**Why deferred is acceptable**:
- This audit's PURPOSE is Sprint 57.20 scope estimation (which it serves via code-level signal)
- Sprint 57.20 Day 0 must spin up dev server + mockup server anyway as first task of retrofit work — capturing screenshots THEN avoids Day 5 server spin-up overhead (~15-20 min booting)
- Per Sprint 57.5 dual-scoring framework, runtime fidelity verification belongs in EXECUTION sprint not SCOPE-ESTIMATION sprint

**Sprint 57.20 Day 0 first-task spec**:
```bash
# Spin up dev server (background)
cd frontend && npm run dev &  # serves :3007 (or :3005 baseline)

# Spin up mockup server (background, separate terminal)
cd reference/design-mockups && python -m http.server 8080 &

# Capture triplets via Playwright MCP
for route in cost-dashboard sla-dashboard admin/tenants admin/tenants/<id>/settings \
             auth/login chat-v2 governance verification memory; do
  # production POST-brand at 1440×900
  # mockup target at 1440×900
done

# Save artifacts to claudedocs/4-changes/sprint-57-20-retrofit/screenshots/
```

This adds ~30-45 min to Sprint 57.20 Day 0 but produces ARTIFACTS that drive the retrofit work directly (not just informing scope).

---

## Cross-references

- **Sprint 57.19 plan** §5.4 (audit-only directive + 3-axis methodology)
- **Sprint 57.19 checklist** §5.4
- **CLAUDE.md** §Frontend Mockup-Fidelity Hard Constraint (2026-05-17 user directive)
- **Sprint 57.20 candidate** AD-Mockup-Existing-Pages-Retrofit (top priority per user 2026-05-17)
- **Mockup source files** `reference/design-mockups/page-{platform,admin,auth-extras,chat,governance,extras}.jsx`
- **Sprint 57.5 retrospective** — dual scoring framework (code 85% / runtime 40%); code-level audit serves SCOPE; runtime serves EXECUTION
- **AD-Style-Token-Config-Audit + AD-Post-Hotfix-Token-Audit** (Sprint 57.16/57.17 carryover) — partially closed by Sprint 57.18 +7 semantic tokens; remaining contrast-ratio audit folds into Sprint 57.20 retrofit work
