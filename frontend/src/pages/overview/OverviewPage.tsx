/**
 * File: frontend/src/pages/overview/OverviewPage.tsx
 * Purpose: Operator dashboard — verbatim re-point to mockup page-head + overviewStyles; consumes mockup-ui primitives.
 * Category: Frontend / pages / overview
 * Scope: Phase 57 / Sprint 57.29 Day 3 / US-C1
 *
 * Description:
 *   Verbatim re-point of OverviewPage to consume:
 *   - overviewStyles inline-style consts copied byte-for-byte from page-overview.jsx:12-16
 *   - page-head markup inlined verbatim from page-overview.jsx:74-87 (drop <PageHead>)
 *   - KPI row: 4× <Stat> from mockup-ui.tsx (drop <StatCard>/<Spark>)
 *   - grid wrappers: style={overviewStyles.grid2} / style={overviewStyles.grid2eq}
 *   - Chart cards: <Card> from mockup-ui.tsx wrapping CostBurnChart / ErrorTrendChart (drop <CardShell>)
 *   - 7 widget children (ActiveLoopsCard…QuickActionsStrip) unchanged — Day 4 re-points those
 *
 *   R7: AppShellV2 receives no pageTitle prop so the topbar does NOT duplicate
 *   the in-page title. The page-head is rendered inline at the top of the page
 *   content, matching the mockup canonical layout.
 *
 * Created: 2026-05-17 (Sprint 57.19 Day 3 / US-C1)
 * Last Modified: 2026-05-22
 *
 * Modification History (newest-first):
 *   - 2026-05-22: Sprint 57.29 US-C1 — verbatim re-point to mockup .page-head + overviewStyles (drop PageHead/StatCard/CardShell/Spark)
 *   - 2026-05-21: Sprint 57.27 Day 3 — final mockup-fidelity assembly (page-head + KPI + grid layout; AP-3 reversal complete)
 *   - 2026-05-21: Sprint 57.27 Day 2 — extract 5 inline widgets to features/overview/components
 *   - 2026-05-21: Sprint 57.27 Day 1 — extract ActiveLoopsCard + HITLQueueCard to features/overview/components
 *   - 2026-05-17: Sprint 57.20 Day 2 US-C1 — token migration shadcn→mockup tree + shadow-sm on Stat cards
 *   - 2026-05-17: Initial creation (Sprint 57.19 Day 3 / US-C1)
 *
 * Related:
 *   - reference/design-mockups/page-overview.jsx (canonical visual source)
 *   - frontend/src/components/mockup-ui.tsx (Button / Card / Stat / Icon primitives)
 *   - frontend/src/features/overview/components/ (all 7 widget components — unchanged Day 3)
 *   - frontend/src/components/AppShellV2.tsx (page-level layout shell)
 *   - investigation/mockup-fidelity-poc:frontend/src/pages/overview-poc/index.tsx (proven verbatim port reference)
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: inline styles are mockup page-overview.jsx visual-layer literals copied byte-for-byte; re-expressing as Tailwind IS the drift bug this epic kills (STYLE.md §1 escape hatch + frontend-mockup-fidelity.md) */

import type { CSSProperties } from "react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { AppShellV2 } from "@/components/AppShellV2";
import { Button, Card, Spark, Stat } from "@/components/mockup-ui";
import { RequireAuth } from "@/features/auth/components/RequireAuth";
import { useAuthStore } from "@/features/auth/store/authStore";
import { ActiveLoopsCard } from "@/features/overview/components/ActiveLoopsCard";
import { CostBurnChart } from "@/features/overview/components/CostBurnChart";
import { ErrorTrendChart } from "@/features/overview/components/ErrorTrendChart";
import { HITLQueueCard } from "@/features/overview/components/HITLQueueCard";
import { IncidentsCard } from "@/features/overview/components/IncidentsCard";
import { ProvidersCard } from "@/features/overview/components/ProvidersCard";
import { QuickActionsStrip } from "@/features/overview/components/QuickActionsStrip";

// ───────────────── overviewStyles (verbatim from page-overview.jsx:12-16) ─────────────────
// NOTE: loopRow / miniBar / miniBarFill / trafficDot / quickBtn belong to the
// Day-4 widget files (ActiveLoopsCard, QuickActionsStrip) — NOT included here.

const overviewStyles = {
  page: { padding: 18 } satisfies CSSProperties,
  kpiRow: {
    display: "grid",
    gridTemplateColumns: "repeat(4, 1fr)",
    gap: 12,
    marginBottom: 14,
  } satisfies CSSProperties,
  grid2: {
    display: "grid",
    gridTemplateColumns: "1.4fr 1fr",
    gap: 14,
    marginBottom: 14,
  } satisfies CSSProperties,
  grid2eq: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: 14,
    marginBottom: 14,
  } satisfies CSSProperties,
};

// ───────────────── KPI spark data (kept from prior sprint — no fixtures file change) ─────────────────
const COST_MTD_SPARK = [2, 4, 5, 6, 8, 10, 12, 14, 16, 18, 20, 22];
const SLA_P95_SPARK = [2.0, 2.1, 2.0, 1.9, 1.95, 1.88, 1.84];

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
    <div style={overviewStyles.page}>
      {/* ── page head (verbatim from page-overview.jsx:74-87) ── */}
      <div className="page-head">
        <div>
          <div className="page-title">{t("overview.title")}</div>
          <div className="page-sub">
            {t("overview.subtitle")}
            <span className="route-pill">/overview</span>
            <span className="mono subtle">
              {tenant?.code ?? "acme-prod"} · {roles[0] ?? "operator"} · {liveClock}
            </span>
          </div>
        </div>
        <div className="page-actions">
          <Button variant="outline" size="sm" icon="download">
            {t("overview.export")}
          </Button>
          <Button
            variant="primary"
            size="sm"
            icon="chat"
            onClick={() => navigate("/chat-v2")}
          >
            {t("overview.newChat")}
          </Button>
        </div>
      </div>

      {/* ── KPI row (verbatim from page-overview.jsx:90-95) ──
        costMtd + slaP95 carry a <Spark> sparkline. page-overview.jsx passes raw number
        arrays to Stat.spark; the verbatim production form wraps them in the mockup-ui
        <Spark> SVG — a component-logic-layer rewrite of the mockup's latent
        array-as-text bug. The visual layer (the .stat-spark class) is unchanged. */}
      <div style={overviewStyles.kpiRow}>
        <Stat
          label={t("overview.kpi.activeSessions")}
          value="14"
          unit={t("overview.kpi.activeSessionsUnit")}
          delta="+3"
          deltaDir="up"
        />
        <Stat
          label={t("overview.kpi.hitlPending")}
          value="3"
          unit={t("overview.kpi.hitlPendingUnit")}
          delta={t("overview.kpi.hitlPendingDelta")}
          deltaDir="down"
        />
        <Stat
          label={t("overview.kpi.costMtd")}
          value="$2,847"
          delta={t("overview.kpi.costMtdDelta")}
          deltaDir="up"
          spark={<Spark points={COST_MTD_SPARK} />}
        />
        <Stat
          label={t("overview.kpi.slaP95")}
          value="1.84s"
          unit={t("overview.kpi.slaP95Unit")}
          delta={t("overview.kpi.slaP95Delta")}
          deltaDir="up"
          spark={<Spark points={SLA_P95_SPARK} />}
        />
      </div>

      {/* ── row: active loops + HITL (mockup grid2 = 1.4fr 1fr) ── */}
      <div style={overviewStyles.grid2}>
        <ActiveLoopsCard />
        <HITLQueueCard />
      </div>

      {/* ── row: cost burn + providers (mockup grid2eq = 1fr 1fr) ── */}
      {/*
        Card API from mockup-ui.tsx: title / subtitle / actions / foot / children / className / bodyClass
        The mockup page-overview.jsx wraps CostBurnChart/ErrorTrendChart in <Card title subtitle actions>.
        mockup-ui.tsx Card renders card-head (title+subtitle+actions) + card-body.
        No header-action link slot beyond the `actions` ReactNode — that matches the mockup exactly.
      */}
      <div style={overviewStyles.grid2eq}>
        <Card
          title={t("overview.costBurn.title")}
          subtitle={t("overview.costBurn.subtitle")}
          actions={
            <Button
              variant="ghost"
              size="sm"
              iconRight="arrow_right"
              onClick={() => navigate("/cost-dashboard")}
            >
              {t("overview.costBurn.details")}
            </Button>
          }
        >
          <CostBurnChart />
        </Card>
        <ProvidersCard />
      </div>

      {/* ── row: incidents + error trend (mockup grid2eq = 1fr 1fr) ── */}
      <div style={overviewStyles.grid2eq}>
        <IncidentsCard />
        <Card
          title={t("overview.errors.title")}
          subtitle={t("overview.errors.subtitle")}
          actions={
            <Button
              variant="ghost"
              size="sm"
              iconRight="arrow_right"
              onClick={() => navigate("/error-policy")}
            >
              {t("overview.errors.policy")}
            </Button>
          }
        >
          <ErrorTrendChart />
        </Card>
      </div>

      {/* ── quick actions strip (mockup :237-266) ── */}
      <QuickActionsStrip />
    </div>
  );
}

export function OverviewPage(): JSX.Element {
  // R7: no pageTitle prop → AppShellV2 topbar does NOT render a duplicate title.
  // The in-page .page-head is the sole title for /overview, matching the mockup.
  return (
    <RequireAuth>
      <AppShellV2>
        <OverviewPageInner />
      </AppShellV2>
    </RequireAuth>
  );
}

export default OverviewPage;
