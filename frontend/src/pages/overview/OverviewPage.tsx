/**
 * File: frontend/src/pages/overview/OverviewPage.tsx
 * Purpose: Operator dashboard — final mockup-fidelity assembly (page-head + KPI + grid layout).
 * Category: Frontend / pages / overview
 * Scope: Phase 57 / Sprint 57.27 Day 3 / US-B1 + US-D2
 *
 * Description:
 *   1:1 port of mockup OverviewPage (page-overview.jsx :71-267):
 *   - page-head: PageHead primitive (title + subtitle/route-pill/mono-meta + actions)
 *   - KPI row: 4× StatCard with spark where applicable
 *   - grid2 (1.4fr 1fr): ActiveLoopsCard + HITLQueueCard
 *   - grid2eq #1 (1fr 1fr): CostBurn CardShell + ProvidersCard
 *   - grid2eq #2 (1fr 1fr): IncidentsCard + ErrorTrend CardShell
 *   - QuickActionsStrip
 *
 *   R7: AppShellV2 receives no pageTitle prop so the topbar does NOT duplicate
 *   the in-page title. The page-head title is rendered via <PageHead> at the
 *   top of the page content, matching the mockup canonical layout.
 *
 *   AP-3 reversal complete: zero inline Card / Badge / Stat / RiskBadge
 *   definitions remain. All widget components imported from features/overview/.
 *
 * Created: 2026-05-17 (Sprint 57.19 Day 3 / US-C1)
 * Last Modified: 2026-05-21
 *
 * Modification History (newest-first):
 *   - 2026-05-21: Sprint 57.27 Day 3 — final mockup-fidelity assembly (page-head + KPI + grid layout; AP-3 reversal complete)
 *   - 2026-05-21: Sprint 57.27 Day 2 — extract 5 inline widgets to features/overview/components
 *   - 2026-05-21: Sprint 57.27 Day 1 — extract ActiveLoopsCard + HITLQueueCard to features/overview/components
 *   - 2026-05-17: Sprint 57.20 Day 2 US-C1 — token migration shadcn→mockup tree + shadow-sm on Stat cards
 *   - 2026-05-17: Initial creation (Sprint 57.19 Day 3 / US-C1)
 *
 * Related:
 *   - reference/design-mockups/page-overview.jsx (canonical visual source)
 *   - frontend/src/components/ui/PageHead.tsx (page-head primitive)
 *   - frontend/src/components/charts/StatCard.tsx (KPI stat primitive)
 *   - frontend/src/components/charts/Spark.tsx (sparkline primitive)
 *   - frontend/src/components/ui/CardShell.tsx (card wrapper primitive)
 *   - frontend/src/features/overview/components/ (all 7 widget components)
 *   - frontend/src/components/AppShellV2.tsx (page-level layout shell)
 */

import { ArrowRight, Download, MessageSquare } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { AppShellV2 } from "@/components/AppShellV2";
import { Spark } from "@/components/charts/Spark";
import { StatCard } from "@/components/charts/StatCard";
import { CardShell } from "@/components/ui/CardShell";
import { PageHead } from "@/components/ui/PageHead";
import { RequireAuth } from "@/features/auth/components/RequireAuth";
import { useAuthStore } from "@/features/auth/store/authStore";
import { ActiveLoopsCard } from "@/features/overview/components/ActiveLoopsCard";
import { CostBurnChart } from "@/features/overview/components/CostBurnChart";
import { ErrorTrendChart } from "@/features/overview/components/ErrorTrendChart";
import { HITLQueueCard } from "@/features/overview/components/HITLQueueCard";
import { IncidentsCard } from "@/features/overview/components/IncidentsCard";
import { ProvidersCard } from "@/features/overview/components/ProvidersCard";
import { QuickActionsStrip } from "@/features/overview/components/QuickActionsStrip";
import {
  COST_MTD_SPARK,
  SLA_P95_SPARK,
} from "@/features/overview/__fixtures__/kpiSparklines";

// ───────────────── page ─────────────────

function OverviewPageInner(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();
  // Real auth context for the page-head mono meta (mockup :80 hardcodes
  // "acme-prod · operator" — production shows the logged-in tenant + role).
  const tenant = useAuthStore((s) => s.tenant);
  const roles = useAuthStore((s) => s.roles);

  // Live clock for the mono meta line in page-head (mockup :80)
  const [liveClock, setLiveClock] = useState(() =>
    new Date().toLocaleTimeString("en-US", { hour12: false }),
  );
  useEffect(() => {
    const id = setInterval(() => {
      setLiveClock(new Date().toLocaleTimeString("en-US", { hour12: false }));
    }, 1_000);
    return () => clearInterval(id);
  }, []);

  return (
    // mockup overviewStyles.page = padding: 18
    <div className="flex flex-col gap-[14px] p-[18px]">
      {/* ── page-head (mockup :74-87) ── */}
      <PageHead
        title={t("overview.title")}
        subtitle={t("overview.subtitle")}
        routePath="/overview"
        badges={
          // mono meta: tenant · role · live clock (mockup :80)
          <span className="font-mono text-[11px] text-fg-muted">
            {tenant?.code ?? "—"} · {roles[0] ?? "—"} · {liveClock}
          </span>
        }
        actions={
          <>
            <button
              type="button"
              className="flex items-center gap-1 rounded-[6px] border border-border bg-bg-1 px-3 py-[6px] text-[12px] hover:bg-bg-hover"
            >
              <Download className="h-3.5 w-3.5" />
              {t("overview.export")}
            </button>
            <button
              type="button"
              onClick={() => navigate("/chat-v2")}
              className="flex items-center gap-1 rounded-[6px] bg-primary px-3 py-[6px] text-[12px] text-primary-foreground hover:bg-primary/90"
            >
              <MessageSquare className="h-3.5 w-3.5" />
              {t("overview.newChat")}
            </button>
          </>
        }
      />

      {/* ── KPI row (mockup :90-95) — 4-col gap-[12px] mb handled by flex gap-[14px] parent ── */}
      <div className="grid grid-cols-4 gap-[12px]">
        <StatCard
          label={t("overview.kpi.activeSessions")}
          value="14"
          unit={t("overview.kpi.activeSessionsUnit")}
          delta="+3"
          deltaDir="up"
        />
        <StatCard
          label={t("overview.kpi.hitlPending")}
          value="3"
          unit={t("overview.kpi.hitlPendingUnit")}
          delta={t("overview.kpi.hitlPendingDelta")}
          deltaDir="down"
        />
        <StatCard
          label={t("overview.kpi.costMtd")}
          value="$2,847"
          delta={t("overview.kpi.costMtdDelta")}
          deltaDir="up"
          spark={<Spark points={COST_MTD_SPARK} tone="var(--primary)" />}
        />
        <StatCard
          label={t("overview.kpi.slaP95")}
          value="1.84s"
          unit={t("overview.kpi.slaP95Unit")}
          delta={t("overview.kpi.slaP95Delta")}
          deltaDir="up"
          spark={<Spark points={SLA_P95_SPARK} tone="var(--success)" />}
        />
      </div>

      {/* ── row: active loops + HITL (mockup grid2 = 1.4fr 1fr) ── */}
      <div className="grid grid-cols-[1.4fr_1fr] gap-[14px]">
        <ActiveLoopsCard />
        <HITLQueueCard />
      </div>

      {/* ── row: cost burn + providers (mockup grid2eq = 1fr 1fr) ── */}
      <div className="grid grid-cols-2 gap-[14px]">
        <CardShell
          title={t("overview.costBurn.title")}
          subtitle={t("overview.costBurn.subtitle")}
          actions={
            <button
              type="button"
              onClick={() => navigate("/cost-dashboard")}
              className="flex items-center gap-1 text-[11px] text-fg-muted hover:text-foreground"
            >
              {t("overview.costBurn.details")}
              <ArrowRight className="h-3 w-3" />
            </button>
          }
        >
          <CostBurnChart />
        </CardShell>
        <ProvidersCard />
      </div>

      {/* ── row: incidents + error trend (mockup grid2eq = 1fr 1fr) ── */}
      <div className="grid grid-cols-2 gap-[14px]">
        <IncidentsCard />
        <CardShell
          title={t("overview.errors.title")}
          subtitle={t("overview.errors.subtitle")}
          actions={
            <button
              type="button"
              onClick={() => navigate("/error-policy")}
              className="flex items-center gap-1 text-[11px] text-fg-muted hover:text-foreground"
            >
              {t("overview.errors.policy")}
              <ArrowRight className="h-3 w-3" />
            </button>
          }
        >
          <ErrorTrendChart />
        </CardShell>
      </div>

      {/* ── quick actions strip (mockup :237-266) ── */}
      <QuickActionsStrip />
    </div>
  );
}

export function OverviewPage(): JSX.Element {
  // R7: no pageTitle prop → AppShellV2 topbar does NOT render a duplicate title.
  // The in-page <PageHead> is the sole title for /overview, matching the mockup.
  return (
    <RequireAuth>
      <AppShellV2>
        <OverviewPageInner />
      </AppShellV2>
    </RequireAuth>
  );
}

export default OverviewPage;
