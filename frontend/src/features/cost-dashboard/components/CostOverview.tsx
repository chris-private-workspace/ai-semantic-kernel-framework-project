/**
 * File: frontend/src/features/cost-dashboard/components/CostOverview.tsx
 * Purpose: Cost Dashboard top-level — verbatim re-point to mockup page-admin.jsx:201-320 (Sprint 57.31 Day 1).
 * Category: Frontend / cost-dashboard / components
 * Scope: Phase 57 / Sprint 57.24 Day 1 US-B1 → 57.31 Day 1 (verbatim re-point — 3rd Phase-2 per-page re-point)
 *
 * Description:
 *   Sprint 57.31 Day 1 verbatim re-point: drop translated-Tailwind PageHead /
 *   StatCard / CardShell wrappers in favor of inline mockup verbatim markup
 *   (.page-head / .grid-stats / .grid-main / inline .page-title / .page-sub /
 *   .route-pill) + mockup-ui <Stat> / <Spark> / <Button> / <Badge> / <Card>
 *   primitives per page-admin.jsx:201-320.
 *
 *   The 4 child widgets (CategoryBarsCard / TenantTopTable / ProviderMixCard
 *   / CostBreakdownTable) get their own Day 1 verbatim re-points; this file
 *   composes them.
 *
 *   Backend reused: useCostSummary TanStack hook + GET /api/v1/cost-summary
 *   (Sprint 57.9 US-6 Day 4 stable).
 *
 * Created: 2026-05-06 (Sprint 57.1 Day 1)
 * Last Modified: 2026-05-23
 *
 * Modification History (newest-first):
 *   - 2026-05-23: Sprint 57.31 Day 1 — verbatim re-point to mockup .page-head/.grid-stats/.grid-main per page-admin.jsx:201-320 (drop PageHead/StatCard/CardShell)
 *   - 2026-05-19: Sprint 57.24 Day 2 US-C3 — §6 ProviderMixCard admin-scope (+ §5/§6 wrap 2-col grid; Group C complete)
 *   - 2026-05-19: Sprint 57.24 Day 2 US-C2 — §5 TenantTopTable admin-scope top-8 (parent-gated; fixture + banner)
 *   - 2026-05-19: Sprint 57.24 Day 2 US-C1 — §4 CategoryBarsCard 6-bar breakdown (fully-fixture per R3)
 *   - 2026-05-19: Sprint 57.24 Day 1 US-B3 — §3 30d Spend over time card (CardShell + AreaChart + BackendGapBanner)
 *   - 2026-05-19: Sprint 57.24 Day 1 US-B2 — 4-stat sparkline grid (Spark + StatCard) with real Spend MTD + 3 fixtures
 *   - 2026-05-19: Sprint 57.24 Day 1 US-B1 — PageHead + admin scope gate + page-actions stubs (rebuild start)
 *   - 2026-05-11: Sprint 57.15 — inline styles → Tailwind utility classes (AD-Inline-Style-Cleanup-Sweep)
 *   - 2026-05-10: Sprint 57.13 US-B2 — loading → <CardSkeleton>; error → <ErrorRetry> (components/ui)
 *   - 2026-05-10: Sprint 57.13 US-A2 — tenant_id from authStore.tenant.id (was URL ?tenant_id=)
 *   - 2026-05-09: Sprint 57.9 US-6 Day 4 — migrate to useCostSummary TanStack hook (drop store loadData/data/loading/error)
 *   - 2026-05-10: Sprint 57.7 US-B3 — migrate to AppShell + Tailwind utility classes
 *   - 2026-05-06: Initial creation (Sprint 57.1 Day 1 / US-2 — Cost overview)
 *
 * Related:
 *   - reference/design-mockups/page-admin.jsx:201-320 (CostPage canonical mockup)
 *   - frontend/src/components/mockup-ui.tsx (Card / Stat / Spark / Button / Badge / Icon primitives)
 *   - frontend/src/pages/overview/OverviewPage.tsx (Sprint 57.29 verbatim re-point reference)
 *   - sprint-57-31-plan.md §Technical Specifications
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: inline-style literals are mockup page-admin.jsx visual-layer literals copied byte-for-byte; STYLE.md §1 escape hatch + frontend-mockup-fidelity.md */

import type { CSSProperties } from "react";
import { useTranslation } from "react-i18next";

import { AreaChart } from "../../../components/charts";
import { Badge, Button, Card, Spark, Stat } from "../../../components/mockup-ui";
import { BackendGapBanner } from "../../../components/ui/BackendGapBanner";
import { CardSkeleton, ErrorRetry } from "../../../components/ui";
import { useAuthStore } from "../../auth/store/authStore";
import { SPEND_OVER_TIME_30D } from "../__fixtures__/spendOverTime30d";
import { useCostSummary } from "../hooks/useCostSummary";
import { useCostStore } from "../store/costStore";
import { CategoryBarsCard } from "./CategoryBarsCard";
import { CostBreakdownTable } from "./CostBreakdownTable";
import { ProviderMixCard } from "./ProviderMixCard";
import { TenantTopTable } from "./TenantTopTable";

// Mirrors backend _ADMIN_PLATFORM_ROLES (platform_layer/identity/auth.py); same
// pattern as AdminTenantsPage. Used to gate the admin-only scope Badge in the
// page-head and the cross-tenant + cross-provider widgets.
const PLATFORM_ADMIN_ROLES = ["admin", "platform_admin"];

// Sparkline fixtures for the 4-stat grid. Spend MTD trend tail ($2,847) matches
// the mockup demo value; other 3 fully fixture pending backend metric surfaces
// (tokens.total / runs.count / cache.hit_rate; AD-Cost-Dashboard-Backend-
// Extensions-Phase58). When real data lands, hooks replace inline arrays.
const STAT_FIXTURES = {
  spendMtdSpark: [1200, 1450, 1700, 1980, 2200, 2400, 2600, 2847],
  tokensMtdSpark: [8, 9, 10, 11, 12, 13, 14, 14.2],
  costPerRunSpark: [0.044, 0.046, 0.048, 0.05, 0.05, 0.052, 0.052],
  cacheHitSpark: [28, 30, 32, 34, 35, 36, 37, 38],
};

// Verbatim from page-admin.jsx:218 / 225 / 255 / 257 — section layout consts
// reused by the page below. matches Sprint 57.29 OverviewPage pattern.
const layoutStyles = {
  page: { padding: 18 } satisfies CSSProperties,
  gridStats: {
    display: "grid",
    gridTemplateColumns: "repeat(4, 1fr)",
    gap: 12,
    marginBottom: 14,
  } satisfies CSSProperties,
  gridMain: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: 14,
    marginBottom: 14,
  } satisfies CSSProperties,
  spacer14: { height: 14 } satisfies CSSProperties,
};

export function CostOverview() {
  const { t } = useTranslation("common");
  const tenantId = useAuthStore((s) => s.tenant?.id ?? "");
  const roles = useAuthStore((s) => s.roles);
  const isPlatformAdmin = roles.some((r) => PLATFORM_ADMIN_ROLES.includes(r));
  const currentMonth = useCostStore((s) => s.currentMonth);

  const { data, isLoading, error, refetch } = useCostSummary(tenantId, currentMonth);

  return (
    <div style={layoutStyles.page}>
      {/* ── page head (verbatim from page-admin.jsx:203-216) ── */}
      <div className="page-head">
        <div>
          <div className="page-title">{t("cost.pageTitle")}</div>
          <div className="page-sub">
            {t("cost.pageSub")}
            <span className="route-pill">/cost-dashboard</span>
            {isPlatformAdmin && (
              <span data-testid="cost-admin-scope-badge" style={{ display: "inline-flex" } satisfies CSSProperties}>
                <Badge tone="warning">{t("cost.adminScope")}</Badge>
              </span>
            )}
          </div>
        </div>
        <div className="page-actions">
          <Button
            variant="outline"
            size="sm"
            icon="filter"
            disabled
            title={t("cost.action.filterPending")}
            data-testid="cost-action-by-tenant"
          >
            {t("cost.action.byTenant")}
          </Button>
          <Button
            variant="outline"
            size="sm"
            icon="download"
            disabled
            title={t("cost.action.csvPending")}
            data-testid="cost-action-csv"
          >
            {t("cost.action.csv")}
          </Button>
        </div>
      </div>

      {/* ── §2 .grid-stats 4-stat sparkline row (verbatim from page-admin.jsx:218-223) ──
          Spend MTD value swaps to real data.total_cost_usd when loaded; other 3
          + all 4 sparklines are fixture pending backend metric surfaces
          (AD-Cost-Dashboard-Backend-Extensions-Phase58). */}
      <div style={layoutStyles.gridStats} data-testid="cost-stat-grid">
        <Stat
          label={t("cost.stat.spendMtd")}
          value={data ? `$${Number(data.total_cost_usd).toLocaleString()}` : "$—"}
          delta="+8.4%"
          deltaDir="down"
          spark={<Spark points={STAT_FIXTURES.spendMtdSpark} tone="var(--memory)" />}
        />
        <Stat
          label={t("cost.stat.tokensMtd")}
          value="14.2"
          unit="M"
          delta="+2.1M"
          deltaDir="up"
          spark={<Spark points={STAT_FIXTURES.tokensMtdSpark} />}
        />
        <Stat
          label={t("cost.stat.costPerRun")}
          value="$0.052"
          delta="+$0.004"
          deltaDir="down"
          spark={<Spark points={STAT_FIXTURES.costPerRunSpark} tone="var(--warning)" />}
        />
        <Stat
          label={t("cost.stat.cacheHit")}
          value="38"
          unit="%"
          delta="+4pp"
          deltaDir="up"
          spark={<Spark points={STAT_FIXTURES.cacheHitSpark} tone="var(--success)" />}
        />
      </div>

      {/* ── §3 + §4 .grid-main row 1 (verbatim from page-admin.jsx:225-253) ──
          30d Spend over time AreaChart (left) + 6-bar Category breakdown (right). */}
      <div style={layoutStyles.gridMain}>
        <Card
          title={t("cost.spendOverTime.title")}
          subtitle={t("cost.spendOverTime.subtitle")}
        >
          <AreaChart data={SPEND_OVER_TIME_30D} tone="var(--memory)" height={200} />
          <BackendGapBanner reason={t("cost.banner.areaChart30d")} />
        </Card>
        <CategoryBarsCard />
      </div>

      {/* ── 14px spacer (verbatim from page-admin.jsx:255) ── */}
      <div style={layoutStyles.spacer14} />

      {/* ── §5 + §6 .grid-main row 2 admin-scope (verbatim from page-admin.jsx:257-318) ──
          TenantTopTable (cross-tenant fixture) + ProviderMixCard (cross-provider fixture).
          Mounted only for platform admins (parent gate via isPlatformAdmin; child
          components are admin-agnostic for unit-test reuse). */}
      {isPlatformAdmin && (
        <div style={layoutStyles.gridMain}>
          <TenantTopTable />
          <ProviderMixCard />
        </div>
      )}

      {/* ── Backend-bound bottom section: tenant-scope cost breakdown + states ──
          Real backend by_type data (NOT fixture); shown to all authenticated
          users (single-tenant scope, no admin gate). */}
      {!tenantId && (
        <p
          className="subtle"
          style={{ fontSize: 13, color: "var(--danger)" } satisfies CSSProperties}
        >
          No tenant in your session.
        </p>
      )}

      {isLoading && tenantId && <CardSkeleton count={3} />}

      {error && (
        <div role="alert">
          <ErrorRetry error={error} onRetry={() => void refetch()} />
        </div>
      )}

      {data && !isLoading && !error && (
        <>
          <p style={{ fontSize: 15, marginTop: 14 } satisfies CSSProperties}>
            <strong>Total cost ({data.month}):</strong> ${data.total_cost_usd}
          </p>
          <CostBreakdownTable data={data} />
        </>
      )}
    </div>
  );
}
