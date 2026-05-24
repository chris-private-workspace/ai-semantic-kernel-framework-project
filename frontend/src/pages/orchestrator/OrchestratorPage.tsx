/**
 * File: frontend/src/pages/orchestrator/OrchestratorPage.tsx
 * Purpose: /orchestrator — verbatim CSS re-point of mockup `page-agents.jsx` Orchestrator (L1-340).
 * Category: Frontend / pages / orchestrator
 * Scope: Phase 57 / Sprint 57.34 (Phase-2 per-page verbatim-CSS re-point; 5th app of epic, 1st non-rich-dashboard shape)
 *
 * Description:
 *   Verbatim CSS re-point per Sprint 57.28+ epic protocol (frontend-verbatim-css-repoint class).
 *   Component-logic layer preserved (useState + 6-tab dispatcher); visual layer re-pointed to
 *   mockup CSS classes byte-for-byte (.page-head / .grid-stats / .tabs / .grid-main / .col / .row /
 *   .field / .input / .select / .textarea / .chip / .kbar / .table / .brand-mark / .route-pill /
 *   .page-actions). Local TSX primitives (Badge / Stat / RiskBadge / TONE_CLASS / Switch / Field /
 *   inputBase Tailwind) dropped in favour of shared `mockup-ui.tsx` set (Tabs/Field/Switch promoted
 *   Sprint 57.34 Day 1/2/3).
 *
 *   Sprint 57.19 vintage was a Tailwind translation of the mockup (≈598 lines); this re-point
 *   removes Tailwind-translated CSS for verbatim mockup class names, drops ≈90 lines of local
 *   primitives, and inherits the consistent visual baseline shipped Sprint 57.28-57.32.
 *
 * Mockup source: `reference/design-mockups/page-agents.jsx` L1-340 (L341+ is /subagents).
 *
 * Created: 2026-05-17 (Sprint 57.19 Day 3 / US-C2)
 * Last Modified: 2026-05-24
 *
 * Modification History (newest-first):
 *   - 2026-05-24: Sprint 57.34 Day 3 — verbatim re-point: Tools + Subagents + Budgets + Policies tabs data-testid hooks (folded into Day 1 visual re-point per scope-shape; tab bodies use .table/.chip/.grid-main/.kbar/.thin-rule verbatim CSS)
 *   - 2026-05-24: Sprint 57.34 Day 2 — verbatim re-point: Config + Prompt tabs data-testid hooks + textarea verbatim defaultValue (folded into Day 1 visual re-point per scope-shape; tab bodies use .field/.input/.select/.textarea/.kbar verbatim CSS)
 *   - 2026-05-24: Sprint 57.34 Day 1 — verbatim re-point: page-head + grid-stats + Tabs structure + import mockup-ui primitives (drop local Badge/Stat/RiskBadge/TONE_CLASS/Field/Switch/inputBase/TextInput/Select)
 *   - 2026-05-17: Initial creation (Sprint 57.19 Day 3 / US-C2)
 *
 * Related:
 *   - reference/design-mockups/page-agents.jsx (canonical visual source L1-340)
 *   - frontend/src/components/mockup-ui.tsx (shared verbatim primitive set)
 *   - frontend/src/styles-mockup.css (Layer 2 — byte-identical mockup stylesheet, globally imported)
 *   - frontend/src/components/AppShellV2.tsx (page-level shell)
 *   - docs/rules-on-demand/frontend-mockup-fidelity.md (verbatim-CSS method)
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: inline styles are mockup page-agents.jsx visual-layer literals copied byte-for-byte; re-expressing as Tailwind IS the drift bug this epic kills (STYLE.md §1 escape hatch + frontend-mockup-fidelity.md) */

import type { FC, ReactNode } from "react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { AppShellV2 } from "@/components/AppShellV2";
import {
  Badge,
  Button,
  Card,
  Field,
  RiskBadge,
  Stat,
  Switch,
  Tabs,
  type RiskLevel,
} from "@/components/mockup-ui";
import { RequireAuth } from "@/features/auth/components/RequireAuth";

// ───────────────── Config tab (placeholder for Day 2 verbatim re-point) ─────────────────

const ConfigTab: FC = () => {
  const { t } = useTranslation();
  return (
    <div className="grid-main" data-testid="orchestrator-config-tab">
      <Card title={t("orchestrator.config.core")}>
        <div className="col" style={{ gap: 14, maxWidth: 540 }}>
          <Field label="Display name">
            <input className="input" defaultValue="orchestrator-main" />
          </Field>
          <Field label="Primary model" help="LLM-neutral; concrete provider chosen by adapter">
            <select className="select" defaultValue="claude-haiku-4-5">
              <option>claude-haiku-4-5</option>
              <option>claude-sonnet-4-5</option>
              <option>claude-opus-4-1</option>
              <option>gpt-5</option>
              <option>azure-openai-gpt-4o</option>
            </select>
          </Field>
          <Field label="Fallback model" help="Used when primary circuit breaker opens">
            <select className="select" defaultValue="claude-sonnet-4-5">
              <option>claude-sonnet-4-5</option>
              <option>claude-opus-4-1</option>
            </select>
          </Field>
          <div className="grid-2">
            <Field label="Temperature">
              <input className="input" defaultValue="0.2" />
            </Field>
            <Field label="Top P">
              <input className="input" defaultValue="0.95" />
            </Field>
          </div>
          <Field label="Max thinking tokens / turn">
            <input className="input" defaultValue="2048" />
          </Field>
          <Field label="Termination policy">
            <select className="select" defaultValue="end_turn (default)">
              <option>end_turn (default)</option>
              <option>max_turns</option>
              <option>budget_exhausted</option>
            </select>
          </Field>
        </div>
      </Card>
      <div className="col" style={{ gap: 14 }}>
        <Card title={t("orchestrator.config.memoryAccess")} subtitle={t("orchestrator.config.memoryAccessSub")}>
          <div className="col" style={{ gap: 10, fontSize: 12.5 }}>
            {(["system", "tenant", "role", "user", "session"] as const).map((s) => (
              <div key={s} className="spread">
                <span className="mono">{s}</span>
                <select
                  className="select"
                  style={{ width: 110, fontSize: 11.5 }}
                  defaultValue={s === "system" ? "read" : "write"}
                >
                  <option>none</option>
                  <option>read</option>
                  <option>write</option>
                </select>
              </div>
            ))}
          </div>
        </Card>
        <Card title={t("orchestrator.config.verification")} subtitle={t("orchestrator.config.verificationSub")}>
          <div className="col" style={{ gap: 8, fontSize: 12 }}>
            <div className="row">
              <Switch on={true} />
              <span>Require verification before write tools</span>
            </div>
            <div className="row">
              <Switch on={true} />
              <span>Block on failed verification</span>
            </div>
            <div className="row">
              <Switch on={false} />
              <span>Skip verification for risk=low tools</span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

const SYSTEM_PROMPT_PREVIEW = `# Role
You are the orchestrator agent for IPA Platform V2 — an enterprise AI operations platform for {{tenant_name}}.

# Goal
Receive operator requests, plan a sequence of actions, dispatch to specialized subagents when the task is complex, and produce a verified outcome with HITL gating for any write action.

# Available subagents (call as_tool or fork)
- log-scanner — tail + grep logs from a service
- dep-checker — health-probe downstream services
- metrics-pull — query observability backend
- evidence-collector — assemble RCA evidence bundle
- compliance-auditor — answer audit queries with citations

# Tool use policy
- Read tools: auto-call when needed.
- Write tools: ALWAYS request HITL approval first (see range 9).
- If a tool fails 3× with TRANSIENT class, escalate to a teammate subagent.

# Output discipline
- Always emit a short reasoning trace.
- Final answer must cite tool calls + memory reads as evidence.

# Constraints
- Never promise timelines.
- Never expose internal tooling names to non-operator roles.
- Always respect tenant_id boundary; cross-tenant access is a tripwire.`;

const PromptTab: FC = () => {
  const { t } = useTranslation();
  return (
    <div className="grid-main" data-testid="orchestrator-prompt-tab">
      <Card
        title={t("orchestrator.prompt.title")}
        subtitle={t("orchestrator.prompt.subtitle")}
        actions={
          <div className="row">
            <Badge tone="primary">{t("orchestrator.version")}</Badge>
            <Button variant="ghost" size="sm" icon="git">
              {t("orchestrator.prompt.history")}
            </Button>
            <Button variant="outline" size="sm" icon="play">
              {t("orchestrator.prompt.test")}
            </Button>
          </div>
        }
      >
        <textarea className="textarea" rows={20} defaultValue={SYSTEM_PROMPT_PREVIEW} />
      </Card>
      <div className="col" style={{ gap: 14 }}>
        <Card title={t("orchestrator.prompt.variables")}>
          <div className="col" style={{ gap: 8, fontSize: 12 }}>
            {[
              { k: "tenant_name", v: "string", req: true },
              { k: "operator_role", v: "enum", req: true },
              { k: "locale", v: "string", req: false },
              { k: "time_zone", v: "string", req: false },
            ].map((x) => (
              <div key={x.k} className="spread">
                <span className="mono" style={{ fontSize: 11.5 }}>{`{{${x.k}}}`}</span>
                <div className="row" style={{ gap: 4 }}>
                  <Badge>{x.v}</Badge>
                  {x.req && <Badge tone="warning">required</Badge>}
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
};

interface ToolRow {
  id: string;
  domain: string;
  risk: RiskLevel;
  sandbox: "NONE" | "RESTRICTED" | "FULL_SANDBOX";
  on: boolean;
}

const TOOLS_FIXTURE: ToolRow[] = [
  { id: "incidents.list", domain: "rca", risk: "low", sandbox: "NONE", on: true },
  { id: "metrics.query", domain: "rca", risk: "low", sandbox: "NONE", on: true },
  { id: "log.tail", domain: "rca", risk: "low", sandbox: "NONE", on: true },
  { id: "log.grep", domain: "rca", risk: "medium", sandbox: "RESTRICTED", on: true },
  { id: "evidence.attach", domain: "rca", risk: "medium", sandbox: "RESTRICTED", on: true },
  { id: "audit_query_logs", domain: "audit", risk: "medium", sandbox: "RESTRICTED", on: true },
  { id: "redact_pii", domain: "audit", risk: "high", sandbox: "RESTRICTED", on: false },
  { id: "page_oncall", domain: "incident", risk: "high", sandbox: "RESTRICTED", on: true },
  { id: "k8s.set_env", domain: "incident", risk: "high", sandbox: "FULL_SANDBOX", on: false },
  { id: "k8s.rollback", domain: "incident", risk: "critical", sandbox: "FULL_SANDBOX", on: false },
];

const SANDBOX_TONE: Record<ToolRow["sandbox"], string> = {
  NONE: "success",
  RESTRICTED: "warning",
  FULL_SANDBOX: "danger",
};

const ToolsTab: FC = () => {
  const { t } = useTranslation();
  return (
    <div data-testid="orchestrator-tools-tab">
    <Card
      title={t("orchestrator.tools.title")}
      subtitle={t("orchestrator.tools.subtitle")}
      actions={
        <Button
          variant="primary"
          size="sm"
          icon="plus"
          onClick={() => {
            location.hash = "tools";
          }}
        >
          {t("orchestrator.tools.openRegistry")}
        </Button>
      }
      bodyClass="flush"
    >
      <table className="table">
        <thead>
          <tr>
            <th>Tool</th>
            <th>Domain</th>
            <th>Risk</th>
            <th>Sandbox</th>
            <th>Enabled</th>
          </tr>
        </thead>
        <tbody>
          {TOOLS_FIXTURE.map((row) => (
            <tr key={row.id}>
              <td className="mono" style={{ fontSize: 12 }}>
                {row.id}
              </td>
              <td>
                <Badge>{row.domain}</Badge>
              </td>
              <td>
                <RiskBadge level={row.risk} />
              </td>
              <td>
                <Badge tone={SANDBOX_TONE[row.sandbox]}>{row.sandbox}</Badge>
              </td>
              <td>
                <Switch on={row.on} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
    </div>
  );
};

const SUBAGENT_MODE_TONE: Record<string, string> = {
  fork: "thinking",
  as_tool: "tool",
  handoff: "info",
  teammate: "memory",
};

interface SubagentRow {
  id: string;
  modes: string[];
  max_tok: number;
  max_conc: number;
  on: boolean;
}

const SUBAGENTS_FIXTURE: SubagentRow[] = [
  { id: "log-scanner", modes: ["fork", "as_tool"], max_tok: 4000, max_conc: 3, on: true },
  { id: "dep-checker", modes: ["fork", "as_tool"], max_tok: 3000, max_conc: 3, on: true },
  { id: "metrics-pull", modes: ["fork", "as_tool"], max_tok: 2000, max_conc: 5, on: true },
  { id: "evidence-collector", modes: ["as_tool"], max_tok: 8000, max_conc: 1, on: true },
  { id: "compliance-auditor", modes: ["handoff", "teammate"], max_tok: 16000, max_conc: 1, on: true },
  { id: "postmortem-writer", modes: ["handoff"], max_tok: 8000, max_conc: 1, on: false },
];

const SubagentsTab: FC = () => {
  const { t } = useTranslation();
  return (
    <div data-testid="orchestrator-subagents-tab">
    <Card
      title={t("orchestrator.subagents.title")}
      subtitle={t("orchestrator.subagents.subtitle")}
      actions={
        <Button
          variant="primary"
          size="sm"
          icon="plus"
          onClick={() => {
            location.hash = "subagents";
          }}
        >
          {t("orchestrator.subagents.openRegistry")}
        </Button>
      }
      bodyClass="flush"
    >
      <table className="table">
        <thead>
          <tr>
            <th>Subagent</th>
            <th>Allowed modes</th>
            <th>Max tokens</th>
            <th>Max concurrent</th>
            <th>Enabled</th>
          </tr>
        </thead>
        <tbody>
          {SUBAGENTS_FIXTURE.map((row) => (
            <tr key={row.id}>
              <td className="mono" style={{ fontSize: 12, fontWeight: 500 }}>
                {row.id}
              </td>
              <td>
                <div className="row" style={{ gap: 4 }}>
                  {row.modes.map((m) => (
                    <Badge key={m} tone={SUBAGENT_MODE_TONE[m] ?? ""}>
                      {m}
                    </Badge>
                  ))}
                </div>
              </td>
              <td className="mono tnum">{row.max_tok.toLocaleString()}</td>
              <td className="mono tnum">{row.max_conc}</td>
              <td>
                <Switch on={row.on} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
    </div>
  );
};

const BUDGETS: { k: string; v: number; unit: string }[] = [
  { k: "Max loop turns", v: 30, unit: "" },
  { k: "Max total tokens", v: 200000, unit: "" },
  { k: "Max wall-clock duration", v: 600, unit: "s" },
  { k: "Max subagent depth", v: 3, unit: "" },
  { k: "Max concurrent subagents", v: 5, unit: "" },
  { k: "Max tool calls / turn", v: 8, unit: "" },
];

const BudgetsTab: FC = () => {
  const { t } = useTranslation();
  return (
    <div className="grid-main" data-testid="orchestrator-budgets-tab">
      <Card title={t("orchestrator.budgets.loop")} subtitle={t("orchestrator.budgets.loopSub")}>
        <div className="col" style={{ gap: 14 }}>
          {BUDGETS.map((b) => (
            <div
              key={b.k}
              className="grid-2"
              style={{ gridTemplateColumns: "1fr auto", gap: 14, alignItems: "center" }}
            >
              <span style={{ fontSize: 12.5 }}>{b.k}</span>
              <div className="row" style={{ gap: 6 }}>
                <input className="input mono" defaultValue={b.v} style={{ width: 110 }} />
                <span className="muted" style={{ fontSize: 11 }}>
                  {b.unit}
                </span>
              </div>
            </div>
          ))}
        </div>
      </Card>
      <Card title={t("orchestrator.budgets.termination")}>
        <div className="col" style={{ gap: 8, fontSize: 12 }}>
          <div className="row">
            <Switch on={true} />
            <span>
              Stop on <span className="mono">stop_reason=end_turn</span>
            </span>
          </div>
          <div className="row">
            <Switch on={true} />
            <span>Stop on max-turns reached</span>
          </div>
          <div className="row">
            <Switch on={true} />
            <span>Stop on budget exhausted</span>
          </div>
          <div className="row">
            <Switch on={true} />
            <span>Stop on FATAL error class</span>
          </div>
          <div className="row">
            <Switch on={false} />
            <span>Stop on HITL rejection</span>
          </div>
          <div className="row">
            <Switch on={true} />
            <span>Stop on tripwire fired</span>
          </div>
        </div>
      </Card>
    </div>
  );
};

const PoliciesTab: FC = () => {
  const { t } = useTranslation();
  return (
    <div data-testid="orchestrator-policies-tab">
    <Card title={t("orchestrator.policies.title")}>
      <div className="col" style={{ gap: 12, maxWidth: 720 }}>
        <Field label="Default HITL policy for write tools">
          <select className="select" defaultValue="always_ask">
            <option>auto</option>
            <option>ask_once</option>
            <option>always_ask</option>
          </select>
        </Field>
        <Field label="Off-platform notifications">
          <div className="row" style={{ gap: 8 }}>
            <label className="row" style={{ gap: 5, fontSize: 12 }}>
              <input type="checkbox" defaultChecked /> Teams
            </label>
            <label className="row" style={{ gap: 5, fontSize: 12 }}>
              <input type="checkbox" defaultChecked /> Email
            </label>
            <label className="row" style={{ gap: 5, fontSize: 12 }}>
              <input type="checkbox" /> PagerDuty
            </label>
          </div>
        </Field>
        <Field label="Risk escalation">
          <div className="kbar">
            <Badge tone="success">low → auto</Badge>
            <Badge tone="info">medium → ask_once</Badge>
            <Badge tone="warning">high → always_ask</Badge>
            <Badge tone="danger">critical → always_ask + L2</Badge>
          </div>
        </Field>
        <div className="thin-rule" />
        <Field label="Cross-tenant tripwire (CANNOT disable)">
          <Badge tone="danger">armed · always-on</Badge>
        </Field>
        <Field label="PII in tool input">
          <Badge tone="danger">armed · always-on</Badge>
        </Field>
        <Field label="Provider key exposure">
          <Badge tone="danger">armed · always-on</Badge>
        </Field>
      </div>
    </Card>
    </div>
  );
};

// ───────────────── page ─────────────────

type TabId = "config" | "prompt" | "tools" | "subagents" | "budgets" | "policies";

function OrchestratorPageInner(): JSX.Element {
  const { t } = useTranslation();
  const [tab, setTab] = useState<TabId>("config");

  const tabItems: { id: TabId; label: ReactNode; count?: number }[] = [
    { id: "config", label: t("orchestrator.tabs.config") },
    { id: "prompt", label: t("orchestrator.tabs.prompt") },
    { id: "tools", label: t("orchestrator.tabs.tools"), count: 18 },
    { id: "subagents", label: t("orchestrator.tabs.subagents"), count: 6 },
    { id: "budgets", label: t("orchestrator.tabs.budgets") },
    { id: "policies", label: t("orchestrator.tabs.policies") },
  ];

  return (
    <div>
      <div className="page-head">
        <div>
          <div className="row" style={{ gap: 10, marginBottom: 6 }}>
            <div className="brand-mark" style={{ width: 32, height: 32 }} />
            <div>
              <div className="row" style={{ gap: 8 }}>
                <span className="mono" style={{ fontSize: 20, fontWeight: 600 }}>
                  orchestrator-main
                </span>
                <Badge tone="primary">{t("orchestrator.version")}</Badge>
                <Badge dot tone="success">
                  {t("orchestrator.live")}
                </Badge>
              </div>
              <div className="page-sub">
                {t("orchestrator.subtitle")}
                <span className="route-pill">/orchestrator</span>
              </div>
            </div>
          </div>
        </div>
        <div className="page-actions">
          <Button variant="outline" size="sm" icon="play">
            {t("orchestrator.actions.test")}
          </Button>
          <Button variant="outline" size="sm" icon="git">
            {t("orchestrator.actions.viewRepo")}
          </Button>
          <Button variant="primary" size="sm" icon="bolt">
            {t("orchestrator.actions.deploy")}
          </Button>
        </div>
      </div>

      <div className="grid-stats">
        <Stat label={t("orchestrator.kpi.sessions24h")} value="2,847" delta="+12%" deltaDir="up" />
        <Stat label={t("orchestrator.kpi.avgTurns")} value="4.2" delta="+0.1" deltaDir="down" />
        <Stat label={t("orchestrator.kpi.subagentSpawns")} value="412" delta="+8" deltaDir="up" />
        <Stat label={t("orchestrator.kpi.p95Session")} value="18.4" unit="s" delta="-2s" deltaDir="up" />
      </div>

      <Tabs
        items={tabItems.map((i) => ({ id: i.id, label: i.label, count: i.count }))}
        value={tab}
        onChange={(id) => setTab(id as TabId)}
        ariaLabel={t("orchestrator.tabs.label")}
      />

      {tab === "config" && <ConfigTab />}
      {tab === "prompt" && <PromptTab />}
      {tab === "tools" && <ToolsTab />}
      {tab === "subagents" && <SubagentsTab />}
      {tab === "budgets" && <BudgetsTab />}
      {tab === "policies" && <PoliciesTab />}
    </div>
  );
}

export function OrchestratorPage(): JSX.Element {
  const { t } = useTranslation();
  return (
    <RequireAuth>
      <AppShellV2 pageTitle={t("orchestrator.title")}>
        <OrchestratorPageInner />
      </AppShellV2>
    </RequireAuth>
  );
}

export default OrchestratorPage;
