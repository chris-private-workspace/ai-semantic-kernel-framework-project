# Sprint 57.20 DRIFT-REPORT-ROUND-2: Sprint 57.19 7-output Runtime Fidelity Audit

**Date**: 2026-05-17
**Sprint**: 57.20 Day 4 US-E1
**Audit scope**: Sprint 57.19 7 mockup-port outputs (4 Operations pages + 3 Topbar overlays) **after** Sprint 57.20 shell rewrite + token migration
**Method**: Playwright MCP screenshot capture at 1440×900 + side-by-side compare against `reference/design-mockups/`

## TL;DR

All 7 Sprint 57.19 outputs **auto-inherit** the new Sprint 57.20 shell (dark theme + Geist font + grid layout + Topbar) without rendering crashes. **Cosmetic page-level drift remains** for cards/widgets within those pages — catalogued as **Tier R2** retrofit work for Sprint 57.21+ AD-Mockup-Direct-Port-Round-2.

## Captures inventory (7 PNG triplets at 1440×900)

| Output | Post-Sprint-57.20 capture | Mockup reference | Behavior preserved |
|--------|--------------------------|------------------|--------------------|
| `/overview` | `screenshots/overview/prod-overview-post-day2.png` | mockup `page-overview.jsx` | ✅ useActiveLoops hook + fixture data flows |
| `/orchestrator` | `screenshots/sprint-57-19-inheritance/orchestrator-post.png` | mockup absence (Sprint 57.19 NEW; no direct mockup analog) | ✅ 6 sub-tabs render |
| `/subagents` | `screenshots/sprint-57-19-inheritance/subagents-post.png` | mockup `page-agents.jsx` (partial analog) | ✅ Subagent feature layer loaded |
| `/state-inspector` | `screenshots/sprint-57-19-inheritance/state-inspector-post.png` | mockup absence (Sprint 57.19 NEW; cross-cuts mockup) | ✅ hybrid live+fixture rendering |
| CommandPalette (⌘K) | `screenshots/sprint-57-19-inheritance/command-palette-post.png` | mockup `topbar-overlays.jsx` `CommandPalette` | ✅ 4 groups Actions/Pages/Tenants/Sessions |
| NotificationsPanel (bell) | `screenshots/sprint-57-19-inheritance/notifications-panel-post.png` | mockup `topbar-overlays.jsx` `NotificationsPanel` | ✅ 6 fixture items + tabs + mark-all + 4 severity tokens |
| UserMenu (avatar) | `screenshots/sprint-57-19-inheritance/user-menu-post.png` | mockup `topbar-overlays.jsx` `UserMenu` | ✅ 3 tenant fixtures + 4 nav items + theme toggle |

## Findings catalogue

### Tier R2-A (Sprint 57.21+ — cosmetic Card visual polish)

| # | Page | Drift | Severity | Sprint 57.21+ AD |
|---|------|-------|----------|------------------|
| R2-1 | `/overview` | Cost burn SVG fixture math; real burn data needed | Cosmetic | AD-Overview-Backend-Wire |
| R2-2 | `/overview` | HITL queue fixture; needs real governance feed | Cosmetic | AD-Overview-Backend-Wire (folds R2-1) |
| R2-3 | `/overview` | PROVIDERS fixture; needs Cat 12 telemetry traffic-light feed | Cosmetic | AD-SLA-Provider-Telemetry-Wire |
| R2-4 | `/overview` | RECENT_INCIDENTS fixture; incidents endpoint not in scope | Cosmetic | AD-Incidents-Backend (Phase 58+) |
| R2-5 | `/overview` | ERROR_24H fixture; needs Cat 12 24-hour error histogram | Cosmetic | AD-Error-Telemetry-Wire |
| R2-6 | `/orchestrator` | 6 sub-tabs render OK but content is mostly fixtures; needs real orchestrator state feed | Structural | AD-Orchestrator-Backend-Wire |
| R2-7 | `/subagents` | Empty list with `not_implemented_reason` banner (Sprint 57.19 US-B4); needs real subagent invocations persisted | Structural | AD-Subagent-RealList-Phase58 |
| R2-8 | `/state-inspector` | Hybrid live (session state) + fixture (version chain); needs version chain endpoint | Structural | AD-State-VersionChain-Phase58 |

### Tier R2-B (Sprint 57.21+ — overlay backend wiring)

| # | Overlay | Drift | Severity | Sprint 57.21+ AD |
|---|---------|-------|----------|------------------|
| R2-9 | CommandPalette | Tenants + Sessions groups currently fixture; wire Cat 1 sessions list + Cat 12 tenants index | Structural | AD-CommandPalette-Backend-Wire |
| R2-10 | NotificationsPanel | 6 mockup items local state; need Cat 12 SSE/poll feed spec | Structural | AD-NotificationsPanel-Backend-Feed |
| R2-11 | UserMenu | Tenant switching is fixture; wire paired with WorkOS SCIM | Structural | AD-UserMenu-Tenant-Switch |

### Tier R2-C (Sprint 57.20+ — known carryovers, addressed via Day 3)

| # | Issue | Resolution |
|---|-------|-----------|
| R2-12 | `bg-card` rendered transparent in dark theme (Sprint 57.19 + earlier) | ✅ Day 2 + Day 3 token migration to `bg-bg-1` |
| R2-13 | `text-muted-foreground` AA contrast 3.89:1 on bg-muted (Sprint 57.17 cascade) | ✅ Day 2 + Day 3 token migration to `text-fg-muted` on `bg-bg-2` (AA-compliant new pair) |
| R2-14 | shell layout `flex+sticky` doesn't match mockup edge-to-edge grid | ✅ Day 1 AppShellV2 V3 rewrite |
| R2-15 | typography Geist not wired to body | ✅ Day 1 B1f `@layer base body { font-family }` + Noto Sans TC CDN |

### Tier R2-D (Sprint 57.21+ — full UX rewrite multi-sprint epic)

| # | Page | Drift | Severity | Sprint 57.21+ AD |
|---|------|-------|----------|------------------|
| R2-16 | `/chat-v2` | Mockup `page-chat.jsx` has ~10× richer UX: SessionList API + ChatHeader + TurnRender block types (thinking/tool/memory/verification/subagent_fork) + 4-tab Inspector with OTel spans / memory ops / subagent tree | Structural (multi-sprint) | **AD-ChatV2-Full-Mockup-Fidelity** Phase 58+ multi-sprint epic (NEW Sprint 57.20 Day 3) |

## Inheritance verdict

| Aspect | Verdict |
|--------|---------|
| Shell layout (sidebar + Topbar + main column) | ✅ All 7 outputs inherit correctly |
| Dark theme default | ✅ All 7 outputs inherit (no white flashes; `[data-density="default"]` + `class="dark"` applied) |
| Geist font typography | ✅ All 7 outputs use mockup font stack (system Geist fallback + Noto Sans TC CDN) |
| Topbar breadcrumb + tenant pill + cmdk + locale + theme + bell + UserMenu | ✅ All 7 outputs render correct Topbar |
| Sidebar tenant switcher pill + brand block + bottom user card | ✅ Inherited correctly |
| Overlay positioning (palette modal + bell dropdown + avatar dropdown) | ✅ All open as expected |
| Page-internal Card / widget tokens | ⚠️ Tier R2-A/B/D drift remains for Sprint 57.21+ retrofit |

## Sprint 57.21+ candidate priority (per user 2026-05-16 Q3 alignment "前後端同 sprint")

1. **🔴 AD-ChatV2-Full-Mockup-Fidelity** (multi-sprint epic; Phase 58+) — biggest visible UX gap
2. **AD-Overview-Backend-Wire** (folds R2-1 + R2-2; Sprint 57.21 candidate)
3. **AD-Subagent-RealList-Phase58** + **AD-Loop-Session-Enrich-Phase58** (Cat 1/11 read facade enrichment)
4. **AD-State-VersionChain-Phase58** (Cat 7 endpoint extension)
5. **AD-CommandPalette-Backend-Wire** + **AD-NotificationsPanel-Backend-Feed** + **AD-UserMenu-Tenant-Switch** (overlay bundle)
6. **AD-Mockup-Existing-Pages-Retrofit Tier 1** (Sprint 57.19 US-F1 DRIFT-REPORT.md): 9 pages including cost-dashboard / memory / verification / governance — token migration already applied via Sprint 57.20 to chat-v2; remaining pages need same treatment

## References

- `claudedocs/4-changes/sprint-57-19-existing-pages-drift-audit/DRIFT-REPORT.md` (Sprint 57.19 US-F1; predecessor; ~330 lines)
- `reference/design-mockups/` (canonical visual source)
- Sprint 57.20 progress.md (D-DAY1-1 through D-DAY3-3)
- `.claude/rules/sprint-workflow.md` calibration matrix
