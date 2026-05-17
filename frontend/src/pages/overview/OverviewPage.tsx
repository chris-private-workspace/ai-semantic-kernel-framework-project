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
 *   - 2026-05-17: Sprint 57.20 Day 2 US-C1 — token migration shadcn→mockup tree (bg-card→bg-bg-1; text-muted-foreground→text-fg-muted; hover:bg-muted/40→hover:bg-bg-hover) + shadow-sm on Stat cards for mockup parity
 *   - 2026-05-17: Initial creation (Sprint 57.19 Day 3 / US-C1)
 *
 * Related:
 *   - reference/design-mockups/page-overview.jsx (canonical visual source)
 *   - ../../features/loops/hooks/useActiveLoops.ts (US-B1 consumer)
 *   - frontend/src/components/AppShellV2.tsx (page-level layout shell)
 */

import { ArrowRight, CheckCheck, Download, MessageSquare, Shield, Users } from "lucide-react";
import type { FC, ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { AppShellV2 } from "@/components/AppShellV2";
import { RequireAuth } from "@/features/auth/components/RequireAuth";
import { useActiveLoops } from "@/features/loops/hooks/useActiveLoops";
import type { Loop } from "@/features/loops/types";

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

type Tone = "success" | "warning" | "danger" | "thinking" | "info" | "primary" | "muted";

const TONE_CLASS: Record<Tone, string> = {
  success: "bg-success/16 text-success",
  warning: "bg-warning/16 text-warning",
  danger: "bg-danger/16 text-danger",
  thinking: "bg-thinking/16 text-thinking",
  info: "bg-info/16 text-info",
  primary: "bg-primary/16 text-primary",
  muted: "bg-bg-2 text-fg-muted",
};

const Badge: FC<{ tone?: Tone; dot?: boolean; children: ReactNode }> = ({
  tone = "muted",
  dot,
  children,
}) => (
  <span
    className={`inline-flex items-center gap-1 rounded-full px-2 py-[2px] text-[10.5px] font-medium uppercase tracking-wide ${TONE_CLASS[tone]}`}
  >
    {dot && <span className="h-1.5 w-1.5 rounded-full bg-current" />}
    {children}
  </span>
);

const RISK_TONE: Record<string, Tone> = {
  low: "success",
  medium: "info",
  high: "warning",
  critical: "danger",
};

const RiskBadge: FC<{ level: string }> = ({ level }) => (
  <Badge tone={RISK_TONE[level] ?? "muted"}>{level}</Badge>
);

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

// ───────────────── inline fixtures (Sprint 57.20+ swap to real APIs) ─────────────────

const HITL_QUEUE = [
  {
    id: "appr_91",
    title: "salesforce_update — refund $4,820",
    risk: "high",
    requester: "sess_7c11d",
    sla: "3h 12m",
  },
  {
    id: "appr_92",
    title: "email_send — refund confirmation to 14 customers",
    risk: "medium",
    requester: "sess_7c11d",
    sla: "3h 14m",
  },
  {
    id: "appr_88",
    title: "servicenow_create_ticket — P1 incident escalation",
    risk: "critical",
    requester: "sess_4f88c",
    sla: "23m",
  },
];

const RECENT_INCIDENTS = [
  { id: "INC-2451", title: "p95 latency breach · gpt-4.1 provider", sev: "high", status: "open", since: "12m" },
  { id: "INC-2447", title: "redaction rule false-positive · acme-prod", sev: "low", status: "investigating", since: "1h" },
  { id: "INC-2440", title: "subagent budget exceeded x4 · globex-eu", sev: "medium", status: "open", since: "2h" },
  { id: "INC-2438", title: "kb_search vector index rebuild", sev: "low", status: "resolved", since: "3h" },
];

const PROVIDERS: Array<{ name: string; state: "green" | "amber" | "red"; p95: number; calls: string }> = [
  { name: "claude-haiku-4-5", state: "green", p95: 1.8, calls: "12.4k" },
  { name: "gpt-4.1", state: "amber", p95: 3.2, calls: "8.1k" },
  { name: "gpt-4.1-mini", state: "green", p95: 1.1, calls: "4.7k" },
  { name: "embedding-3-large", state: "green", p95: 0.4, calls: "21.0k" },
];

const ERROR_24H = [3, 2, 4, 1, 0, 2, 1, 0, 0, 1, 3, 5, 8, 12, 9, 6, 4, 3, 5, 7, 4, 2, 1, 2];

// ───────────────── inline SVG charts (mockup port) ─────────────────

const CostBurnChart: FC = () => {
  const days = 30;
  const today = 18;
  const dailyBudget = 4200 / days;
  const spent = Array.from({ length: today }, (_, i) =>
    dailyBudget * (0.6 + (i / today) * 0.9 + Math.sin(i * 0.7) * 0.15),
  );
  const cumulative = spent.reduce<number[]>(
    (acc, v, i) => [...acc, (acc[i - 1] ?? 0) + v],
    [],
  );
  const W = 360;
  const H = 130;
  const padding = { l: 30, r: 8, t: 8, b: 22 };
  const innerW = W - padding.l - padding.r;
  const innerH = H - padding.t - padding.b;
  const maxY = 4200;
  const xAt = (i: number) => padding.l + (i / (days - 1)) * innerW;
  const yAt = (v: number) => padding.t + innerH - (v / maxY) * innerH;
  const budgetLine = `M ${xAt(0)} ${yAt(0)} L ${xAt(days - 1)} ${yAt(4200)}`;
  const burnPath = cumulative
    .map((v, i) => `${i === 0 ? "M" : "L"} ${xAt(i)} ${yAt(v)}`)
    .join(" ");
  const burnArea = `${burnPath} L ${xAt(today - 1)} ${yAt(0)} L ${xAt(0)} ${yAt(0)} Z`;
  const mtd = cumulative[today - 1] ?? 0;
  const onPace = dailyBudget * today;
  return (
    <div className="flex flex-col gap-2">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" height={H}>
        <defs>
          <linearGradient id="overview-burn-grad" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="hsl(var(--primary) / 0.32)" />
            <stop offset="100%" stopColor="hsl(var(--primary) / 0)" />
          </linearGradient>
        </defs>
        {[0, 1050, 2100, 3150, 4200].map((v) => (
          <g key={v}>
            <line
              x1={padding.l}
              x2={W - padding.r}
              y1={yAt(v)}
              y2={yAt(v)}
              stroke="hsl(var(--border))"
              strokeDasharray="2 2"
            />
            <text
              x={padding.l - 4}
              y={yAt(v) + 3}
              textAnchor="end"
              fontSize={9} fill="hsl(var(--fg-subtle))"
            >
              ${v}
            </text>
          </g>
        ))}
        <path d={budgetLine} stroke="hsl(var(--fg-subtle))" strokeDasharray="4 3" strokeWidth="1" fill="none" />
        <path d={burnArea} fill="url(#overview-burn-grad)" />
        <path d={burnPath} stroke="hsl(var(--primary))" strokeWidth="1.5" fill="none" />
        <circle cx={xAt(today - 1)} cy={yAt(mtd)} r="3" fill="hsl(var(--primary))" />
      </svg>
      <div className="flex items-center gap-3 text-[11px] text-fg-muted">
        <span>
          <span className="font-mono text-primary">${mtd.toFixed(0)}</span> MTD
        </span>
        <span className="flex-1" />
        <span>
          <span className="font-mono">${onPace.toFixed(0)}</span> on-pace
        </span>
        <span className={mtd > onPace ? "text-warning" : "text-success"}>
          {mtd > onPace ? "over pace" : "under pace"}
        </span>
      </div>
    </div>
  );
};

const ErrorTrendChart: FC = () => {
  const W = 360;
  const H = 130;
  const padding = { l: 30, r: 8, t: 8, b: 22 };
  const innerW = W - padding.l - padding.r;
  const innerH = H - padding.t - padding.b;
  const maxY = Math.max(...ERROR_24H, 10);
  const xAt = (i: number) => padding.l + (i / (ERROR_24H.length - 1)) * innerW;
  const yAt = (v: number) => padding.t + innerH - (v / maxY) * innerH;
  const bw = (innerW / ERROR_24H.length) * 0.7;
  const total = ERROR_24H.reduce((a, b) => a + b, 0);
  const peak = Math.max(...ERROR_24H);
  const last3 = ERROR_24H.slice(-3).reduce((a, b) => a + b, 0);
  return (
    <div className="flex flex-col gap-2">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" height={H}>
        {[0, 4, 8, 12].map((v) => (
          <g key={v}>
            <line
              x1={padding.l}
              x2={W - padding.r}
              y1={yAt(v)}
              y2={yAt(v)}
              stroke="hsl(var(--border))"
              strokeDasharray="2 2"
            />
            <text
              x={padding.l - 4}
              y={yAt(v) + 3}
              textAnchor="end"
              fontSize={9} fill="hsl(var(--fg-subtle))"
            >
              {v}
            </text>
          </g>
        ))}
        {ERROR_24H.map((v, i) => {
          const tone =
            v >= 10 ? "hsl(var(--danger))" : v >= 6 ? "hsl(var(--warning))" : "hsl(var(--info))";
          return (
            <rect
              key={i}
              x={xAt(i) - bw / 2}
              y={yAt(v)}
              width={bw}
              height={innerH - (yAt(v) - padding.t)}
              fill={tone}
              fillOpacity={0.85}
              rx={1}
            />
          );
        })}
      </svg>
      <div className="flex items-center gap-3 text-[11px] text-fg-muted">
        <span>
          <span className="font-mono text-danger">{total}</span> errors · 24h
        </span>
        <span className="flex-1" />
        <span>
          <span className="font-mono">{peak}</span> peak / hour
        </span>
        <span className={last3 > 10 ? "text-warning" : "text-success"}>
          {last3 > 10 ? "rising" : "stable"}
        </span>
      </div>
    </div>
  );
};

// ───────────────── widgets ─────────────────

const STATUS_TONE: Record<string, Tone> = {
  running: "success",
  "hitl-paused": "warning",
  verifying: "thinking",
  error: "danger",
  ended: "muted",
};

const ActiveLoopsCard: FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { data, isLoading, error } = useActiveLoops(10);
  const items: Loop[] = data?.items ?? [];

  return (
    <Card
      title={t("overview.activeLoops.title")}
      subtitle={
        isLoading
          ? t("action.loading")
          : `${items.length} ${t("overview.activeLoops.subtitle")}`
      }
      actions={
        <button
          type="button"
          onClick={() => navigate("/loop-debug")}
          className="flex items-center gap-1 text-[11px] text-fg-muted hover:text-foreground"
        >
          {t("overview.activeLoops.openDebug")} <ArrowRight className="h-3 w-3" />
        </button>
      }
      bodyClassName=""
    >
      {error && (
        <div className="px-4 py-6 text-center text-[12px] text-danger" role="alert">
          {error.message}
        </div>
      )}
      {!error && !isLoading && items.length === 0 && (
        <div className="px-4 py-6 text-center text-[12px] text-fg-muted">
          {t("overview.activeLoops.empty")}
        </div>
      )}
      {!error && items.length > 0 && (
        <div>
          {items.map((loop) => {
            const maxTurns = 50; // backend gap — see AD-Loop-Session-Enrich-Phase58
            const pct = Math.min(100, (loop.turn_count / maxTurns) * 100);
            const tone = STATUS_TONE[loop.status] ?? "muted";
            return (
              <button
                key={loop.session_id}
                type="button"
                onClick={() => navigate("/loop-debug")}
                className="grid w-full cursor-pointer grid-cols-[auto_1fr_auto_auto_auto] items-center gap-[10px] border-b border-border px-[10px] py-2 text-left text-[12.5px] last:border-0 hover:bg-bg-hover"
              >
                <Badge tone={tone} dot>
                  {loop.status}
                </Badge>
                <div className="flex min-w-0 flex-col gap-[2px]">
                  <span className="font-mono text-[11.5px]">
                    {loop.session_id.slice(0, 8)}…
                  </span>
                  <span className="font-mono text-[10.5px] text-fg-muted">
                    {loop.token_usage.toLocaleString()} tok · ${loop.total_cost_usd}
                  </span>
                </div>
                <div className="flex w-20 flex-col gap-[3px]">
                  <span className="font-mono text-[10.5px] text-fg-muted">
                    turn {loop.turn_count}/{maxTurns}
                  </span>
                  <div className="relative h-[6px] overflow-hidden rounded-[3px] bg-bg-2">
                    <div
                      className={`absolute inset-0 origin-left ${pct > 80 ? "bg-warning" : "bg-primary"}`}
                      // eslint-disable-next-line no-restricted-syntax -- dynamic per-row progress fill per mockup parity (STYLE.md §1 escape hatch)
                      style={{ transform: `scaleX(${pct / 100})` }}
                    />
                  </div>
                </div>
                <span className="w-[60px] text-right font-mono text-[11px] text-fg-muted">
                  {loop.turn_count}t
                </span>
                <span className="w-[40px] text-right font-mono text-[11px] text-fg-muted">
                  {new Date(loop.started_at_ms).toLocaleTimeString("en-US", { hour12: false }).slice(0, 5)}
                </span>
              </button>
            );
          })}
        </div>
      )}
    </Card>
  );
};

const HITLQueueCard: FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  return (
    <Card
      title={t("overview.hitlQueue.title")}
      subtitle={`${HITL_QUEUE.length} pending`}
      actions={
        <button
          type="button"
          onClick={() => navigate("/governance")}
          className="flex items-center gap-1 text-[11px] text-fg-muted hover:text-foreground"
        >
          {t("overview.hitlQueue.review")} <ArrowRight className="h-3 w-3" />
        </button>
      }
    >
      <div className="flex flex-col gap-[10px]">
        {HITL_QUEUE.map((req) => (
          <button
            key={req.id}
            type="button"
            onClick={() => navigate("/governance")}
            className={`flex flex-col gap-[6px] rounded-[8px] border p-[10px] text-left ${
              req.risk === "critical"
                ? "border-danger/40 bg-danger/8"
                : "border-border bg-bg-2"
            }`}
          >
            <div className="flex items-center justify-between gap-[6px]">
              <RiskBadge level={req.risk} />
              <span className="font-mono text-[10.5px] text-fg-muted">
                SLA · {req.sla}
              </span>
            </div>
            <div className="text-[12.5px] font-medium leading-[1.4]">{req.title}</div>
            <div className="font-mono text-[10.5px] text-fg-muted">
              {req.id} · from {req.requester}
            </div>
          </button>
        ))}
      </div>
    </Card>
  );
};

const ProvidersCard: FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  return (
    <Card
      title={t("overview.providers.title")}
      subtitle={`${PROVIDERS.length} providers · 24h`}
      actions={
        <button
          type="button"
          onClick={() => navigate("/sla-dashboard")}
          className="flex items-center gap-1 text-[11px] text-fg-muted hover:text-foreground"
        >
          {t("overview.providers.details")} <ArrowRight className="h-3 w-3" />
        </button>
      }
    >
      <div className="flex flex-col">
        {PROVIDERS.map((p, i) => (
          <div
            key={p.name}
            className={`flex items-center gap-[10px] px-1 py-[10px] ${i < PROVIDERS.length - 1 ? "border-b border-border" : ""}`}
          >
            <span
              className={`h-2 w-2 rounded-full ${
                p.state === "green" ? "bg-success" : p.state === "amber" ? "bg-warning" : "bg-danger"
              }`}
              // eslint-disable-next-line no-restricted-syntax -- per-state coloured ring per mockup parity (STYLE.md §1 escape hatch)
              style={{
                boxShadow:
                  p.state === "green"
                    ? "0 0 0 3px hsl(var(--success) / 0.18)"
                    : p.state === "amber"
                      ? "0 0 0 3px hsl(var(--warning) / 0.18)"
                      : "0 0 0 3px hsl(var(--danger) / 0.18)",
              }}
            />
            <span className="flex-1 font-mono text-[12px]">{p.name}</span>
            <span className="font-mono text-[11px] text-fg-muted">p95 {p.p95}s</span>
            <span className="w-[60px] text-right font-mono text-[11px] text-fg-muted">
              {p.calls}
            </span>
          </div>
        ))}
      </div>
    </Card>
  );
};

const IncidentsCard: FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const openCount = RECENT_INCIDENTS.filter((i) => i.status !== "resolved").length;
  return (
    <Card
      title={t("overview.incidents.title")}
      subtitle={`${openCount} open`}
      actions={
        <button
          type="button"
          onClick={() => navigate("/incidents")}
          className="flex items-center gap-1 text-[11px] text-fg-muted hover:text-foreground"
        >
          {t("overview.incidents.all")} <ArrowRight className="h-3 w-3" />
        </button>
      }
      bodyClassName=""
    >
      <div>
        {RECENT_INCIDENTS.map((inc, i) => (
          <button
            key={inc.id}
            type="button"
            onClick={() => navigate("/incidents")}
            className={`flex w-full cursor-pointer items-center gap-[10px] px-[14px] py-[10px] text-left text-[12.5px] hover:bg-bg-hover ${i < RECENT_INCIDENTS.length - 1 ? "border-b border-border" : ""}`}
          >
            <RiskBadge level={inc.sev} />
            <span className="w-[64px] font-mono text-[11.5px]">{inc.id}</span>
            <span className="flex-1">{inc.title}</span>
            <Badge
              tone={
                inc.status === "resolved"
                  ? "success"
                  : inc.status === "open"
                    ? "warning"
                    : "muted"
              }
            >
              {inc.status}
            </Badge>
            <span className="w-[40px] text-right font-mono text-[11px] text-fg-muted">
              {inc.since}
            </span>
          </button>
        ))}
      </div>
    </Card>
  );
};

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
      <div className="flex gap-3">
        <button
          type="button"
          onClick={() => navigate("/chat-v2")}
          className="flex flex-1 flex-col items-start gap-[6px] rounded-[8px] border border-border bg-bg-1 p-3 text-left hover:bg-bg-hover"
        >
          <span className="flex items-center gap-[6px]">
            <MessageSquare className="h-3.5 w-3.5 text-primary" />
            <span className="text-[12.5px] font-medium">{t("overview.quick.newChat")}</span>
          </span>
          <span className="text-[11px] text-fg-muted">{t("overview.quick.newChatSub")}</span>
        </button>
        <button
          type="button"
          onClick={() => navigate("/governance")}
          className="flex flex-1 flex-col items-start gap-[6px] rounded-[8px] border border-border bg-bg-1 p-3 text-left hover:bg-bg-hover"
        >
          <span className="flex items-center gap-[6px]">
            <Shield className="h-3.5 w-3.5 text-warning" />
            <span className="text-[12.5px] font-medium">{t("overview.quick.review")}</span>
          </span>
          <span className="text-[11px] text-fg-muted">{t("overview.quick.reviewSub")}</span>
        </button>
        <button
          type="button"
          onClick={() => navigate("/admin/tenants")}
          className="flex flex-1 flex-col items-start gap-[6px] rounded-[8px] border border-border bg-bg-1 p-3 text-left hover:bg-bg-hover"
        >
          <span className="flex items-center gap-[6px]">
            <Users className="h-3.5 w-3.5 text-info" />
            <span className="text-[12.5px] font-medium">{t("overview.quick.tenants")}</span>
          </span>
          <span className="text-[11px] text-fg-muted">{t("overview.quick.tenantsSub")}</span>
        </button>
        <button
          type="button"
          onClick={() => navigate("/verification")}
          className="flex flex-1 flex-col items-start gap-[6px] rounded-[8px] border border-border bg-bg-1 p-3 text-left hover:bg-bg-hover"
        >
          <span className="flex items-center gap-[6px]">
            <CheckCheck className="h-3.5 w-3.5 text-success" />
            <span className="text-[12.5px] font-medium">{t("overview.quick.verification")}</span>
          </span>
          <span className="text-[11px] text-fg-muted">
            {t("overview.quick.verificationSub")}
          </span>
        </button>
      </div>
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
