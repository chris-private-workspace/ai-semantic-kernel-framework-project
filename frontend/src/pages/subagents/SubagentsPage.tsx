/* eslint-disable no-restricted-syntax -- verbatim re-point: inline styles are mockup page-agents.jsx visual-layer literals copied byte-for-byte; re-expressing as Tailwind IS the drift bug this epic kills (STYLE.md §1 escape hatch + frontend-mockup-fidelity.md) */
/**
 * File: frontend/src/pages/subagents/SubagentsPage.tsx
 * Purpose: Subagent Registry — verbatim port from reference/design-mockups/page-agents.jsx SubagentsRegistry + SubagentDetail (lines 300-440).
 * Category: Frontend / pages / subagents
 * Scope: Phase 57 / Sprint 57.38 Day 1 / Domain B (5th -with-extras app)
 *
 * Description:
 *   Verbatim CSS re-point of mockup `SubagentsRegistry` + `SubagentDetail` blocks:
 *     - .page-head + .page-title + .page-sub + .route-pill + .page-actions
 *     - .grid-3 4-mode KPI strip (fork=thinking / as_tool=tool / teammate=memory / handoff=info)
 *       with .stat + .stat-label + .stat-value + .subtle and colored borderLeft 3px
 *     - 2-col grid 1.4fr 1fr (verbatim inline style; eslint-disable no-restricted-syntax)
 *     - Left mockup-ui Card "Subagents" / "Click to inspect / edit" bodyClass="flush"
 *       containing .table with 6 headers and 8 fixture rows; selected row highlight
 *       via inline style background oklch(from var(--primary) l c h / 0.10)
 *     - Right Card with inner Tabs (AgentSpec / Budget / Tools / Stats) — per-tab
 *       layouts use .col / .row / .mono / .subtle / .input / .select / .textarea / .field
 *
 *   Sprint 57.33 defensive `?.length` optional chain on `data?.items?.length` preserved
 *   (AD-Overview-PreExisting-Route-Crashes regression guard; spec
 *   "survives backend payload with items field missing" must still pass).
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
 *   - 2026-05-24: Sprint 57.38 Day 1 — verbatim CSS re-point from Tailwind utilities to mockup .page-head/.grid-3/.stat/.card/.table/.row classes per page-agents.jsx:300-450 (5th -with-extras app)
 *   - 2026-05-24: Sprint 57.33 Day 1 US-B1 — defensive ?. on items.length (crash fix; AD-Overview-PreExisting-Route-Crashes)
 *   - 2026-05-17: Initial creation (Sprint 57.19 Day 4 / US-C3)
 *
 * Related:
 *   - reference/design-mockups/page-agents.jsx (SubagentsRegistry + SubagentDetail; lines 300-440)
 *   - reference/design-mockups/styles.css (.page-head .grid-3 .stat .card .table .row .col)
 *   - frontend/src/styles-mockup.css (byte-identical copy; Sprint 57.28 4-layer foundation)
 *   - frontend/src/components/mockup-ui.tsx (Button / Badge / Card / Tabs / Field primitives)
 *   - frontend/src/features/subagents/hooks/useSubagents.ts (US-B4 consumer; contract unchanged)
 */

import type { FC } from "react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { AppShellV2 } from "@/components/AppShellV2";
import {
  Badge,
  Button,
  Card,
  Field,
  Tabs,
} from "@/components/mockup-ui";
import { RequireAuth } from "@/features/auth/components/RequireAuth";
import { useSubagents } from "@/features/subagents/hooks/useSubagents";
import type { SubagentMode } from "@/features/subagents/types";

// ───────────────── mode tone map (mockup verbatim) ─────────────────
// Mockup `page-agents.jsx:357` inline ternary: fork→thinking, as_tool→tool, handoff→info, else→memory.
// Hoisted to a typed map so JSX stays scannable; tone values unchanged.

const MODE_TONE: Record<SubagentMode, string> = {
  fork: "thinking",
  as_tool: "tool",
  teammate: "memory",
  handoff: "info",
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

// 4 KPI cards; per-mode color literal `var(--thinking|tool|memory|info)` is mockup verbatim (page-agents.jsx:333-336).
const MODE_KPI: Array<{ mode: SubagentMode; count: number; descKey: string; c: string }> = [
  { mode: "fork", count: 3, descKey: "subagents.mode.forkDesc", c: "var(--thinking)" },
  { mode: "as_tool", count: 6, descKey: "subagents.mode.asToolDesc", c: "var(--tool)" },
  { mode: "teammate", count: 1, descKey: "subagents.mode.teammateDesc", c: "var(--memory)" },
  { mode: "handoff", count: 2, descKey: "subagents.mode.handoffDesc", c: "var(--info)" },
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
    <Card
      title={<span className="mono">{sub.role}</span>}
      subtitle={`AgentSpec · ${sub.modes.join(" + ")}`}
      bodyClass="flush"
      actions={
        <Button variant="ghost" size="sm" icon="play">
          {t("subagents.detail.testInvoke")}
        </Button>
      }
    >
      <div style={{ padding: "0 16px" }}>
        <Tabs
          items={tabItems}
          value={tab}
          onChange={(id) => setTab(id as typeof tab)}
          ariaLabel={t("subagents.detail.tabsLabel")}
        />
      </div>
      <div className="card-body">
        {tab === "spec" && (
          <div className="col" style={{ gap: 12 }}>
            <Field label={t("subagents.detail.role")}>
              <input className="input mono" readOnly defaultValue={sub.role} />
            </Field>
            <Field label={t("subagents.detail.model")}>
              <select className="select" defaultValue={sub.model}>
                <option>claude-haiku-4-5</option>
                <option>claude-sonnet-4-5</option>
                <option>claude-opus-4-1</option>
              </select>
            </Field>
            <Field label={t("subagents.detail.systemPrompt")}>
              <textarea className="textarea" rows={6} defaultValue={sub.prompt} />
            </Field>
            <Field label={t("subagents.detail.allowedModes")}>
              <div className="row" style={{ gap: 6 }}>
                {(["fork", "as_tool", "teammate", "handoff"] as SubagentMode[]).map((m) => {
                  const checked = sub.modes.includes(m);
                  return (
                    <label
                      key={m}
                      className="row"
                      style={{
                        gap: 5,
                        fontSize: 12,
                        padding: "4px 8px",
                        border: "1px solid var(--border)",
                        borderRadius: 4,
                        background: checked ? "var(--primary-soft)" : "var(--bg-1)",
                        cursor: "pointer",
                      }}
                    >
                      <input
                        type="checkbox"
                        defaultChecked={checked}
                        style={{ accentColor: "var(--primary)" }}
                      />
                      <span
                        className="mono"
                        style={{ color: checked ? "var(--primary)" : "var(--fg-muted)" }}
                      >
                        {m}
                      </span>
                    </label>
                  );
                })}
              </div>
            </Field>
          </div>
        )}
        {tab === "budget" && (
          <div className="col" style={{ gap: 12 }}>
            <Field label={t("subagents.detail.maxTokens")}>
              <input className="input mono" defaultValue="10000" />
            </Field>
            <Field label={t("subagents.detail.maxDuration")}>
              <input className="input mono" defaultValue="300" />
            </Field>
            <Field label={t("subagents.detail.maxConcurrent")}>
              <input className="input mono" defaultValue="5" />
            </Field>
            <Field label={t("subagents.detail.maxDepth")}>
              <input className="input mono" defaultValue="3" />
            </Field>
            <div
              className="muted"
              style={{
                fontSize: 11.5,
                padding: 10,
                background: "var(--bg-2)",
                border: "1px solid var(--border)",
                borderRadius: 6,
              }}
            >
              {t("subagents.detail.worktreeAbsent")}
            </div>
          </div>
        )}
        {tab === "tools" && (
          <div className="col" style={{ gap: 8 }}>
            <div
              className="subtle"
              style={{
                fontSize: 11,
                fontFamily: "var(--font-mono)",
                textTransform: "uppercase",
                letterSpacing: "0.06em",
              }}
            >
              {t("subagents.detail.toolsAttached")}
            </div>
            <div className="kbar">
              <Badge tone="tool" pill>log.tail</Badge>
              <Badge tone="tool" pill>log.grep</Badge>
              <Badge tone="tool" pill>metrics.query</Badge>
            </div>
            <Button variant="outline" size="sm" icon="plus">
              {t("subagents.detail.attachTool")}
            </Button>
          </div>
        )}
        {tab === "stats" && (
          <div className="col" style={{ gap: 8, fontSize: 12 }}>
            <div className="spread">
              <span className="muted">{t("subagents.detail.calls24h")}</span>
              <span className="mono">{sub.calls24}</span>
            </div>
            <div className="spread">
              <span className="muted">{t("subagents.detail.p95")}</span>
              <span className="mono">{sub.p95}s</span>
            </div>
            <div className="spread">
              <span className="muted">{t("subagents.detail.successRate")}</span>
              <span className="mono">99.2%</span>
            </div>
            <div className="spread">
              <span className="muted">{t("subagents.detail.avgTokens")}</span>
              <span className="mono">2,840</span>
            </div>
            <div className="spread">
              <span className="muted">{t("subagents.detail.topOrchestrator")}</span>
              <span className="mono">orchestrator-main</span>
            </div>
          </div>
        )}
      </div>
    </Card>
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
    <div>
      {/* page head — verbatim port of page-agents.jsx:316-329 */}
      <div className="page-head">
        <div>
          <div className="page-title">{t("subagents.title")}</div>
          <div className="page-sub">
            {t("subagents.subtitle")}
            <span className="route-pill">/subagents</span>
            <span className="mono subtle">
              · {SUBAGENT_LIST.length} {t("subagents.registered")}
            </span>
          </div>
        </div>
        <div className="page-actions">
          <Button variant="outline" size="sm" icon="git">
            {t("subagents.syncFromRepo")}
          </Button>
          <Button variant="primary" size="sm" icon="plus">
            {t("subagents.newSubagent")}
          </Button>
        </div>
      </div>

      {/* carryover banner (US-B4 stub) — preserved role="status" for spec compat */}
      {!isLoading && !error && notImplementedReason && realItemsCount === 0 && (
        <div
          role="status"
          style={{
            margin: "0 0 14px 0",
            padding: 10,
            border: "1px solid color-mix(in oklch, var(--warning) 40%, transparent)",
            background: "color-mix(in oklch, var(--warning) 8%, transparent)",
            borderRadius: 8,
            fontSize: 12,
            color: "var(--warning)",
          }}
        >
          <strong>{t("subagents.carryoverHeading")}</strong>: {notImplementedReason}
        </div>
      )}
      {error && (
        <div
          role="alert"
          style={{
            margin: "0 0 14px 0",
            padding: 10,
            border: "1px solid color-mix(in oklch, var(--danger) 40%, transparent)",
            background: "color-mix(in oklch, var(--danger) 8%, transparent)",
            borderRadius: 8,
            fontSize: 12,
            color: "var(--danger)",
          }}
        >
          {error.message}
        </div>
      )}

      {/* 4-mode KPI strip — verbatim port of page-agents.jsx:331-344 */}
      <div className="grid-3" style={{ marginBottom: 16 }}>
        {MODE_KPI.map((m) => (
          <div key={m.mode} className="stat" style={{ borderLeft: `3px solid ${m.c}` }}>
            <div className="stat-label">
              {/* keep <div> wrapper so spec `getByText(mode, { selector: "div" })` resolves */}
              <div
                style={{
                  color: m.c,
                  fontWeight: 600,
                  textTransform: "uppercase",
                  letterSpacing: "0.04em",
                  fontFamily: "var(--font-mono)",
                }}
              >
                {m.mode}
              </div>
            </div>
            <div className="stat-value" style={{ fontSize: 22 }}>{m.count}</div>
            <div className="subtle" style={{ fontSize: 10.5 }}>{t(m.descKey)}</div>
          </div>
        ))}
      </div>

      {/* 2-col grid: list left, detail right — verbatim port of page-agents.jsx:346-370 */}
      <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 14 }}>
        <Card
          title={t("subagents.list.title")}
          subtitle={t("subagents.list.subtitle")}
          bodyClass="flush"
        >
          <table className="table">
            <thead>
              <tr>
                <th>{t("subagents.col.role")}</th>
                <th>{t("subagents.col.model")}</th>
                <th>{t("subagents.col.modes")}</th>
                <th>{t("subagents.col.status")}</th>
                <th style={{ textAlign: "right" }}>{t("subagents.col.calls24h")}</th>
                <th style={{ textAlign: "right" }}>{t("subagents.col.p95")}</th>
              </tr>
            </thead>
            <tbody>
              {SUBAGENT_LIST.map((s) => (
                <tr
                  key={s.id}
                  onClick={() => setSelectedId(s.id)}
                  style={{
                    background:
                      selectedId === s.id
                        ? "oklch(from var(--primary) l c h / 0.10)"
                        : undefined,
                  }}
                >
                  <td className="mono" style={{ fontSize: 12, fontWeight: 500 }}>{s.role}</td>
                  <td className="mono subtle" style={{ fontSize: 11.5 }}>{s.model}</td>
                  <td>
                    <div className="row" style={{ gap: 4 }}>
                      {s.modes.map((m) => (
                        <Badge key={m} tone={MODE_TONE[m]}>{m}</Badge>
                      ))}
                    </div>
                  </td>
                  <td>
                    <Badge tone={s.status === "live" ? "success" : "warning"} dot>
                      {s.status}
                    </Badge>
                  </td>
                  <td className="mono tnum" style={{ textAlign: "right" }}>{s.calls24}</td>
                  <td className="mono tnum subtle" style={{ textAlign: "right" }}>{s.p95}s</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>

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
