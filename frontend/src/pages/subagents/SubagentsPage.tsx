/**
 * File: frontend/src/pages/subagents/SubagentsPage.tsx
 * Purpose: Subagent Registry — port from reference/design-mockups/page-agents.jsx SubagentsRegistry + SubagentDetail.
 * Category: Frontend / pages / subagents
 * Scope: Phase 57 / Sprint 57.19 Day 4 / US-C3
 *
 * Description:
 *   1:1 port of mockup `SubagentsRegistry` + `SubagentDetail`:
 *     - 4-mode KPI cards (fork=thinking / as_tool=tool / teammate=memory / handoff=info)
 *     - 2-column grid (1.4fr list table + 1fr detail card with inner Tabs spec/budget/tools/stats)
 *
 *   NOT a drawer (checklist plan mentioned shadcn `<Sheet>` but mockup uses inline
 *   right-side card layout — mockup-fidelity hard constraint wins). Click row in
 *   list table → updates `selected` state → right-side card re-renders.
 *
 *   Backend US-B4 stub returns empty + `not_implemented_reason` (AD-Subagent-
 *   RealList-Phase58). When `items.length === 0` AND `not_implemented_reason` set,
 *   render carryover banner above the table; table falls back to mockup fixture
 *   (8 rows) for visual fidelity reference so design review can proceed.
 *
 * Created: 2026-05-17 (Sprint 57.19 Day 4 / US-C3)
 * Last Modified: 2026-05-24
 *
 * Modification History (newest-first):
 *   - 2026-05-24: Sprint 57.33 Day 1 US-B1 — defensive ?. on items.length (crash fix; AD-Overview-PreExisting-Route-Crashes)
 *   - 2026-05-17: Initial creation (Sprint 57.19 Day 4 / US-C3)
 *
 * Related:
 *   - reference/design-mockups/page-agents.jsx (SubagentsRegistry + SubagentDetail)
 *   - frontend/src/features/subagents/hooks/useSubagents.ts (US-B4 consumer)
 *   - frontend/src/components/ui/tabs.tsx (Sprint 57.19 NEW primitive)
 */

import { GitBranch, Play, Plus } from "lucide-react";
import type { FC, ReactNode } from "react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { AppShellV2 } from "@/components/AppShellV2";
import { Tabs } from "@/components/ui/tabs";
import { RequireAuth } from "@/features/auth/components/RequireAuth";
import { useSubagents } from "@/features/subagents/hooks/useSubagents";
import type { SubagentMode } from "@/features/subagents/types";

// ───────────────── primitives (mockup parity inline) ─────────────────

type Tone = "success" | "warning" | "danger" | "thinking" | "info" | "primary" | "tool" | "memory" | "muted";

const TONE_CLASS: Record<Tone, string> = {
  success: "bg-success/16 text-success",
  warning: "bg-warning/16 text-warning",
  danger: "bg-danger/16 text-danger",
  thinking: "bg-thinking/16 text-thinking",
  info: "bg-info/16 text-info",
  primary: "bg-primary/16 text-primary",
  tool: "bg-tool/16 text-tool",
  memory: "bg-memory/16 text-memory",
  muted: "bg-muted text-muted-foreground",
};

const Badge: FC<{ tone?: Tone; dot?: boolean; children: ReactNode }> = ({
  tone = "muted",
  dot,
  children,
}) => (
  <span
    className={`inline-flex items-center gap-1 rounded-full px-2 py-[2px] text-[10.5px] font-medium ${TONE_CLASS[tone]}`}
  >
    {dot && <span className="h-1.5 w-1.5 rounded-full bg-current" />}
    {children}
  </span>
);

const MODE_TONE: Record<SubagentMode, Tone> = {
  fork: "thinking",
  as_tool: "tool",
  teammate: "memory",
  handoff: "info",
};

const MODE_BORDER: Record<SubagentMode, string> = {
  fork: "border-l-thinking",
  as_tool: "border-l-tool",
  teammate: "border-l-memory",
  handoff: "border-l-info",
};

// ───────────────── fixtures (Sprint 57.20+ replaced by real backend) ─────────────────

interface SubagentFixture {
  id: string;
  role: string;
  prompt: string;
  model: string;
  modes: SubagentMode[];
  status: "live" | "staging";
  calls24: number;
  p95: number;
}

const SUBAGENT_LIST: SubagentFixture[] = [
  { id: "log-scanner", role: "log-scanner", prompt: "Tail and grep logs from a service. Return matched lines.", model: "claude-haiku-4-5", modes: ["fork", "as_tool"], status: "live", calls24: 412, p95: 2.2 },
  { id: "dep-checker", role: "dep-checker", prompt: "Check health of downstream dependencies via health-probe.", model: "claude-haiku-4-5", modes: ["fork", "as_tool"], status: "live", calls24: 188, p95: 1.86 },
  { id: "metrics-pull", role: "metrics-pull", prompt: "Pull time-series metrics from observability backend.", model: "claude-haiku-4-5", modes: ["fork", "as_tool"], status: "live", calls24: 540, p95: 0.32 },
  { id: "evidence-collector", role: "evidence-collector", prompt: "Assemble RCA evidence bundle from metrics + logs + memory.", model: "claude-sonnet-4-5", modes: ["as_tool"], status: "live", calls24: 28, p95: 4.4 },
  { id: "compliance-auditor", role: "compliance-auditor", prompt: "Answer compliance + audit queries with citations from KB.", model: "claude-opus-4-1", modes: ["handoff", "teammate"], status: "live", calls24: 18, p95: 8.2 },
  { id: "postmortem-writer", role: "postmortem-writer", prompt: "Draft postmortem doc following 5-whys + timeline template.", model: "claude-sonnet-4-5", modes: ["handoff"], status: "staging", calls24: 2, p95: 12.0 },
  { id: "anomaly-detector", role: "anomaly-detector", prompt: "Detect statistical anomalies in metric streams.", model: "claude-haiku-4-5", modes: ["as_tool"], status: "live", calls24: 84, p95: 0.41 },
  { id: "summarizer", role: "summarizer", prompt: "Compact reduce ≤500-token summary of an artifact.", model: "claude-haiku-4-5", modes: ["as_tool"], status: "live", calls24: 612, p95: 0.55 },
];

const MODE_KPI: Array<{ mode: SubagentMode; count: number; descKey: string }> = [
  { mode: "fork", count: 3, descKey: "subagents.mode.forkDesc" },
  { mode: "as_tool", count: 6, descKey: "subagents.mode.asToolDesc" },
  { mode: "teammate", count: 1, descKey: "subagents.mode.teammateDesc" },
  { mode: "handoff", count: 2, descKey: "subagents.mode.handoffDesc" },
];

// ───────────────── detail card (inner tabs) ─────────────────

const SubagentDetailCard: FC<{ sub: SubagentFixture }> = ({ sub }) => {
  const { t } = useTranslation();
  const [tab, setTab] = useState<"spec" | "budget" | "tools" | "stats">("spec");
  const tabItems = [
    { id: "spec", label: t("subagents.detail.spec") },
    { id: "budget", label: t("subagents.detail.budget") },
    { id: "tools", label: t("subagents.detail.tools") },
    { id: "stats", label: t("subagents.detail.stats") },
  ];

  return (
    <div className="rounded-[12px] border border-border bg-card text-card-foreground">
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <div>
          <div className="font-mono text-sm font-semibold">{sub.role}</div>
          <div className="text-[11px] text-muted-foreground">AgentSpec · {sub.modes.join(" + ")}</div>
        </div>
        <button
          type="button"
          className="inline-flex items-center gap-1 rounded-[6px] px-2 py-1 text-[11px] text-muted-foreground hover:text-foreground"
        >
          <Play className="h-3 w-3" /> {t("subagents.detail.testInvoke")}
        </button>
      </div>
      <div className="px-4 pt-2">
        <Tabs
          items={tabItems}
          value={tab}
          onChange={(id) => setTab(id as typeof tab)}
          ariaLabel={t("subagents.detail.tabsLabel")}
        />
      </div>
      <div className="p-4">
        {tab === "spec" && (
          <div className="flex flex-col gap-3 text-[12px]">
            <div className="flex flex-col gap-1">
              <span className="text-[11px] uppercase tracking-wide text-muted-foreground">{t("subagents.detail.role")}</span>
              <input className="w-full rounded-[6px] border border-border bg-muted/30 px-2 py-1 font-mono" readOnly defaultValue={sub.role} />
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-[11px] uppercase tracking-wide text-muted-foreground">{t("subagents.detail.model")}</span>
              <input className="w-full rounded-[6px] border border-border bg-muted/30 px-2 py-1 font-mono" readOnly defaultValue={sub.model} />
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-[11px] uppercase tracking-wide text-muted-foreground">{t("subagents.detail.systemPrompt")}</span>
              <textarea
                rows={4}
                readOnly
                defaultValue={sub.prompt}
                className="w-full resize-none rounded-[6px] border border-border bg-muted/30 px-2 py-1 font-mono text-[11.5px]"
              />
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-[11px] uppercase tracking-wide text-muted-foreground">{t("subagents.detail.allowedModes")}</span>
              <div className="flex flex-wrap items-center gap-1.5">
                {(["fork", "as_tool", "teammate", "handoff"] as SubagentMode[]).map((m) => (
                  <Badge key={m} tone={sub.modes.includes(m) ? MODE_TONE[m] : "muted"}>
                    {m}
                  </Badge>
                ))}
              </div>
            </div>
          </div>
        )}
        {tab === "budget" && (
          <div className="flex flex-col gap-3 text-[12px]">
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">{t("subagents.detail.maxTokens")}</span>
              <span className="font-mono">10,000</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">{t("subagents.detail.maxDuration")}</span>
              <span className="font-mono">300 s</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">{t("subagents.detail.maxConcurrent")}</span>
              <span className="font-mono">5</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">{t("subagents.detail.maxDepth")}</span>
              <span className="font-mono">3</span>
            </div>
            <div className="rounded-[6px] border border-border bg-muted/30 p-2 text-[11.5px] text-muted-foreground">
              {t("subagents.detail.worktreeAbsent")}
            </div>
          </div>
        )}
        {tab === "tools" && (
          <div className="flex flex-col gap-2">
            <span className="text-[11px] uppercase tracking-wide text-muted-foreground">
              {t("subagents.detail.toolsAttached")}
            </span>
            <div className="flex flex-wrap items-center gap-1.5">
              <Badge tone="tool">log.tail</Badge>
              <Badge tone="tool">log.grep</Badge>
              <Badge tone="tool">metrics.query</Badge>
            </div>
            <button
              type="button"
              className="mt-1 inline-flex w-fit items-center gap-1 rounded-[6px] border border-border px-2 py-1 text-[11px] hover:bg-muted/40"
            >
              <Plus className="h-3 w-3" /> {t("subagents.detail.attachTool")}
            </button>
          </div>
        )}
        {tab === "stats" && (
          <div className="flex flex-col gap-2 text-[12px]">
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">{t("subagents.detail.calls24h")}</span>
              <span className="font-mono">{sub.calls24}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">{t("subagents.detail.p95")}</span>
              <span className="font-mono">{sub.p95}s</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">{t("subagents.detail.successRate")}</span>
              <span className="font-mono">99.2%</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">{t("subagents.detail.avgTokens")}</span>
              <span className="font-mono">2,840</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">{t("subagents.detail.topOrchestrator")}</span>
              <span className="font-mono">orchestrator-main</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// ───────────────── page ─────────────────

function SubagentsPageInner(): JSX.Element {
  const { t } = useTranslation();
  const [selectedId, setSelectedId] = useState<string>("compliance-auditor");
  const { data, isLoading, error } = useSubagents({ limit: 50 });

  const active = SUBAGENT_LIST.find((s) => s.id === selectedId) ?? SUBAGENT_LIST[0];
  const notImplementedReason = data?.not_implemented_reason ?? null;
  // FIX-Sprint-57-33 US-B1 (2026-05-24): defensive ?. on items — backend stub may return
  // {not_implemented_reason: "..."} without an items field; previously crashed the page tree
  // with "Cannot read properties of undefined (reading 'length')" (AD-Overview-PreExisting-Route-Crashes).
  const realItemsCount = data?.items?.length ?? 0;

  return (
    <div className="flex flex-col gap-[14px] p-[18px]">
      {/* page head */}
      <header className="flex items-start justify-between">
        <div className="text-[12.5px] text-muted-foreground">
          {t("subagents.subtitle")}
          <span className="ml-2 rounded-[4px] bg-muted px-[6px] py-[1px] font-mono text-[11px]">
            /subagents
          </span>
          <span className="ml-2 font-mono text-[11px] text-muted-foreground">
            · {SUBAGENT_LIST.length} {t("subagents.registered")}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            className="inline-flex items-center gap-1 rounded-[6px] border border-border bg-card px-3 py-[6px] text-[12px] hover:bg-muted/40"
          >
            <GitBranch className="h-3.5 w-3.5" /> {t("subagents.syncFromRepo")}
          </button>
          <button
            type="button"
            className="inline-flex items-center gap-1 rounded-[6px] bg-primary px-3 py-[6px] text-[12px] text-primary-foreground hover:bg-primary/90"
          >
            <Plus className="h-3.5 w-3.5" /> {t("subagents.newSubagent")}
          </button>
        </div>
      </header>

      {/* carryover banner (US-B4 stub) */}
      {!isLoading && !error && notImplementedReason && realItemsCount === 0 && (
        <div
          role="status"
          className="rounded-[8px] border border-warning/40 bg-warning/8 p-3 text-[12px] text-warning"
        >
          <strong>{t("subagents.carryoverHeading")}</strong>: {notImplementedReason}
        </div>
      )}
      {error && (
        <div role="alert" className="rounded-[8px] border border-danger/40 bg-danger/8 p-3 text-[12px] text-danger">
          {error.message}
        </div>
      )}

      {/* 4-mode KPI row */}
      <div className="grid grid-cols-4 gap-3">
        {MODE_KPI.map((m) => (
          <div
            key={m.mode}
            className={`rounded-[12px] border border-border bg-card p-4 border-l-[3px] ${MODE_BORDER[m.mode]}`}
          >
            <div className="font-mono text-[11px] font-semibold uppercase tracking-wide text-foreground">
              {m.mode}
            </div>
            <div className="mt-1 font-mono text-[22px] font-semibold tabular-nums">{m.count}</div>
            <div className="text-[10.5px] text-muted-foreground">{t(m.descKey)}</div>
          </div>
        ))}
      </div>

      {/* 2-col grid: list left, detail right */}
      <div className="grid grid-cols-[1.4fr_1fr] gap-[14px]">
        <div className="rounded-[12px] border border-border bg-card">
          <div className="border-b border-border px-4 py-3">
            <div className="text-sm font-semibold">{t("subagents.list.title")}</div>
            <div className="text-[11px] text-muted-foreground">{t("subagents.list.subtitle")}</div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-[12px]">
              <thead className="text-left text-[11px] uppercase tracking-wide text-muted-foreground">
                <tr>
                  <th className="border-b border-border px-3 py-2">{t("subagents.col.role")}</th>
                  <th className="border-b border-border px-3 py-2">{t("subagents.col.model")}</th>
                  <th className="border-b border-border px-3 py-2">{t("subagents.col.modes")}</th>
                  <th className="border-b border-border px-3 py-2">{t("subagents.col.status")}</th>
                  <th className="border-b border-border px-3 py-2 text-right">{t("subagents.col.calls24h")}</th>
                  <th className="border-b border-border px-3 py-2 text-right">{t("subagents.col.p95")}</th>
                </tr>
              </thead>
              <tbody>
                {SUBAGENT_LIST.map((s) => {
                  const isSel = s.id === selectedId;
                  return (
                    <tr
                      key={s.id}
                      onClick={() => setSelectedId(s.id)}
                      className={`cursor-pointer border-b border-border last:border-0 ${isSel ? "bg-primary/10" : "hover:bg-muted/40"}`}
                    >
                      <td className="px-3 py-2 font-mono font-medium">{s.role}</td>
                      <td className="px-3 py-2 font-mono text-[11.5px] text-muted-foreground">{s.model}</td>
                      <td className="px-3 py-2">
                        <div className="flex flex-wrap items-center gap-1">
                          {s.modes.map((m) => (
                            <Badge key={m} tone={MODE_TONE[m]}>
                              {m}
                            </Badge>
                          ))}
                        </div>
                      </td>
                      <td className="px-3 py-2">
                        <Badge tone={s.status === "live" ? "success" : "warning"} dot>
                          {s.status}
                        </Badge>
                      </td>
                      <td className="px-3 py-2 text-right font-mono tabular-nums">{s.calls24}</td>
                      <td className="px-3 py-2 text-right font-mono tabular-nums text-muted-foreground">
                        {s.p95}s
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        <SubagentDetailCard sub={active} />
      </div>
    </div>
  );
}

export function SubagentsPage(): JSX.Element {
  const { t } = useTranslation();
  return (
    <RequireAuth>
      <AppShellV2 pageTitle={t("subagents.title")}>
        <SubagentsPageInner />
      </AppShellV2>
    </RequireAuth>
  );
}

export default SubagentsPage;
