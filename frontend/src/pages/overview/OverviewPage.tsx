/**
 * File: frontend/src/pages/overview/OverviewPage.tsx
 * Purpose: Operator dashboard — port from reference/design-mockups/page-overview.jsx.
 * Category: Frontend / pages / overview
 * Scope: Phase 57 / Sprint 57.19 Day 3 / US-C1
 *
 * Description:
 *   1:1 port of mockup OverviewPage (4 KPI row → active-loops + HITL queue
 *   → cost burn + providers traffic-light → recent incidents + error trend
 *   → quick actions strip).
 *
 *   Data sources:
 *   - ACTIVE_LOOPS    → useActiveLoops (US-B1 backend; Cat 1)
 *   - HITL_QUEUE      → fixture this sprint (governance API integration deferred)
 *   - RECENT_INCIDENTS→ fixture this sprint (incidents endpoint not in scope)
 *   - PROVIDERS       → fixture this sprint (telemetry traffic-light deferred)
 *   - COST_BURN chart → inline SVG, demo numbers (cost-dashboard data-load deferred)
 *   - ERROR_24H chart → inline SVG, demo numbers (telemetry data-load deferred)
 *
 *   Mockup-fidelity hard constraint (CLAUDE.md §Frontend Mockup-Fidelity):
 *   visual layout / padding / radius / colour tokens follow page-overview.jsx
 *   exactly. Backend gaps surface as graceful placeholders, NOT layout drift.
 *
 *   Sprint 57.20+ retrofit will swap fixtures for real endpoints
 *   (AD-Overview-Backend-Wire bundle).
 *
 * Created: 2026-05-17 (Sprint 57.19 Day 3 / US-C1)
 *
 * Modification History (newest-first):
 *   - 2026-05-21: Sprint 57.27 Day 2 — extract 5 inline widgets to features/overview/components
 *   - 2026-05-21: Sprint 57.27 Day 1 — extract ActiveLoopsCard + HITLQueueCard to features/overview/components
 *   - 2026-05-17: Sprint 57.20 Day 2 US-C1 — token migration shadcn→mockup tree + shadow-sm on Stat cards
 *   - 2026-05-17: Initial creation (Sprint 57.19 Day 3 / US-C1)
 *
 * Related:
 *   - reference/design-mockups/page-overview.jsx (canonical visual source)
 *   - ../../features/loops/hooks/useActiveLoops.ts (US-B1 consumer)
 *   - frontend/src/components/AppShellV2.tsx (page-level layout shell)
 */

import { ArrowRight, Download, MessageSquare } from "lucide-react";
import type { FC, ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { AppShellV2 } from "@/components/AppShellV2";
import { RequireAuth } from "@/features/auth/components/RequireAuth";
import { ActiveLoopsCard } from "@/features/overview/components/ActiveLoopsCard";
import { CostBurnChart } from "@/features/overview/components/CostBurnChart";
import { ErrorTrendChart } from "@/features/overview/components/ErrorTrendChart";
import { HITLQueueCard } from "@/features/overview/components/HITLQueueCard";
import { IncidentsCard } from "@/features/overview/components/IncidentsCard";
import { ProvidersCard } from "@/features/overview/components/ProvidersCard";
import { QuickActionsStrip } from "@/features/overview/components/QuickActionsStrip";

// ───────────────── primitives (mockup parity inline) ─────────────────

interface CardProps {
  title?: ReactNode;
  subtitle?: ReactNode;
  actions?: ReactNode;
  bodyClassName?: string;
  children: ReactNode;
}

const Card: FC<CardProps> = ({ title, subtitle, actions, bodyClassName, children }) => (
  <div className="rounded-[12px] border border-border bg-bg-1 text-foreground">
    {(title || actions) && (
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <div>
          {title && <div className="text-sm font-semibold">{title}</div>}
          {subtitle && <div className="text-[11px] text-fg-muted">{subtitle}</div>}
        </div>
        {actions}
      </div>
    )}
    <div className={bodyClassName ?? "p-4"}>{children}</div>
  </div>
);

// Badge / RiskBadge / Tone / TONE_CLASS inline primitives removed Sprint 57.27 Day 2:
// IncidentsCard (the sole consumer) is now imported from features/overview/components/.
// _primitives.tsx is the single-source for Badge + RiskBadge in the overview feature.

interface StatProps {
  label: string;
  value: string;
  unit?: string;
  delta?: string;
  deltaDir?: "up" | "down";
}

const Stat: FC<StatProps> = ({ label, value, unit, delta, deltaDir = "up" }) => (
  <div className="rounded-[12px] border border-border bg-bg-1 p-4 shadow-sm">
    <div className="flex items-center justify-between text-[11px] text-fg-muted">
      <span>{label}</span>
      {delta && (
        <span
          className={
            deltaDir === "up" ? "text-success text-[10.5px]" : "text-warning text-[10.5px]"
          }
        >
          {deltaDir === "up" ? "▲" : "▼"} {delta}
        </span>
      )}
    </div>
    <div className="mt-1 font-mono text-[22px] font-semibold tabular-nums">
      {value}
      {unit && <span className="ml-1 text-[11px] font-normal text-fg-muted">{unit}</span>}
    </div>
  </div>
);

// ───────────────── inline fixtures migrated to features/overview/__fixtures__/ (Sprint 57.27 Day 2) ─────────────────
// HITL_QUEUE     → features/overview/__fixtures__/hitlQueue.ts (Sprint 57.27 Day 1)
// RECENT_INCIDENTS → features/overview/__fixtures__/incidents.ts (Sprint 57.27 Day 2)
// PROVIDERS      → features/overview/__fixtures__/providers.ts (Sprint 57.27 Day 2)
// ERROR_24H      → features/overview/__fixtures__/errorTrend.ts (Sprint 57.27 Day 2)
// CostBurnChart  → features/overview/components/CostBurnChart.tsx (Sprint 57.27 Day 2)
// ErrorTrendChart→ features/overview/components/ErrorTrendChart.tsx (Sprint 57.27 Day 2)
// ProvidersCard  → features/overview/components/ProvidersCard.tsx (Sprint 57.27 Day 2)
// IncidentsCard  → features/overview/components/IncidentsCard.tsx (Sprint 57.27 Day 2)
// QuickActionsStrip → features/overview/components/QuickActionsStrip.tsx (Sprint 57.27 Day 2)

// ───────────────── page ─────────────────

function OverviewPageInner(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();

  return (
    <div className="flex flex-col gap-[14px] p-[18px]">
      {/* page head: subtitle + route pill (AppShellV2 already renders pageTitle in header) */}
      <header className="flex items-start justify-between">
        <div className="text-[12.5px] text-fg-muted">
          {t("overview.subtitle")}
          <span className="ml-2 rounded-[4px] bg-bg-2 px-[6px] py-[1px] font-mono text-[11px]">
            /overview
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            className="flex items-center gap-1 rounded-[6px] border border-border bg-bg-1 px-3 py-[6px] text-[12px] hover:bg-bg-hover"
          >
            <Download className="h-3.5 w-3.5" /> {t("overview.export")}
          </button>
          <button
            type="button"
            onClick={() => navigate("/chat-v2")}
            className="flex items-center gap-1 rounded-[6px] bg-primary px-3 py-[6px] text-[12px] text-primary-foreground hover:bg-primary/90"
          >
            <MessageSquare className="h-3.5 w-3.5" /> {t("overview.newChat")}
          </button>
        </div>
      </header>

      {/* KPI row */}
      <div className="grid grid-cols-4 gap-3">
        <Stat label={t("overview.kpi.activeSessions")} value="14" unit="loops" delta="+3" deltaDir="up" />
        <Stat
          label={t("overview.kpi.hitlPending")}
          value="3"
          unit="approvals"
          delta="1 critical"
          deltaDir="down"
        />
        <Stat label={t("overview.kpi.costMtd")} value="$2,847" delta="68% of $4,200" deltaDir="up" />
        <Stat label={t("overview.kpi.slaP95")} value="1.84s" unit="across loops" delta="-0.12s wow" deltaDir="up" />
      </div>

      {/* row: active loops + HITL */}
      <div className="grid grid-cols-[1.4fr_1fr] gap-[14px]">
        <ActiveLoopsCard />
        <HITLQueueCard />
      </div>

      {/* row: cost burn + providers */}
      <div className="grid grid-cols-2 gap-[14px]">
        <Card
          title={t("overview.costBurn.title")}
          subtitle={t("overview.costBurn.subtitle")}
          actions={
            <button
              type="button"
              onClick={() => navigate("/cost-dashboard")}
              className="flex items-center gap-1 text-[11px] text-fg-muted hover:text-foreground"
            >
              {t("overview.costBurn.details")} <ArrowRight className="h-3 w-3" />
            </button>
          }
        >
          <CostBurnChart />
        </Card>
        <ProvidersCard />
      </div>

      {/* row: incidents + error trend */}
      <div className="grid grid-cols-2 gap-[14px]">
        <IncidentsCard />
        <Card
          title={t("overview.errors.title")}
          subtitle={t("overview.errors.subtitle")}
          actions={
            <button
              type="button"
              onClick={() => navigate("/error-policy")}
              className="flex items-center gap-1 text-[11px] text-fg-muted hover:text-foreground"
            >
              {t("overview.errors.policy")} <ArrowRight className="h-3 w-3" />
            </button>
          }
        >
          <ErrorTrendChart />
        </Card>
      </div>

      {/* quick actions strip */}
      <QuickActionsStrip />
    </div>
  );
}

export function OverviewPage(): JSX.Element {
  const { t } = useTranslation();
  return (
    <RequireAuth>
      <AppShellV2 pageTitle={t("overview.title")}>
        <OverviewPageInner />
      </AppShellV2>
    </RequireAuth>
  );
}

export default OverviewPage;
