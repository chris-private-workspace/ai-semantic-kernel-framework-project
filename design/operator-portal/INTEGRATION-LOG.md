# Mockup → Production Port Tracking

> **Authoritative source**: this file. Sprint 57.18 cp'd `reference/design-mockups/` → `design/operator-portal/` as long-term design reference. Production code under `frontend/src/` rolls forward; this directory stays as the design-time snapshot. Each row below is updated by the porting sprint that lands real content in production.

## Status

- **Sprint 57.18 (2026-05-16)**: mockup imported as design reference. No pages ported yet. 20 PROP/DRAFT stub routes created in `frontend/src/routes.config.ts` (all render `ComingSoonPlaceholder.tsx` until ported).
- **Sprint 57.19 (2026-05-17)**: Round 1 of 14 priority units shipped — **7 of 28** rows transitioned to SHIPPED (Operations 4 pages + Topbar overlays 3). Brand color US-A1 indigo applied. Backend Cat 1/3/7/11 gap fills (US-B1-B4) accompany frontend ports.
- **Sprint 57.20+ (planned)**: Round 2 Auth 4 補完 + Round 3 Governance 3 補完 + retrofit of 9 existing ship pages per DRIFT-REPORT.md output.

## Port Progress

| Mockup file | Production target | Sprint | Status | Notes |
|---|---|---|---|---|
| page-overview.jsx | frontend/src/pages/overview/index.tsx (~580 lines) | Sprint 57.19 US-C1 | **SHIPPED** | Priority 1 (Operations core); 4-KPI + 6 widgets + 2 SVG + 4 quick-action; Vitest 6 cases |
| page-agents.jsx (orchestrator section) | frontend/src/pages/orchestrator/index.tsx (~570 lines) | Sprint 57.19 US-C2 | **SHIPPED** | Priority 1; 6 sub-tabs (Config/Prompt/Tools/Subagents/Budgets/Policies); NEW components/ui/tabs.tsx (~75 lines); Vitest 7 cases |
| page-agents.jsx (subagents section) | frontend/src/pages/subagents/index.tsx (~390 lines) | Sprint 57.19 US-C3 | **SHIPPED** | Priority 1; inline 2-col NOT Sheet drawer (D-DAY4-1 mockup fidelity); 4-mode KPI + 8 fixture rows + inner Tabs detail; Vitest 7 cases |
| page-platform.jsx (state-inspector section) | frontend/src/pages/state-inspector/index.tsx (~370 lines) | Sprint 57.19 US-C4 | **SHIPPED** | Priority 1; hybrid live+fixture (chain fixture + current-state hybrid via Cat 7 GET when ?session_id=<uuid>); Vitest 8 cases |
| page-platform.jsx (compaction section) | frontend/src/pages/compaction/ | TBD | Stub | Priority 2 |
| page-platform.jsx (jit-retrieval section) | frontend/src/pages/jit-retrieval/ | TBD | Stub | Priority 2 |
| page-agents.jsx (subagent-tree section) | frontend/src/pages/subagent-tree/ | TBD | Stub | Priority 2 |
| topbar-overlays.jsx (CommandPalette ⌘K) | frontend/src/components/topbar/CommandPalette.tsx (~200 lines) | Sprint 57.19 US-D1 | **SHIPPED** | Priority 1 (Topbar overlay); cmdk@^1.1.1 inside shadcn Dialog + 4 groups (Actions/Pages/Tenants/Sessions); global ⌘K/Ctrl+K hotkey via AppShellV2; Vitest 6 cases |
| topbar-overlays.jsx (NotificationsPanel) | frontend/src/components/topbar/NotificationsPanel.tsx (~170 lines) | Sprint 57.19 US-D2 | **SHIPPED** | Priority 1; 6 mockup fixture items + Tabs (All/Unread) + mark-all + 4 severity tokens; bell button in AppShellV2; Vitest 7 cases |
| topbar-overlays.jsx (UserMenu) | frontend/src/components/UserMenu.tsx (EXTENDED +~50 LoC) | Sprint 57.19 US-D3 | **SHIPPED** | Priority 1; D-DAY5-1 — extended existing UserMenu (AP-4 Potemkin avoidance) NOT created dead topbar/UserMenu.tsx; +3 tenant fixtures + 4 nav items (Profile/MFA/Preferences/Theme toggle); existing Vitest 6 cases wrap ThemeProvider |
| page-register.jsx | frontend/src/pages/auth/register/ | Sprint 57.19? | Not started | Priority 1 (Auth flow) |
| page-invite.jsx | frontend/src/pages/auth/invite/ | Sprint 57.19? | Not started | Priority 1 |
| page-mfa.jsx | frontend/src/pages/auth/mfa/ | Sprint 57.19? | Not started | Priority 1 |
| page-expired.jsx | frontend/src/pages/auth/expired/ | Sprint 57.19? | Not started | Priority 1 |
| page-governance.jsx (redaction section) | frontend/src/pages/redaction/ | Sprint 57.19? | Stub | Priority 1 (Governance) |
| page-platform.jsx (error-policy section) | frontend/src/pages/error-policy/ | Sprint 57.19? | Stub | Priority 1 |
| page-governance.jsx (audit-log section) | frontend/src/pages/audit-log/ | Sprint 57.19? | DRAFT in routes.config.ts (active=false) | Priority 1; promote to active |
| page-extras.jsx (incidents section) | frontend/src/pages/incidents/ | TBD | Stub | Business domain |
| page-models.jsx | frontend/src/pages/cache-manager/ | TBD | Stub | Observability |
| page-sse.jsx | frontend/src/pages/sse/ | TBD | Stub | Observability |
| page-platform2.jsx (devui section) | frontend/src/pages/devui/ | TBD | Stub | Observability |
| page-models.jsx | frontend/src/pages/models/ | TBD | Stub | Resources |
| page-tools.jsx | frontend/src/pages/tools/ | TBD | Stub | Resources |
| page-platform2.jsx (tenant-onboarding section) | frontend/src/pages/tenant-onboarding/ | TBD | Stub | Admin |
| page-admin.jsx (pricing section) | frontend/src/pages/pricing/ | TBD | Stub | Admin |
| page-admin.jsx (rbac section) | frontend/src/pages/rbac/ | TBD | Stub | Admin |
| page-account.jsx (profile section) | frontend/src/pages/profile/ | TBD | DRAFT in routes.config.ts (active=false) | Admin |
| page-account.jsx (mfa section) | frontend/src/pages/mfa/ | TBD | DRAFT in routes.config.ts (active=false) | Admin |

## Dev Server (Mockup Prototype)

To preview the mockup as a live page (no build step — React via Babel CDN):

```bash
cd design/operator-portal
python -m http.server 8080
# open http://localhost:8080/
```

Sidebar shows all 32 routes across 6 categories. Topbar `⌘K` opens CommandPalette. Theme + variant + density switchable via top-right Tweaks panel.

## Authoritative References

- `design/operator-portal/AGENTS.md` — 守則 for editing the mockup prototype (do NOT modify production files via mockup edits)
- `design/operator-portal/DESIGN_RATIONALE.md` (192 lines) — every menu entry's rationale + V2 11+1 範疇 mapping
- `frontend/src/routes.config.ts` — production registry (33 entries after Sprint 57.18)
- `docs/03-implementation/agent-harness-planning/01-eleven-categories-spec.md` — V2 backend 範疇 spec
- `docs/03-implementation/agent-harness-planning/16-frontend-design.md` — V2 frontend design philosophy

## Modification History

- 2026-05-16: Sprint 57.18 — initial creation; tracks Sprint 57.19+ rolling port progress (US-A1)
