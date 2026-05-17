# Sprint 57.20 Retrospective — AD-Mockup-Direct-Port Foundation

**Sprint**: 57.20 — Shell Rewrite + 2 Anchor Pages (Option W; Frontend-Led, Backend-Follows)
**Branch**: `feature/sprint-57-20-mockup-existing-pages-retrofit`
**Dates**: 2026-05-17
**Calibration class**: `frontend-mockup-direct-port` 0.55 (NEW 1st application; HYBRID weighted blend)
**Commits**: 5 (Day 0 `c0c79829` + Day 1 B1b-d `19c30990` + B1e-f `a361455c` + B1g `<sha>` + Day 2 `d6cc70bd` + Day 3 `d639ceca` + Day 4 `<sha pending>`)

---

## Q1 — What was delivered

**Plan pivot** (Day 0): Original Sprint 57.20 Option Y (Tier 1 retrofit of 5 existing pages) **aborted** after Day 0 Playwright runtime capture revealed 5 shell-level drift dimensions (theme / layout / topbar / sidebar / typography). Replaced with **Option W** (Frontend-Led, Backend-Follows; shell rewrite + anchor pages + token migration).

**Day 0**: Plan/checklist pivot, 12 D-PRE drift findings catalogued (0% scope shift), 6 Playwright reference baseline captures (mockup + production pre).

**Day 1** (3 commits):
- **B1b-d** shell rewrite: AppShellV2 V3 grid `[240px | 1fr]` + NEW `components/layout/Topbar.tsx` (breadcrumb + tenant pill + ⌘K + locale + theme + bell + UserMenu avatar; ~180 lines) + Sidebar enrichment (brand block + LOOP-FIRST + tenant switcher pill + bottom user identity card)
- **B1e-f** theme + font wire: index.css +11 mockup layout tokens × 2 modes (`--bg/--bg-1/--bg-2/--bg-3/--bg-hover/--fg/--fg-muted/--fg-subtle/--border-strong/--primary-soft/--shadow`) + `[data-density]` mechanism + Geist/Noto Sans TC body wire + dark default on `<html>` + tailwind.config.ts +11 color mappings
- **B1g** cascade fix (Vitest 275/277 → 277/277): Topbar title `<span>` → `<h1>` (a11y page-title-is-h1 contract preservation); thread `userMenu` prop AppShellV2 → Topbar override slot (Never Delete Tests rule)
- 4 smoke captures of NEW shell on existing pages (shell/overview/cost-dashboard/governance)

**Day 2** (1 commit `d6cc70bd`): `/overview` token migration shadcn → mockup tree (8 `replace_all` edits: `bg-card → bg-bg-1`, `text-muted-foreground → text-fg-muted`, `hover:bg-muted/40 → hover:bg-bg-hover`, `bg-muted → bg-bg-2`, SVG text fills, etc.). Latent visual bug fix (D-DAY2-1): Sprint 57.19 used `bg-card` (undefined shadcn token) → rendered transparent; migration fixed.

**Day 3** (1 commit `d639ceca`): `/chat-v2` token migration across 5 `chat_v2/components/` files (10 `replace_all` edits). Behavioral preservation 100% (SSE / HITL / state machine / Cat 9 audit / mode toggle / shortcuts). **AD-ChatV2-Full-Mockup-Fidelity** NEW carryover Phase 58+ multi-sprint epic (D-DAY3-1: mockup ~10× richer UX requires multi-sprint backend wire ADs).

**Day 4** (this commit): Sprint 57.19 7-output runtime fidelity check (3 Operations pages POST + 3 Topbar overlay POSTs; `/overview` Day 2 capture reused). DRIFT-REPORT-ROUND-2.md catalogues 16 R2 findings → Sprint 57.21+ AD bundles. Closeout: retrospective + memory snapshot + 4 doc syncs.

**Quality gates**: Vitest **277/277 PASS** ✅ / Build 2.69-2.79s ✅ / Main bundle **320.76 kB unchanged from Sprint 57.19** ✅ / Lint silent (--max-warnings 0) ✅ / Anti-Pattern 11/11 PASS ✅ / 0 backend changes ✅ / 0 features layer touched ✅

---

## Q2 — Calibration ratio analysis

| Metric | Value |
|--------|-------|
| Calibration class | `frontend-mockup-direct-port` 0.55 (NEW 1st application; HYBRID: shell ×0.55 ~35% + per-page mockup-direct ×0.50 ~50% + closeout ×0.80 ~15%) |
| Bottom-up estimate | ~18-22 hr (Day 0 setup 2 hr + Day 1 5-6 hr shell + 1 hr theme + 1 hr font + 4-5 hr Day 2 overview + 5-6 hr Day 3 chat-v2 + 3-4 hr Day 4 verification/closeout) |
| Calibrated commit | ~10-12 hr |
| **Actual elapsed** | ~5-6 hr (Day 0 ~1 hr + Day 1 ~2 hr + Day 2 ~1 hr + Day 3 ~1.5 hr + Day 4 ~1.5 hr) |
| **Ratio `actual/committed`** | **0.45-0.55** (below [0.85, 1.20] band by 0.30-0.40) |
| **Ratio `actual/bottom-up`** | **0.25-0.30** (bottom-up was ~2× too generous) |

### Why under-band by 0.45

1. **Sprint 57.18 token foundation already shipped** — Sprint 57.20 only needed to ADD 11 new mockup tokens (`--bg-1/--fg-muted/etc.`), not rewrite the whole token tree. Sprint 57.18 already shipped 11 semantic + 4 risk tokens.

2. **Sprint 57.19 OverviewPage already 1:1 mockup port** — Day 2 reduced from full rewrite (~4-5 hr) to token migration (~1 hr). Sprint 57.19 Operations 4 pages did the structural mockup port work.

3. **Sprint 57.15-57.16 inline-style sweeps already migrated chat-v2 to Tailwind** — Day 3 reduced from full UX rewrite (~5-6 hr) to token migration (~1.5 hr). Sprint 57.15+ Round 1+2 did the Tailwind structural migration.

4. **chat-v2 full UX gap is multi-sprint** — Day 3 correctly bounded scope to token migration + AD carryover (D-DAY3-1). Trying to do full UX in one sprint would have busted scope 3-5× over.

### When to adjust

Per `When to adjust` 3-sprint window rule: single data point below band by 0.45 is **KEEP** for now (need 3 consecutive < 0.7 to propose multiplier reduction).

If Sprint 57.21 + Sprint 57.22 repeat the pattern (frontend mockup-direct-port → token migration only, no full rewrite needed) → propose `frontend-mockup-direct-port` 0.55 → 0.35-0.40 multiplier adjustment.

If Sprint 57.21 hits a NEW page that genuinely needs structural rewrite (e.g. AD-ChatV2-Full-Mockup-Fidelity) → ratio may swing back into band. Reserve judgement.

---

## Q3 — Anti-Pattern self-check (11/11 PASS sprint-wide)

| AP | Status | Evidence |
|----|--------|----------|
| AP-1 No god component | ✅ | Topbar 180L / AppShellV2 90L / Sidebar 236L / OverviewPage 727L (component-per-card pattern) / 5 chat_v2 components 64-155L |
| AP-2 No Potemkin | ✅ | useActiveLoops real hook; SSE + HITL + governance real services preserved; fixtures explicitly documented as Sprint 57.21+ wire ADs |
| AP-3 No cross-directory scattering | ✅ | NEW Topbar in `components/layout/`; shell components stay in `components/`; chat_v2 components stay in `features/chat_v2/components/` |
| AP-4 No rename-only refactor | ✅ | Day 1 grid layout + new tokens deliver visible mockup-fidelity gain; Days 2-3 fix latent visual bugs (bg-card transparent) |
| AP-5 No hardcoded secrets | ✅ | 0 .env / config / credential changes |
| AP-6 No silent backend assumptions | ✅ | 0 backend changes; fixtures explicit; AD references on every fixture |
| AP-7 No prop drilling | ✅ | Topbar consumes authStore/ThemeProvider via hooks; no 3+ level prop chains |
| AP-8 No event handler swallowing errors | ✅ | useActiveLoops error → `<div role="alert">`; ApprovalCard setError + display; InputBar errorMessage display |
| AP-9 No race conditions | ✅ | TanStack Query refetch + staleTime; chatStore optimistic + SSE overwrite pattern |
| AP-10 No untested critical path | ✅ | Vitest 277/277 covers AppShellV2 / Sidebar / overview / chat-v2 (approval-card.spec etc.) |
| AP-11 No TS any leak | ✅ | tsc 0 errors; 0 new `any` |

---

## Q4 — What went well

- **Plan pivot Day 0 caught early**: Initial Option Y plan was wrong but Playwright MCP runtime capture surfaced the issue before any code was written. Validates Sprint 57.5 dual-scoring framework + 三-prong Step 2.5.
- **Token foundation made migration fast**: Sprint 57.18 shipped 11 semantic + 4 risk tokens; Sprint 57.20 adds 11 layout tokens layer; migration is now ergonomic (`bg-card → bg-bg-1` etc.).
- **Behavioral preservation 100%**: 0 SSE/HITL/state-machine regressions; existing functional layer reuse is sound (Option W validated).
- **Never Delete Tests rule honored**: Day 1 cascade fix preserved AppShellV2.test.tsx by adapting components, not tests.
- **Anti-stop rule continued validation**: 30+ Bash/Edit/Read/Playwright tool calls across 4 days, 0 unnecessary user-blocking pauses.
- **Latent visual bug fix surfaced**: D-DAY2-1 + D-DAY3-2 silent `bg-card` undefined token (Sprint 57.19 + earlier shipped this) → Sprint 57.20 token migration fixes the dark-theme transparency.

---

## Q5 — What to improve

- **Scope discovery cost is high**: Day 2 + Day 3 each took ~30-45 min to read existing implementations + mockup + decide reduced scope. Future sprint plans for "mockup port" should include a Day 0 grep pass on existing implementation tokens + behavior contract before estimating.
- **DRIFT-REPORT-ROUND-2 deferred to Day 4** captures the same pattern as DRIFT-REPORT.md Day 5 deferral in Sprint 57.19. Consider: should "drift catalogue" be incremental per-day rather than EOD?
- **Calibration class is unstable** at 1st application 0.55 = below-band by 0.45. Adjusting to 0.35-0.40 after 2-3 sprints of evidence per `When to adjust` rule.

---

## Q6 — Carryovers opened / closed

### NEW carryovers (Sprint 57.21+ ADs)

1. **🔴 AD-ChatV2-Full-Mockup-Fidelity** (NEW Day 3 D-DAY3-1; multi-sprint epic) — biggest visible UX gap; covers SessionList API + Turn block types + Inspector OTel spans + 6 sub-components
2. **AD-Mockup-Direct-Port-Round-2** (Sprint 57.21+ retrofit of Tier R2-A/B drift findings; 11 items in DRIFT-REPORT-ROUND-2)
3. **AD-Geist-Font-Asset-Bundling** (NEW Day 1; Phase 58+ self-host via `@fontsource/geist-sans`)

### Reaffirmed Sprint 57.19 carryovers (Phase 58+)

- AD-Subagent-RealList-Phase58 (Cat 11 wire)
- AD-Loop-Session-Enrich-Phase58 (Cat 1 wire)
- AD-Overview-Backend-Wire (folds R2-1 + R2-2; Sprint 57.21+)
- AD-Orchestrator-Backend-Wire (R2-6)
- AD-State-VersionChain-Phase58 (R2-8)
- AD-CommandPalette-Backend-Wire (R2-9)
- AD-NotificationsPanel-Backend-Feed (R2-10)
- AD-UserMenu-Tenant-Switch (R2-11)

### Closed this sprint

- ✅ AD-Mockup-Existing-Pages-Retrofit Tier 1 (Sprint 57.19 US-F1 DRIFT-REPORT.md): **partially closed** — `/chat-v2` token-migrated Day 3; `/cost-dashboard / /memory / /verification / /governance` still need same treatment (Sprint 57.21+ AD-Mockup-Direct-Port-Round-2)

---

## Q7 — Final disposition

- Sprint 57.20 = ✅ COMPLETE; PR ready to open
- Branch: `feature/sprint-57-20-mockup-existing-pages-retrofit` (6 commits)
- Phase 57+ Frontend status: 16/N → 17/N
- main HEAD update: post-PR-merge `<new sha>`
- Top Sprint 57.21 candidate: **AD-Mockup-Direct-Port-Round-2** (Tier R2-A token migration for remaining 8 ship pages + R2-B overlay backend wires) OR **🔴 AD-ChatV2-Full-Mockup-Fidelity Phase-1** (SessionList endpoint + per-session detail wire) per user direction
