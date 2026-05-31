# A-6 Deep Analysis: Frontend Real-Data Wiring

**Purpose**: Single-point deep analysis of which frontend pages render real backend data vs fixtures, classified 3-ways (pure-wiring / backend-missing / partial), with the key framing that — per the Mockup-Fidelity rule — fixtures are *intended interim debt*, so A-6 is mostly "do the planned follow-up wiring", with two genuine pure-wiring wins. Analysis only.
**Category / Scope**: Frontend ↔ Backend data wiring (breadth, not a single seam) / Phase 57+ (post Sprint 57.63)
**Created**: 2026-05-31
**Last Modified**: 2026-05-31
**Status**: Active (analysis input for future sprints)

> **Modification History**
> - 2026-05-31: Initial creation — A-6 (final Area-A item); 2-agent parallel audit + spot-verification of the two pure-wiring claims (admin-tenants, memory)

> **Related**: `integration-progress-20260531.md` (Area A item 6); `CLAUDE.md §Frontend Mockup-Fidelity Hard Constraint`; `docs/rules-on-demand/frontend-mockup-fidelity.md §DoD`; `16-frontend-design.md §page→endpoint mapping`.

---

## 0. Headline

A-6 is **breadth, not depth** — unlike A-1…A-5 (one backend seam each), it is a portfolio of ~20 pages each at a different wiring stage. The crucial framing (verified against `CLAUDE.md §Frontend Mockup-Fidelity`): **shipping a widget on fixtures + `BackendGapBanner` + a follow-up wiring sprint is the *intended* workflow, not a regression** ("後端尚未支援的 widget → 仍依 mockup 視覺實作，data 用 fixture；後續 sprint 加 backend API"). So most of A-6 is *expected interim debt*. The actionable-now subset is small and high-value: **two pages (`admin-tenants`, `memory`) are pure-wiring** — their backend endpoints exist and the rebuild dropped already-working data wiring (a mild real regression, not planned debt). Everything else is either *partial* (core data real, sub-charts fixture) or genuinely *backend-missing* (Phase 58+).

---

## 1. Spot-verified pure-wiring wins (the actionable core)

| Page | Hook | Service | Backend endpoint | Current render | Verdict |
|------|------|---------|------------------|----------------|---------|
| **admin-tenants** | ✅ `hooks/useAdminTenants.ts` exists | ✅ `services/adminTenantsService.ts` exists | ✅ `GET /api/v1/admin/tenants` (`admin/tenants.py`) | ❌ `TenantsTable.tsx:94` `.map(TENANTS_FIXTURE)` + `TenantsStatsStrip.tsx:28` `STATS_FIXTURE` | **PURE WIRING** — re-mount the hook, drop `_fixtures`. Page comment (`pages/admin-tenants/index.tsx:13`) literally says "useAdminTenants hook unmounted in this rebuild". ~½ day. |
| **memory** | ⚠️ **hooks dir does NOT exist** (only `types.ts` *references* `useMemoryRecent/ByScope/ByTime` as planned) | ✅ `services/memoryService.ts` exists | ✅ 3 GET endpoints (`memory.py`; role/session layers 501) | ❌ 5 components all `import … from "../_fixtures"` (MemoryMatrix/MemoryPageHeader/RecentMemoryOpsCard/TimeTravelScrubber) | **PURE WIRING (a notch more)** — service + backend exist but the TanStack hooks must be **written** (3 hooks) then components re-pointed. ~3-5h. (Agent missed that the hooks don't exist yet — spot-check caught it.) |

These two are the only places where real, previously-working data wiring was **lost** in the Sprint 57.18-57.43 mockup-rebuild epic. They restore capability, not add it.

---

## 2. The per-page matrix (audit agent; 2 rows spot-verified)

| Page / widget | Data source today | Real hook? | Backend endpoint? | Gap class |
|---------------|-------------------|-----------|-------------------|-----------|
| chat-v2 | real SSE (`chatService.ts` + `useLoopEventStream`) | mounted | ✅ chat/sessions/loops/verification | **FULL REAL** |
| governance/approvals | `useApprovals`+`useApprovalDecide` | mounted | ✅ governance/ | FULL REAL |
| governance/audit-log | `useAuditLog` → `GET /audit/log` | mounted | ✅ audit.py | FULL REAL |
| loop-debug | in-memory `useChatStore.rawEvents` (SSE) | mounted | n/a (in-memory) | FULL REAL (history deferred) |
| auth/register | real form → auth.py | mounted | ✅ auth.py | FULL REAL |
| **admin-tenants** | `_fixtures.ts` | ✅ exists, **unmounted** | ✅ exists | **(a) PURE WIRING** ✅verified |
| **memory** | `_fixtures.ts` | service exists, **hooks TBW** | ✅ exists | **(a) PURE WIRING** ✅verified |
| tenant-settings DangerZone | `_fixtures` (intentionally gated) | none | ✅ delete/archive exist | (a) soft-gate (deliberate) |
| cost-dashboard | summary real (`useCostSummary`) + 4 sub-charts fixture | partial | ✅ cost-summary only | (c) PARTIAL |
| sla-dashboard | report real (`useSLAReport`) + 3 sub-charts + sparklines fixture | partial | ✅ sla-report only | (c) PARTIAL |
| verification | list+trace real (`useVerificationRecent`/`useCorrectionTrace`) + 3 stat KPIs fixture | partial | ✅ verification.py | (c) PARTIAL |
| state-inspector | snapshot real (`useStateSnapshot`, when `?session_id=`) + version-chain fixture | partial | ✅ sessions.py (no version-chain endpoint) | (c) PARTIAL |
| tenant-settings (General/FeatureFlags/Quotas/HITL/Members tabs) | core fields real (5 mounted hooks) + edge fields/usage fixture + BackendGapBanners | partial | ✅ all tab endpoints exist | (c) PARTIAL |
| auth/login | email/pw real + 3 SSO buttons disabled | mounted | ✅ auth.py | (c) PARTIAL (SSO Phase 58+) |
| overview — ActiveLoopsCard | real `useActiveLoops`→`GET /loops` | mounted | ✅ loops.py | (c) partial (agent_name placeholder) |
| overview — KPI strip + HITL/CostBurn/Providers/Incidents/ErrorTrend (6 widgets) | hardcoded literals + `__fixtures__` + BackendGapBanner | none | ❌ no KPI-aggregate / 30d-cost / provider / incidents / error-bucket endpoints | (b) BACKEND MISSING |
| orchestrator (Config/Prompt/Tools/Subagents/Budgets/Policies tabs) | inline `TOOLS_FIXTURE`/`SUBAGENTS_FIXTURE` + hardcoded defaults | none | ❌ no orchestrator-config CRUD endpoints | (b) BACKEND MISSING |
| subagents | `useSubagents` mounted but backend returns empty stub → falls back to 8 fixture rows | mounted | ⚠️ `subagents.py` is a shape-stub (no ORM) | (b) BACKEND MISSING (stub) |
| redaction / error-policy | inline fixtures + BackendGapBanner | none | ❌ no redaction / error-policy endpoints | (b) BACKEND MISSING |
| auth/invite | fetch then fixture fallback | partial | ❌ no invite-metadata endpoint (Phase 58+) | (b) BACKEND MISSING |

**Counts**: FULL REAL ≈ 5 · PURE-WIRING ≈ 2 (+1 soft-gate) · PARTIAL ≈ 7 · BACKEND-MISSING ≈ 7 clusters.

---

## 3. Root-cause patterns (why pages are on fixtures)

- **Pattern A — mockup-rebuild dropped real hooks** (admin-tenants, memory): the Sprint 57.18-57.43 verbatim-CSS re-point epic rebuilt pages from mockup JSX and didn't re-mount the existing hooks. `admin-tenants/index.tsx:13` explicitly documents the unmount. **This is the only pattern that lost working wiring** → A-6's pure-wiring wins.
- **Pattern B — backend is a shape-stub** (subagents): `subagents.py` intentionally returns empty + `not_implemented_reason` (no ORM); frontend falls back to fixtures. Needs real backend (overlaps A-3).
- **Pattern C — summary real, sub-charts deferred** (cost, sla, verification, state-inspector, tenant-settings): the primary hook is wired; each sub-chart/edge-field needs a *new* backend endpoint, shipped as fixture + BackendGapBanner per the AP-2 honesty policy. Expected interim.
- **Pattern D — page built before backend existed** (overview widgets, redaction, error-policy, orchestrator): Sprint 57.39 promoted stubs to real pages with verbatim mockup fixtures; no backend endpoints exist. Expected interim per Mockup-Fidelity rule.

---

## 4. Key findings / distinctions

1. **A-6 is mostly "expected debt", not "broken"** — per the Mockup-Fidelity rule, fixtures + BackendGapBanner + follow-up wiring is the *designed* path. The regression bar is "did the widget layout get altered/deleted because backend was missing" — and it wasn't. So most A-6 items are scheduled follow-ups, not defects.
2. **Two genuine regressions** — `admin-tenants` and `memory` had working data wiring that the rebuild dropped (hook/service + backend still exist). These are the actionable, high-ROI fixes; everything else is net-new wiring waiting on a backend.
3. **Most "backend-missing" items need backend FIRST** — the plan (`16-frontend-design.md`) says Phase 58+ widgets ship backend + frontend in the *same paired sprint*, not piecemeal frontend wiring. So A-6's (b) cluster is really "backend feature sprints", not "frontend wiring".
4. **The admin tenant-settings tabs are the success template** — Quotas/RateLimits/FeatureFlags/HITL/Members were shipped backend+frontend together (Sprint 57.54-57.62) and are wired (partial only at edge fields). That paired pattern is what the (b) cluster should follow.
5. **Spot-check value** — the agent claimed "memory: service unmounted"; verification found the *hooks don't exist at all* (only the service), making memory a notch more work than admin-tenants. Confirms the A-5 lesson: verify high-impact claims.

---

## 5. Risks / open questions

1. **Pure-wiring isn't zero-risk**: re-mounting `useAdminTenants` must restore loading/error/empty states + Playwright e2e + keep CSS parity (`styles-mockup.css` diff empty) — the rebuild's verbatim-CSS gains must not regress. DoD is "hook replaces fixture AND mockup-fidelity intact".
2. **memory hooks must be written** (not just re-mounted) + role/session layers return 501 → those tabs stay gapped until A-1/A-3 memory backend lands.
3. **Backend-missing (b) is a backend question** — overview KPI aggregation, 30d cost timeseries, provider traffic-light, incidents, error buckets, redaction rules, error-policy taxonomy, orchestrator-config CRUD: each is a new endpoint + ORM, not frontend work. Prioritize per product value (overview KPIs likely highest — it's the landing page).
4. **subagents real list** overlaps A-3 (needs the subagent ORM/persistence).
5. **No schema/codegen for REST types** (parallel to A-5b for events) — frontend service DTOs are hand-written; same drift risk.

---

## 6. Recommendation

- **A-6a (do now, ~½ day, pure win)**: re-mount `useAdminTenants` in `admin-tenants`, drop `TENANTS_FIXTURE`/`STATS_FIXTURE`, add loading/error/empty + Playwright e2e + keep CSS parity. Restores lost real data on the most data-heavy admin page.
- **A-6b (pure-wiring, ~1 sprint)**: write the 3 memory TanStack hooks (`useMemoryRecent`/`ByScope`/`ByTime` per the `types.ts` plan) against the existing `memoryService` + re-point the 5 memory components; keep role/session tabs gapped (501) until backend lands.
- **A-6c (partial sub-charts, per-dashboard, needs small backend each)**: cost 30d-timeseries + sla latency/slow-ops + verification stat KPIs + state-inspector version-chain — each is a small backend endpoint + frontend hook; ship per-dashboard.
- **A-6d (backend-missing, paired sprints, product-prioritized)**: overview KPI/widgets first (landing page), then redaction/error-policy/orchestrator/subagents-real/invites — backend + frontend in the same sprint per the plan's paired pattern.
- **Sequencing vs the rest of Area A**: A-6a/A-6b are independent and shippable immediately (no dependency on A-1..A-5). A-6c/A-6d are net-new backend features — lower priority than finishing the backend loop wiring (A-1/A-2/A-4) unless a specific page is demo-critical.

**Area-A picture (A-6)**: A-6a (admin-tenants re-mount) = cheapest win in all of Area A · A-6b (memory hooks) = pure-wiring, slightly more · A-6c/d = net-new backend features framed as "frontend gaps" but actually backend work.

---

## 7. Definition-of-done (per the plan's per-page wiring DoD)

Hook replaces fixture (TanStack `useQuery`/`useMutation`, Zustand UI-only) · `BackendGapBanner` / disabled state removed · loading (`<TableSkeleton>`/`<CardSkeleton>`) + error (`<ErrorRetry>` StrictMode-safe) states · ≥2 Playwright e2e (happy + error/empty; admin = 4) hermetic `**/api/v1/**` mock · CSS parity (`diff styles.css styles-mockup.css` empty, no new inline `style=`) · Vitest hook + component coverage · `git diff --stat` = frontend-only (unless a paired backend+frontend Phase-58 feature).

---

## 8. Method note

Synthesized from a 2-agent parallel read-only audit (frontend-wiring matrix + target/backend-availability cross-check), with the two pure-wiring claims (admin-tenants, memory) spot-verified via `git ls-files` + `git grep` on main `526be549` (Sprint 57.63 merged). Tools had recovered from the earlier-session truncation. Effort figures are judgement estimates, not commitments.
