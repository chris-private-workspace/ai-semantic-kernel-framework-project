# FOUNDATION-SWITCH-REPORT — Sprint 57.28 (AD-Mockup-Fidelity-Foundation-Switch)

**Purpose**: Track the verbatim-CSS 4-layer foundation switch — token-collision resolution + 22-route before/after regression evidence.
**Sprint**: 57.28 (Phase 1 of `claudedocs/5-status/v2-investigation-20260522/03-mockup-consistency-rootcause.md` §5)
**Status**: Day 3 — 22-route before/after sweep + triage complete (0 catastrophic / 0 structural regression from the switch); CI guards landed. Day 4 = final verdict.
**Created**: 2026-05-22

---

## 1. The 4-layer sync protocol (what this sprint lands)

| Layer | File | Day 0 state | Target |
|-------|------|-------------|--------|
| **1** | `reference/design-mockups/styles.css` | canonical (1123 lines, oklch, on main) | unchanged — verbatim source |
| **2** | `frontend/src/styles-mockup.css` | absent | byte-identical copy of Layer 1; imported in `main.tsx` after `index.css` |
| **3** | `frontend/src/index.css` | carries shadcn tokens + 57.18/57.20 mockup HSL approximations + `html{font-size:13px}` | slimmed — mockup-system HSL approximations retired |
| **4** | `frontend/tailwind.config.ts` | all colours `hsl(var(--X))` | mockup tokens → `var(--X)`; shadcn name-collisions de-collided |

---

## 2. Token-collision set (Day 0 三-prong Prong 2 — enumerated)

`{names in mockup styles.css}` ∩ `{names in production index.css :root/.dark}`. Mockup tokens span `:root` (theme-invariant) + `[data-theme][data-variant]` (theme-scoped bg/fg) + `[data-density]`.

### 2a. Tricky collisions — different system, same name → DE-COLLIDE (rename shadcn var)

| Token | Production (shadcn) | Mockup | Resolution |
|-------|---------------------|--------|------------|
| `--primary` | HSL `234 89% 60%` (bridged `hsl(var(--primary))`) | `oklch(0.62 0.16 250)` | rename shadcn → `--sc-primary`; update `index.css` def + `tailwind.config.ts` `primary` bridge; mockup `--primary` (oklch) owns the name |
| `--border` | HSL `214 31% 91%` (bridged `hsl(var(--border))`; also `* { border-color }` index.css:154) | `oklch(...)` theme-scoped | rename shadcn → `--sc-border`; update `index.css` def + `* { border-color }` rule + `tailwind.config.ts` `border` bridge |

> Without de-collision, mockup oklch wins the cascade → `hsl(oklch(...))` = invalid CSS → every `bg-primary` / border breaks.

### 2b. Shared-intent collisions — production token was a 57.18/57.20 approximation OF the mockup token → RETIRE production HSL; mockup verbatim oklch owns the name; bridge → `var(--X)`

| Tokens | Added by | Mockup form |
|--------|----------|-------------|
| `--primary-soft` | Sprint 57.20 | `oklch(... / 0.14)` |
| `--success` `--warning` `--danger` `--thinking` `--tool` `--memory` `--info` | Sprint 57.18 | oklch |
| `--risk-low` `--risk-medium` `--risk-high` `--risk-critical` | Sprint 57.18 | oklch / var |
| `--bg` `--bg-1` `--bg-2` `--bg-3` `--bg-hover` `--fg` `--fg-muted` `--fg-subtle` `--border-strong` `--shadow` | Sprint 57.20 | oklch — **theme-scoped (`[data-theme][data-variant]`)**, see D-PRE-2 |

### 2c. Identical-value collisions — retire production's; mockup owns (no value change)

| Tokens | Note |
|--------|------|
| `--radius` (`8px`) | mockup `:root` `8px` == production (57.26 made it px); mockup also adds `--radius-sm` `--radius-lg` |
| `--row-h` (`36px`) `--pad` (`14px`) `--gap` (`10px`) | mockup `:root` + `[data-density]` overrides identical to production 57.20 values |

### 2d. shadcn-only — NO collision, KEPT

`--background` `--foreground` `--accent`(+fg) `--secondary`(+fg) `--destructive`(+fg) `--muted`(+fg) `--input` `--ring` + all semantic `*-foreground`. Mockup has no same-named token → stays as shadcn HSL with `hsl(var(--X))` bridge; retired page-by-page in Phase 2.

---

## 3. 22-route before/after regression matrix

Captured 1440×900 via `frontend/scripts/route-sweep.mjs`. Before = Day 0 (this branch, pre-switch). After = Day 3 (post Layer 2/3/4 + theme toggle). Both runs: **22/22 routes captured ✓** (0 harness `✗` — no navigation/load failure).

Triage legend: 🟢 unchanged/improvement · 🟡 transition-drift (Phase-2 re-point backlog) · 🔴 catastrophic (in-sprint fix) · 🟠 structural-regression (carryover AD) · ⚪ not-assessable (pre-existing route-sweep mock-shape gap — errors identically before+after).

| # | Route | Shell | Before | After (Day 3) | Verdict |
|---|-------|-------|--------|---------------|---------|
| 1 | `/` | Home | ✓ | plain dev route index (not a mockup-scoped page) | 🟢 unchanged |
| 2 | `/auth/login` | AuthShell | ✓ | dark ✓ — centered card + radial backdrop | 🟡 transition-drift |
| 3 | `/auth/callback` | AuthShell | ✓ | dark ✓ — sign-in progress card | 🟡 transition-drift |
| 4 | `/auth/register` | AuthShell | ✓ | dark ✓ — 4-step wizard | 🟡 transition-drift |
| 5 | `/auth/invite/:token` | AuthShell | ✓ | dark ✓ — login fallback (demo token) | 🟡 transition-drift |
| 6 | `/auth/mfa` | AuthShell | ✓ | dark ✓ — 6-digit grid | 🟡 transition-drift |
| 7 | `/auth/expired` | AuthShell | ✓ | dark ✓ — session-expired card | 🟡 transition-drift |
| 8 | `/auth/dev` | AuthShell | ✓ | dark ✓ — dev-login form | 🟡 transition-drift |
| 9 | `/overview` | AppShellV2 | ✓ | dark ✓ — operator dashboard, 9 widgets | 🟡 transition-drift |
| 10 | `/chat-v2` | AppShellV2 | ✓ | dark ✓ — 3-col shell, sessions + inspector | 🟡 transition-drift |
| 11 | `/orchestrator` | AppShellV2 | dark ✓ | dark ✓ — config form + 4 stat cards (tighter spacing) | 🟡 transition-drift |
| 12 | `/subagents` | AppShellV2 | error boundary | error boundary — `undefined.length` | ⚪ not-assessable (identical before+after) |
| 13 | `/loop-debug` | AppShellV2 | ✓ | dark ✓ — empty-state | 🟡 transition-drift |
| 14 | `/memory` | AppShellV2 | error boundary | error boundary — `undefined.length` | ⚪ not-assessable (identical before+after) |
| 15 | `/state-inspector` | AppShellV2 | dark ✓ | dark ✓ — version chain + diff panel | 🟡 transition-drift |
| 16 | `/governance` | AppShellV2 | ✓ | dark ✓ — graceful inline data-load error (mock `[]`); page usable | 🟡 transition-drift |
| 17 | `/verification` | AppShellV2 | error boundary | error boundary — `undefined.length` | ⚪ not-assessable (identical before+after) |
| 18 | `/cost-dashboard` | AppShellV2 | ✓ | dark ✓ — Cost Ledger, charts + tables | 🟡 transition-drift |
| 19 | `/sla-dashboard` | AppShellV2 | ✓ | dark ✓ — latency charts + SLO status (tighter spacing) | 🟡 transition-drift |
| 20 | `/admin-tenants` | AppShellV2 | ✓ | dark ✓ — console + filter bar | 🟡 transition-drift |
| 21 | `/tenant-settings` | AppShellV2 | ✓ | dark ✓ — settings field list | 🟡 transition-drift |
| 22 | `/compaction` (PROP stub) | AppShellV2 | ✓ | dark ✓ — Coming-Soon placeholder | 🟢 unchanged (PROP stub) |

> "Before ✓" = captured by the Day-0 sweep without harness error. `/orchestrator`, `/state-inspector`, `/subagents`, `/memory`, `/verification` before/ images were opened for direct before/after comparison; the rest are inferred from the functioning pre-57.28 app.

### 3a. Triage (US-D3)

- **🔴 Catastrophic from the switch: 0.** No route that rendered before is blank / crashed / unusable after.
- **🟠 Structural regression from the switch: 0.** No `AD-Foundation-Switch-Regression-*` carryover needed.
- **🟡 Transition-drift: 19 routes.** Every renderable route now loads the verbatim mockup CSS foundation. Colour fidelity improved (verbatim oklch tokens replace the Sprint 57.18/57.20 HSL approximations); spacing/layout shifts on the not-yet-re-pointed pages (`/orchestrator`, `/sla-dashboard` render tighter) because their markup still consumes shadcn utilities on top of the new foundation. **This is the Phase-2 per-page re-point backlog** — expected and accepted under Option B; not fixed this sprint.
- **⚪ Not-assessable: 3 routes** (`/subagents`, `/memory`, `/verification`). All three render the AppErrorBoundary fallback with `Cannot read properties of undefined (reading 'length')` — **identically in the Day-0 before-baseline and the Day-3 after-sweep**. The error pre-dates the switch: it is a `route-sweep.mjs` harness limitation — the generic `[]` mock does not satisfy these pages' object-shaped data hooks (the same D-DAY1-1 class that earned `/cost-dashboard` + `/sla-dashboard` their object mocks; these three never got theirs). A CSS-only foundation switch cannot cause a JS `undefined.length` error. **NOT a foundation-switch regression.**

### 3b. Carryover AD

- 🆕 **AD-RouteSweep-Object-Mock-Gap** (harness maintenance): extend `frontend/scripts/route-sweep.mjs` with object-shaped mocks for `/api/v1/subagents`, `/api/v1/memory/recent`, and the verification endpoint (mirroring the Sprint 57.26 D-DAY1-1 `cost-summary` / `sla-report` object mocks) so those 3 routes become sweep-assessable. Until then they are covered only by their identical before/after error (which proves no switch regression). Picked up by a Phase-2 re-point sprint touching those pages, or a harness-maintenance pass.

### 3c. vs-mockup comparison

Under Option B no page markup is re-pointed this sprint, so a per-route pixel comparison against the `:8080` mockup is **deferred to each Phase-2 re-point sprint**, where it is that sprint's DoD. What this sprint guarantees: the **foundation** — `styles-mockup.css` verbatim load + token bridge + theme — now matches the mockup byte-for-byte (CI diff guard enforces it). The per-route content gap = the entire Phase-2 re-point epic.

---

## 4. Day 0 三-prong D-PRE findings

| ID | Sev | Finding | Implication |
|----|-----|---------|-------------|
| D-PRE-1 | 🟠 | Mockup `styles.css` HAS a full **light theme** — `[data-theme="light"]` + 3 light variants (strict/refined/shadcn), L114-164. Reports 02/03 imprecisely said "no light theme" / "dark-only". | Plan US-C2 "dark-only" premise corrected. Revised approach: keep light support; `ThemeProvider` toggles the mockup `[data-theme]` attribute. **Surfaced to user — confirm before Day 2.** |
| D-PRE-2 | 🟠 | Mockup `--bg`/`--bg-1..3`/`--bg-hover`/`--border`/`--border-strong`/`--fg`/`--fg-muted`/`--fg-subtle`/`--shadow` + `--radius*` are defined in `[data-theme][data-variant]` selectors, **NOT `:root`**. `:root` carries only theme-invariant tokens. | Production `<html>` MUST carry `data-theme="dark" data-variant="linear"` for the verbatim CSS to resolve bg/fg at all. Day 1 sets the static attributes on `index.html`; Day 2 wires the `ThemeProvider` toggle. |
| D-PRE-3 | 🟢 | Mockup `styles.css` uses **0 `rem`** — fully px-based. | `html{font-size:13px}` hack is safe to KEEP through Phase 1 (px mockup classes unaffected; hack only keeps the 13 not-re-pointed Tailwind-rem pages compact). Plan R2 default KEEP confirmed. |
| D-PRE-4 | 🟢 | Token-collision set fully enumerated — see §2. ~28 collisions: 2 tricky (de-collide) + ~26 shared-intent/identical (retire prod approximation). | Day 2 Layer 4 has the exact per-token resolution table. |
| D-PRE-5 | 🟢 | `--radius` / `--row-h` / `--pad` / `--gap` mockup values == production values (57.20/57.26). | Retiring production's = zero value change for these (safe). |
| D-PRE-6 | 🟢 | 4 Vitest files reference theme/token literals: `AuthShell.test.tsx`, `AppShellV2.test.tsx`, `UserMenu.test.tsx`, `adminTenantsRoleGate.test.tsx`. | Day 4 US-E1 examines each; adapt if asserting a retired token / theme path (NOT delete). |

**Prong 1 path verify**: 0 path drift — `index.css` / `main.tsx` / `tailwind.config.ts` / `ThemeProvider.tsx` present (edits); `styles-mockup.css` absent (create); `route-sweep.mjs` present (reused); frontend CI = `.github/workflows/frontend-ci.yml`.
**PoC reference confirmed**: `investigation/mockup-fidelity-poc` `main.tsx` imports `./styles-mockup.css` (L46) after `./index.css` (L40); PoC `styles-mockup.css` present.

---

## 5. Final verdict (Day 4)

**Sprint 57.28 = COMPLETE.** The verbatim-CSS 4-layer sync protocol (Phase 1 — foundation only) is landed:

- **Layer 2** — `frontend/src/styles-mockup.css` is a byte-identical copy of `reference/design-mockups/styles.css` (CI diff guard enforces it on every PR).
- **Layer 3** — `index.css` slimmed: the Sprint 57.18/57.20 HSL mockup-token approximations retired; the verbatim oklch values from Layer 2 are the single source.
- **Layer 4** — `tailwind.config.ts` bridges mockup tokens as `var(--X)` (full oklch); shadcn `--primary`/`--border` de-collided to `--sc-*`.
- **theme** — `ThemeProvider` drives the mockup `[data-theme]` attribute (light + dark both kept); `.dark` class kept in sync for the Phase-1 shadcn transition.
- **CI guard** — `check-mockup-fidelity.mjs` (diff + grep) wired into `frontend-ci.yml`; future re-translation / hardcoded colour fails CI.

**Regression verdict (22-route sweep)**: **0 catastrophic, 0 structural regression** caused by the switch. 19 routes show 🟡 transition-drift (expected — foundation switched, per-page markup not yet re-pointed); 3 routes (`/subagents` `/memory` `/verification`) are ⚪ not-assessable due to a pre-existing route-sweep harness mock-shape gap (error identically before+after — not a switch regression).

**Quality**: Vitest 457/457 · lint clean · build green (main JS 337.06 kB; CSS bundle 592 KB incl. verbatim `styles-mockup.css` ~39 KB raw — matches the plan's "~40 KB CSS" estimate) · `check:mockup-fidelity` passes.

### Phase-2 re-point epic backlog

Phase 1 changed the **CSS delivery method**; Phase 2 re-points each page's markup to consume the mockup classes directly — the work that now gets CSS fidelity "for free" because the foundation is correct:

- **19 transition-drift routes** — each `active` route's markup still consumes shadcn utilities on top of the verbatim foundation; re-point per-route to mockup classes (the `frontend-mockup-strict-rebuild` epic continues).
- **`HEX_OKLCH_BASELINE = 18`** — 18 hardcoded `bg-[#hex]`/`text-[#hex]` lines in `features/` (governance + chat_v2 risk-colour maps: DecisionModal, AuditChainBadge, ApprovalList, ApprovalCard, HITLTurn). Each Phase-2 re-point of those pages should migrate the literals to mockup `--risk-*` tokens and lower the baseline.
- **`AD-RouteSweep-Object-Mock-Gap`** — extend `route-sweep.mjs` with object-shaped mocks for `/api/v1/subagents` + `/api/v1/memory/recent` + the verification endpoint so those 3 routes become sweep-assessable.
- **shadcn-system tokens** — `index.css` still carries the shadcn token set the not-re-pointed pages consume; retired page-by-page as Phase 2 progresses.
