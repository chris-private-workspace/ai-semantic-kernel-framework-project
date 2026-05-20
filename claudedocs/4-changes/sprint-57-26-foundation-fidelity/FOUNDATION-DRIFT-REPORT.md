# FOUNDATION-DRIFT-REPORT — Sprint 57.26 (AD-Foundation-Fidelity-Token-Correction)

**Purpose**: Catalogue the global foundation-token drift between production and mockup, and record the before/after + vs-mockup regression sweep for the 22-route correction.
**Sprint**: 57.26
**Scope**: Cross-cutting frontend (foundation layer only — NOT per-route content rebuild)
**Created**: 2026-05-20 (Day 0 skeleton)
**Status**: 🚧 In Progress — Day 0 skeleton

> **Modification History**
> - 2026-05-20: Day 0 skeleton — 5 foundation drifts + 22-route before/after matrix skeleton

---

## 1. The 5 Foundation Drifts (measured 2026-05-20)

Source evidence: standalone Playwright probe `claudedocs/4-changes/sprint-57-25-sla-dashboard-rebuild/compare-overview-{prod,mockup}.png` + `index.css` / `AppShellV2.tsx` / mockup `styles.css` read.

| # | Foundation token | Production (current) | Mockup `styles.css` | Visual consequence | Fix (Day 1) |
|---|------------------|----------------------|---------------------|--------------------|-------------|
| 1 | root font-size baseline | `16px` (browser default; `index.css` body never sets `font-size`) | `13px` (`styles.css:184`) | All text ~23% larger; every Tailwind rem utility (`text-*`/`p-*`/`gap-*`) inflated across all 22 routes | `html { font-size: 13px }` rem-scaling (US-B1) |
| 2 | shell `<main>` padding | `p-6` = `24px` (`AppShellV2.tsx:115`) | `.main` padding `0` (`styles.css:208`) | Main content offset inward vs mockup | `<main>` inset → measured mockup gutter (US-B2) |
| 3 | sidebar grid column | `240px` (`AppShellV2.tsx:102`) | `232px` (`styles.css:200`) | Left rail 8px too wide on every authed route | `grid-cols-[232px_1fr]` (US-B2) |
| 4 | shell background tokens | `bg-background`/`text-foreground` (shadcn dark `hsl(222 84% 4.9%)` blue-black) | `--bg` token tree (neutral-grey) | Whole-page base hue too blue/dark | `bg-bg`/`text-fg` (US-B2) |
| 5 | `--radius` base token | `0.5rem` (`index.css:51`; rem-based) | `8px` (`styles.css:29`; px) | After fix #1, `0.5rem`→6.5px → radius drifts smaller | `--radius: 8px` (US-B1) |

---

## 2. Day 0 三-prong Findings

| ID | Prong | Finding | Implication |
|----|-------|---------|-------------|
| D-PRE-1 | 2 (content) | `index.css` has exactly ONE rem-valued custom property: `--radius: 0.5rem` (L51) | rem→px correction scope = 1 token; convert to `8px` so it survives rem-scaling |
| D-PRE-2 | 2 (content) | 9 shell components carry 43 Tailwind arbitrary-px values (`[NNpx]`) | arbitrary-px is mockup-faithful (written against the 13px-base mockup by Sprint 57.18-57.25) and does NOT rem-scale — rem-scaling deliberately pulls the inflated `text-*`/`p-*` utilities back to align with this already-correct px world |
| D-PRE-3 | 4 (test selector) | 0 Vitest specs assert literal `240px` / `p-6` / `bg-background` / `grid-cols-[` (only 1 a11y comment mention) | Vitest adapt workload ≈ 0; scope slightly reduced vs plan estimate |
| D-PRE-4 | 1 (path) | `index.css` / `AppShellV2.tsx` / `AuthShell.tsx` / `tailwind.config.ts` all present | 4 edit targets confirmed; 0 create-collisions |

**Go/no-go**: findings shift scope < 20% (D-PRE-3 slightly reduces it) → **GO for Day 1**.

---

## 3. 22-Route Regression Matrix

Legend — Before/After diff: 🟢 intended improvement · 🟡 cosmetic regression (iterate in-sprint) · 🔴 structural regression (carryover) · ⚪ unchanged
Verdict: `FOUNDATION-PARITY` = foundation baseline aligned (residual per-route content drift noted separately as epic backlog)

### 3.1 Public routes (Home + AuthShell × 7)

| Route | Shell | Before/After | vs-Mockup foundation | Residual content drift (epic backlog) | Verdict |
|-------|-------|--------------|----------------------|----------------------------------------|---------|
| `/` (home) | none | _Day 2_ | _Day 2_ | _Day 2_ | _Day 3_ |
| `/auth/login` | AuthShell | _Day 2_ | _Day 2_ | _Day 2_ | _Day 3_ |
| `/auth/callback` | AuthShell | _Day 2_ | _Day 2_ | _Day 2_ | _Day 3_ |
| `/auth/register` | AuthShell | _Day 2_ | _Day 2_ | _Day 2_ | _Day 3_ |
| `/auth/invite/:token` | AuthShell | _Day 2_ | _Day 2_ | _Day 2_ | _Day 3_ |
| `/auth/mfa` | AuthShell | _Day 2_ | _Day 2_ | _Day 2_ | _Day 3_ |
| `/auth/expired` | AuthShell | _Day 2_ | _Day 2_ | _Day 2_ | _Day 3_ |
| `/auth/dev` | AuthShell | _Day 2_ | _Day 2_ | _Day 2_ | _Day 3_ |

### 3.2 AppShellV2 routes (13 real + 1 PROP representative)

| Route | Rebuilt? | Before/After | vs-Mockup foundation | Residual content drift (epic backlog) | Verdict |
|-------|----------|--------------|----------------------|----------------------------------------|---------|
| `/overview` | no | _Day 2_ | _Day 2_ | _Day 2_ | _Day 3_ |
| `/chat-v2` | partial (57.21) | _Day 2_ | _Day 2_ | _Day 2_ | _Day 3_ |
| `/orchestrator` | no | _Day 2_ | _Day 2_ | _Day 2_ | _Day 3_ |
| `/subagents` | no | _Day 2_ | _Day 2_ | _Day 2_ | _Day 3_ |
| `/loop-debug` | no | _Day 2_ | _Day 2_ | _Day 2_ | _Day 3_ |
| `/memory` | no | _Day 2_ | _Day 2_ | _Day 2_ | _Day 3_ |
| `/state-inspector` | no | _Day 2_ | _Day 2_ | _Day 2_ | _Day 3_ |
| `/governance` | no | _Day 2_ | _Day 2_ | _Day 2_ | _Day 3_ |
| `/verification` | no | _Day 2_ | _Day 2_ | _Day 2_ | _Day 3_ |
| `/cost-dashboard` | ✅ 57.24 | _Day 2 (R1 audit)_ | _Day 2_ | _Day 2_ | _Day 3_ |
| `/sla-dashboard` | ✅ 57.25 | _Day 2 (R1 audit)_ | _Day 2_ | _Day 2_ | _Day 3_ |
| `/admin-tenants` | no | _Day 2_ | _Day 2_ | _Day 2_ | _Day 3_ |
| `/tenant-settings` | no | _Day 2_ | _Day 2_ | _Day 2_ | _Day 3_ |
| `/compaction` (PROP rep) | n/a | _Day 2_ | _Day 2_ | _Day 2_ | _Day 3_ |

> `/auth/*` (7) treated as one rebuilt family (✅ 57.23) — R1 audit applies; auth routes captured individually above.

---

## 4. Day 3 Final Verdict

_Populated Day 3._

---

## 5. Epic Backlog (routes still needing `frontend-mockup-strict-rebuild`)

_Populated Day 3 — the residual content drift per route after the foundation correction defines the remaining epic backlog._
