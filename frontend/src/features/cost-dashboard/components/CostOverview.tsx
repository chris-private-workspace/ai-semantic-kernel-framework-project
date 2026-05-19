/**
 * File: frontend/src/features/cost-dashboard/components/CostOverview.tsx
 * Purpose: Cost Dashboard top-level container — mockup-fidelity rebuild (Sprint 57.24 v2).
 * Category: Frontend / cost-dashboard / components
 * Scope: Phase 57 / Sprint 57.24 Day 1 US-B1 (page-head + page-actions; subsequent USs add stat grid / area chart / category bars / tenant table / provider mix)
 *
 * Description:
 *   Sprint 57.24 v2 incremental rebuild from 68-line MVP toward 6-widget-group
 *   mockup-fidelity layout per reference/design-mockups/page-admin.jsx:200-321 (CostPage).
 *
 *   Day 1.3 US-B3 (this state): PageHead (US-B1) + 4-stat sparkline grid
 *   (US-B2) + §3 30-day Spend over time card using new <CardShell> +
 *   <AreaChart> + <BackendGapBanner> primitives. AreaChart uses SPEND_OVER_TIME_30D
 *   fixture data (backend 30-day daily history endpoint not yet shipped per
 *   AP-2 honesty + CLAUDE.md §Mockup-Fidelity backend-gap rule). Existing
 *   Total cost + CostBreakdownTable preserved below temporarily; Day 2 US-C1
 *   supersedes with CategoryBarsCard + remaining Day 2 widgets.
 *
 *   Backend reused: useCostSummary TanStack hook + GET /api/v1/cost-summary
 *   (Sprint 57.9 US-6 Day 4 stable).
 *
 * Created: 2026-05-06 (Sprint 57.1 Day 1)
 * Last Modified: 2026-05-19
 *
 * Modification History (newest-first):
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
 *   - reference/design-mockups/page-admin.jsx:200-321 (CostPage canonical mockup)
 *   - frontend/src/components/ui/PageHead.tsx (US-B1 NEW primitive)
 *   - sprint-57-24-plan.md v2 §Technical Specifications
 */

import { useTranslation } from "react-i18next";

import { AreaChart, Spark, StatCard } from "../../../components/charts";
import { BackendGapBanner } from "../../../components/ui/BackendGapBanner";
import { Button } from "../../../components/ui/button";
import { CardShell } from "../../../components/ui/CardShell";
import { CardSkeleton, ErrorRetry } from "../../../components/ui";
import { PageHead } from "../../../components/ui/PageHead";
import { useAuthStore } from "../../auth/store/authStore";
import { SPEND_OVER_TIME_30D } from "../__fixtures__/spendOverTime30d";
import { useCostSummary } from "../hooks/useCostSummary";
import { useCostStore } from "../store/costStore";
import { CostBreakdownTable } from "./CostBreakdownTable";

// Mirrors backend _ADMIN_PLATFORM_ROLES (platform_layer/identity/auth.py); same
// pattern as AdminTenantsPage. Used to gate the admin-only scope Badge in the
// page-head and (Day 1.4-Day 2) the cross-tenant + cross-provider widgets.
const PLATFORM_ADMIN_ROLES = ["admin", "platform_admin"];

// Sparkline fixtures for Day 1.2 4-stat grid. Spend MTD trend tail ($2,847)
// matches the mockup demo value; other 3 fully fixture pending backend metric
// surfaces (tokens.total / runs.count / cache.hit_rate; AD-Cost-Dashboard-
// Backend-Extensions-Phase58). When real data lands, hooks replace inline arrays.
const STAT_FIXTURES = {
  spendMtdSpark: [1200, 1450, 1700, 1980, 2200, 2400, 2600, 2847],
  tokensMtdSpark: [8, 9, 10, 11, 12, 13, 14, 14.2],
  costPerRunSpark: [0.044, 0.046, 0.048, 0.05, 0.05, 0.052, 0.052],
  cacheHitSpark: [28, 30, 32, 34, 35, 36, 37, 38],
};

export function CostOverview() {
  const { t } = useTranslation("common");
  const tenantId = useAuthStore((s) => s.tenant?.id ?? "");
  const roles = useAuthStore((s) => s.roles);
  const isPlatformAdmin = roles.some((r) => PLATFORM_ADMIN_ROLES.includes(r));
  const currentMonth = useCostStore((s) => s.currentMonth);

  const { data, isLoading, error, refetch } = useCostSummary(tenantId, currentMonth);

  return (
    <div className="space-y-4">
      <PageHead
        title={t("cost.pageTitle")}
        subtitle={t("cost.pageSub")}
        routePath="/cost-dashboard"
        badges={
          isPlatformAdmin && (
            <span
              data-testid="cost-admin-scope-badge"
              className="inline-flex items-center rounded-full bg-warning/15 px-2 py-[2px] text-[10.5px] font-medium uppercase tracking-wide text-warning"
            >
              {t("cost.adminScope")}
            </span>
          )
        }
        actions={
          <>
            <Button
              variant="outline"
              size="sm"
              disabled
              title={t("cost.action.filterPending")}
              data-testid="cost-action-by-tenant"
            >
              {t("cost.action.byTenant")}
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled
              title={t("cost.action.csvPending")}
              data-testid="cost-action-csv"
            >
              {t("cost.action.csv")}
            </Button>
          </>
        }
      />

      {/* §2 4-stat sparkline grid (US-B2). Spend MTD value swaps to real
          data.total_cost_usd when loaded; other 3 + all 4 sparklines are
          fixture pending backend metric surfaces (AP-2 honesty: fixture rows
          plainly demo data; live data integration tracked in Phase 58+
          AD-Cost-Dashboard-Backend-Extensions). */}
      <div className="grid grid-cols-4 gap-3" data-testid="cost-stat-grid">
        <StatCard
          label={t("cost.stat.spendMtd")}
          value={
            data
              ? `$${Number(data.total_cost_usd).toLocaleString()}`
              : "$—"
          }
          delta="+8.4%"
          deltaDir="down"
          spark={
            <Spark
              points={STAT_FIXTURES.spendMtdSpark}
              tone="hsl(var(--memory))"
            />
          }
        />
        <StatCard
          label={t("cost.stat.tokensMtd")}
          value="14.2"
          unit="M"
          delta="+2.1M"
          deltaDir="up"
          spark={<Spark points={STAT_FIXTURES.tokensMtdSpark} />}
        />
        <StatCard
          label={t("cost.stat.costPerRun")}
          value="$0.052"
          delta="+$0.004"
          deltaDir="down"
          spark={
            <Spark
              points={STAT_FIXTURES.costPerRunSpark}
              tone="hsl(var(--warning))"
            />
          }
        />
        <StatCard
          label={t("cost.stat.cacheHit")}
          value="38"
          unit="%"
          delta="+4pp"
          deltaDir="up"
          spark={
            <Spark
              points={STAT_FIXTURES.cacheHitSpark}
              tone="hsl(var(--success))"
            />
          }
        />
      </div>

      {/* §3 Spend over time 30d AreaChart (US-B3). Fixture data pending
          backend 30-day daily history endpoint (AD-Cost-Dashboard-Backend-
          Extensions-Phase58). BackendGapBanner marks fixture state per AP-2. */}
      <CardShell
        title={t("cost.spendOverTime.title")}
        subtitle={t("cost.spendOverTime.subtitle")}
      >
        <AreaChart data={SPEND_OVER_TIME_30D} tone="hsl(var(--memory))" />
        <BackendGapBanner reason={t("cost.banner.areaChart30d")} />
      </CardShell>

      {!tenantId && (
        <p className="text-sm text-destructive">No tenant in your session.</p>
      )}

      {isLoading && tenantId && <CardSkeleton count={3} />}

      {error && (
        <div role="alert">
          <ErrorRetry error={error} onRetry={() => void refetch()} />
        </div>
      )}

      {data && !isLoading && !error && (
        <>
          <p className="text-lg">
            <strong>Total cost ({data.month}):</strong> ${data.total_cost_usd}
          </p>
          <CostBreakdownTable data={data} />
        </>
      )}
    </div>
  );
}
