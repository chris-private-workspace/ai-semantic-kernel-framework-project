/* eslint-disable no-restricted-syntax -- verbatim re-point: inline styles are mockup page-agents.jsx visual-layer literals copied byte-for-byte; re-expressing as Tailwind IS the drift bug this epic kills (STYLE.md §1 escape hatch + frontend-mockup-fidelity.md) */
/**
 * File: frontend/src/pages/subagents/SubagentsPage.tsx
 * Purpose: Subagent Registry — verbatim port from reference/design-mockups/page-agents.jsx SubagentsRegistry + SubagentDetail (lines 300-440), wired to real agent_catalog.
 * Category: Frontend / pages / subagents
 * Scope: Phase 57 / Sprint 57.38 Day 1 (mockup-port) → Sprint 57.78 (real-data wiring)
 *
 * Description:
 *   Verbatim CSS re-point of mockup `SubagentsRegistry` + `SubagentDetail` blocks:
 *     - .page-head + .page-title + .page-sub + .route-pill + .page-actions
 *     - .grid-3 4-mode KPI strip (fork=thinking / as_tool=tool / teammate=memory / handoff=info)
 *     - 2-col grid 1.4fr 1fr; left Card holds a 6-col .table; right Card holds
 *       inner Tabs (AgentSpec / Budget / Tools / Stats).
 *
 *   Sprint 57.78 (Track B) wired the page to the real `GET /api/v1/subagents`
 *   (agent_catalog registry, Sprint 57.70). Row fields (role←key / model /
 *   allowed_modes / status / system_prompt / budget / tools) are REAL; KPI
 *   counts are derived from `allowed_modes`. Usage metrics (calls24h / p95 /
 *   success / avg-tokens / top-orchestrator) have NO runtime data source and are
 *   honest-gapped to "—" (reported in the response `gapped` list) — AP-4: no
 *   fabricated 99.2% / 2840 / orchestrator-main. The 8-row fixture +
 *   `MODE_KPI` hardcoded counts + the carryover banner are removed (AP-2).
 *   Loading / empty states are mockup-native table rows (mirror TenantsTable).
 *
 *   Sprint 57.33 defensive `?.length` optional chain on `data?.items` preserved
 *   (AD-Overview-PreExisting-Route-Crashes regression guard; spec "survives
 *   backend payload with items field missing" must still pass).
 *
 * Created: 2026-05-17 (Sprint 57.19 Day 4 / US-C3)
 * Last Modified: 2026-06-04
 *
 * Modification History (newest-first):
 *   - 2026-06-04: Sprint 57.78 — wire to real agent_catalog registry; remove fixture + carryover banner; honest-gap usage metrics (AD-Subagent-RealList)
 *   - 2026-05-24: Sprint 57.38 Day 1 — verbatim CSS re-point to mockup classes per page-agents.jsx:300-450 (5th -with-extras app)
 *   - 2026-05-24: Sprint 57.33 Day 1 US-B1 — defensive ?. on items.length (crash fix; AD-Overview-PreExisting-Route-Crashes)
 *   - 2026-05-17: Initial creation (Sprint 57.19 Day 4 / US-C3)
 *
 * Related:
 *   - reference/design-mockups/page-agents.jsx (SubagentsRegistry + SubagentDetail; lines 300-440)
 *   - frontend/src/styles-mockup.css (byte-identical copy; Sprint 57.28 4-layer foundation)
 *   - frontend/src/components/mockup-ui.tsx (Button / Badge / Card / Tabs / Field primitives)
 *   - frontend/src/features/subagents/hooks/useSubagents.ts (real GET /subagents consumer)
 *   - frontend/src/features/admin-tenants/components/TenantsTable.tsx (57.73 mockup-native state pattern)
 */

import type { FC } from "react";
import { useMemo, useState } from "react";
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
import type { SubagentMode, SubagentSpec } from "@/features/subagents/types";

// ───────────────── mode tone map (mockup verbatim) ─────────────────
// Mockup `page-agents.jsx:357` inline ternary: fork→thinking, as_tool→tool, handoff→info, else→memory.
// Hoisted to a typed map so JSX stays scannable; tone values unchanged.

const MODE_TONE: Record<SubagentMode, string> = {
  fork: "thinking",
  as_tool: "tool",
  teammate: "memory",
  handoff: "info",
};

const ALL_MODES: SubagentMode[] = ["fork", "as_tool", "teammate", "handoff"];

// 4 KPI cards; per-mode color literal `var(--thinking|tool|memory|info)` is mockup verbatim (page-agents.jsx:333-336).
// Counts are derived REAL from items (allowed_modes membership) — no hardcoded fixture.
const MODE_KPI_META: Array<{ mode: SubagentMode; descKey: string; c: string }> = [
  { mode: "fork", descKey: "subagents.mode.forkDesc", c: "var(--thinking)" },
  { mode: "as_tool", descKey: "subagents.mode.asToolDesc", c: "var(--tool)" },
  { mode: "teammate", descKey: "subagents.mode.teammateDesc", c: "var(--memory)" },
  { mode: "handoff", descKey: "subagents.mode.handoffDesc", c: "var(--info)" },
];

// Subtle "—" placeholder for usage metrics with no runtime data source (AP-4
// honest gap, not a fabricated number). Mirrors TenantsTable GAP_PLACEHOLDER.
const GAP = <span style={{ color: "var(--fg-subtle)" }}>—</span>;

// Read a budget numeric field defensively from the spec's `budget` JSONB
// (meta_data.budget). Returns "" when absent so the input renders empty rather
// than a fabricated default (AP-4). Coerces numbers/strings to a string value.
function budgetValue(budget: Record<string, unknown> | null, key: string): string {
  const v = budget?.[key];
  if (v === undefined || v === null) return "";
  return String(v);
}

// ───────────────── detail card (inner tabs) ─────────────────

const SubagentDetailCard: FC<{ sub: SubagentSpec }> = ({ sub }) => {
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
      title={<span className="mono">{sub.key}</span>}
      subtitle={`AgentSpec · ${sub.allowed_modes.join(" + ")}`}
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
              <input className="input mono" readOnly defaultValue={sub.key} />
            </Field>
            <Field label={t("subagents.detail.model")}>
              <select className="select" value={sub.model ?? ""} onChange={() => undefined}>
                {/* model is a real readonly value here; the hardcoded options are
                    mockup-verbatim visual choices. When the real model isn't one
                    of them the controlled value still shows it (null → empty). */}
                <option value="">—</option>
                <option>claude-haiku-4-5</option>
                <option>claude-sonnet-4-5</option>
                <option>claude-opus-4-1</option>
                {sub.model &&
                  !["claude-haiku-4-5", "claude-sonnet-4-5", "claude-opus-4-1"].includes(
                    sub.model,
                  ) && <option value={sub.model}>{sub.model}</option>}
              </select>
            </Field>
            <Field label={t("subagents.detail.systemPrompt")}>
              <textarea
                className="textarea"
                rows={6}
                defaultValue={sub.system_prompt}
                key={sub.key}
              />
            </Field>
            <Field label={t("subagents.detail.allowedModes")}>
              <div className="row" style={{ gap: 6 }}>
                {ALL_MODES.map((m) => {
                  const checked = sub.allowed_modes.includes(m);
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
                        checked={checked}
                        readOnly
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
              <input
                className="input mono"
                key={`${sub.key}-mt`}
                defaultValue={budgetValue(sub.budget, "max_tokens")}
              />
            </Field>
            <Field label={t("subagents.detail.maxDuration")}>
              <input
                className="input mono"
                key={`${sub.key}-md`}
                defaultValue={budgetValue(sub.budget, "max_duration")}
              />
            </Field>
            <Field label={t("subagents.detail.maxConcurrent")}>
              <input
                className="input mono"
                key={`${sub.key}-mc`}
                defaultValue={budgetValue(sub.budget, "max_concurrent")}
              />
            </Field>
            <Field label={t("subagents.detail.maxDepth")}>
              <input
                className="input mono"
                key={`${sub.key}-mdp`}
                defaultValue={budgetValue(sub.budget, "max_depth")}
              />
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
            {sub.tools.length > 0 ? (
              <div className="kbar">
                {sub.tools.map((tool) => (
                  <Badge key={tool} tone="tool" pill>
                    {tool}
                  </Badge>
                ))}
              </div>
            ) : (
              <div className="subtle" style={{ fontSize: 12 }}>
                {t("subagents.detail.toolsEmpty")}
              </div>
            )}
            <Button variant="outline" size="sm" icon="plus">
              {t("subagents.detail.attachTool")}
            </Button>
          </div>
        )}
        {tab === "stats" && (
          // Usage metrics have NO runtime data source (in the response `gapped`
          // list) — honest-gapped to "—" rather than fabricated numbers (AP-4).
          <div className="col" style={{ gap: 8, fontSize: 12 }}>
            <div className="spread">
              <span className="muted">{t("subagents.detail.calls24h")}</span>
              <span className="mono">{GAP}</span>
            </div>
            <div className="spread">
              <span className="muted">{t("subagents.detail.p95")}</span>
              <span className="mono">{GAP}</span>
            </div>
            <div className="spread">
              <span className="muted">{t("subagents.detail.successRate")}</span>
              <span className="mono">{GAP}</span>
            </div>
            <div className="spread">
              <span className="muted">{t("subagents.detail.avgTokens")}</span>
              <span className="mono">{GAP}</span>
            </div>
            <div className="spread">
              <span className="muted">{t("subagents.detail.topOrchestrator")}</span>
              <span className="mono">{GAP}</span>
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
  const { data, isLoading, isError, error } = useSubagents();

  // FIX-Sprint-57-33 US-B1 (2026-05-24): defensive ?. on items — a backend
  // payload may omit the items field; previously crashed the page tree with
  // "Cannot read properties of undefined (reading 'length')"
  // (AD-Overview-PreExisting-Route-Crashes). Spec "survives missing items field".
  // Memoize so the `?? []` fallback identity is stable across renders (otherwise
  // the modeCounts useMemo below would re-run every render).
  const items: SubagentSpec[] = useMemo(() => data?.items ?? [], [data?.items]);

  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const active =
    items.find((s) => s.key === selectedKey) ?? items[0] ?? null;

  // KPI counts derived REAL from items (allowed_modes membership).
  const modeCounts = useMemo(() => {
    const counts: Record<SubagentMode, number> = {
      fork: 0,
      as_tool: 0,
      teammate: 0,
      handoff: 0,
    };
    for (const s of items) {
      for (const m of s.allowed_modes) {
        if (m in counts) counts[m] += 1;
      }
    }
    return counts;
  }, [items]);

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
              · {items.length} {t("subagents.registered")}
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

      {isError && (
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
          {error?.message}
        </div>
      )}

      {/* 4-mode KPI strip — verbatim port of page-agents.jsx:331-344 */}
      <div className="grid-3" style={{ marginBottom: 16 }}>
        {MODE_KPI_META.map((m) => (
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
            <div className="stat-value" style={{ fontSize: 22 }}>
              {modeCounts[m.mode]}
            </div>
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
              {isLoading ? (
                // Mockup-native loading row (mirror TenantsTable; no shadcn skeleton).
                <tr data-testid="subagent-row-loading">
                  <td colSpan={6} className="subtle" style={{ textAlign: "center", padding: 24, color: "var(--fg-subtle)" }}>
                    {t("subagents.list.loading")}
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr data-testid="subagent-row-empty">
                  <td colSpan={6} className="subtle" style={{ textAlign: "center", padding: 24, color: "var(--fg-subtle)" }}>
                    {t("subagents.list.empty")}
                  </td>
                </tr>
              ) : (
                items.map((s) => (
                  <tr
                    key={s.key}
                    onClick={() => setSelectedKey(s.key)}
                    style={{
                      background:
                        active?.key === s.key
                          ? "oklch(from var(--primary) l c h / 0.10)"
                          : undefined,
                    }}
                  >
                    <td className="mono" style={{ fontSize: 12, fontWeight: 500 }}>{s.key}</td>
                    <td className="mono subtle" style={{ fontSize: 11.5 }}>
                      {s.model ?? GAP}
                    </td>
                    <td>
                      <div className="row" style={{ gap: 4 }}>
                        {s.allowed_modes.map((m) => (
                          <Badge key={m} tone={MODE_TONE[m]}>{m}</Badge>
                        ))}
                      </div>
                    </td>
                    <td>
                      <Badge tone={s.status === "live" ? "success" : "warning"} dot>
                        {s.status}
                      </Badge>
                    </td>
                    <td className="mono tnum subtle" style={{ textAlign: "right" }}>{GAP}</td>
                    <td className="mono tnum subtle" style={{ textAlign: "right" }}>{GAP}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </Card>

        {active && <SubagentDetailCard sub={active} />}
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
