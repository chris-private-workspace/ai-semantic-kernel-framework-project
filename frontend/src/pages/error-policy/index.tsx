/* eslint-disable no-restricted-syntax -- verbatim re-point: inline styles are mockup page-platform.jsx visual-layer literals copied byte-for-byte; re-expressing as Tailwind IS the drift bug this epic kills (STYLE.md §1 escape hatch + frontend-mockup-fidelity.md AP-Phase2-C) */
/**
 * File: frontend/src/pages/error-policy/index.tsx
 * Purpose: Error Policy — verbatim mockup port of `reference/design-mockups/page-platform.jsx:426 ErrorPolicyPage` (PROP→real).
 * Category: Frontend / pages / error-policy
 * Scope: Phase 57 / Sprint 57.39 Day 2 / Domain D (PROP→real promotion)
 *
 * Description:
 *   Sprint 57.39 Day 2 promotes the 1-line ComingSoonPlaceholder re-export to a real-ship
 *   verbatim mockup port. Replaces the Sprint 57.18 PROP stub. Page renders:
 *
 *     1. AuthGate + AppShellV2 wrap (pageTitle "Error Policy"; sidebar + sticky header
 *        from Sprint 57.8 US-2 UserMenu architecture)
 *     2. `.page-head` with title "Error Policy" + subtitle "Range 8 · 4-class taxonomy ·
 *        Circuit breaker · Retry budget · Terminator" + `.route-pill` /error-policy +
 *        Edit-policy/Export actions (AP-2 BackendGapBanner appended above)
 *     3. 4-stat `.grid-stats` strip (Errors · 1h / Auto-recovered / Circuits open /
 *        Budget burn)
 *     4. 2-col `.grid-main` grid:
 *        - Left: `Card` "4-class taxonomy" with 4-class strip (TRANSIENT / LLM_RECOVERABLE
 *          / HITL_RECOVERABLE / FATAL) — each class has color dot + label + desc + count
 *          + `.bar-track` proportional bar; trailing `.thin-rule` + muted source attribution
 *        - Right: `Card` "Retry budget" `bodyClass="dense"` with 4 budgets (Inference /
 *          Tool / Subagent / HITL) — each row has `.spread` name+used/max + `.bar-track`
 *          conditional warning/success color (>70% → warning)
 *     5. Full-width `Card` "Circuit breakers" `bodyClass="flush"` with `.table` of 6 adapters
 *        (azure_openai / anthropic / vector_db / tool.k8s / tool.zendesk / tool.slack) ×
 *        6 columns (Adapter / State / Failures / Threshold / Last trip / Force-close action);
 *        State `Badge` tone success(closed) / warning(half_open) / danger(open) + `dot`
 *
 *   AP-Phase2-A: NO outer padding wrapper — AppShellV2 `.content` already provides padding.
 *   AP-Phase2-B: Inline mixed-font rows use `.row` / `.spread` flex baseline.
 *   AP-Phase2-C: All borders via mockup tokens (`.card` → `--border`); zero shadcn classes.
 *
 *   Data fixtures (ERROR_CLASSES / CIRCUIT_BREAKERS / inline retry budgets) are mockup
 *   verbatim from page-platform.jsx:410-424 + L476-481.
 *
 * Created: 2026-05-24 (Sprint 57.39 Day 2 / Domain D — PROP→real promotion)
 * Last Modified: 2026-05-24
 *
 * Modification History (newest-first):
 *   - 2026-05-24: Sprint 57.39 Day 2 — PROP→real promotion: verbatim mockup port from page-platform.jsx:426 ErrorPolicyPage (replaces 1-line ComingSoonPlaceholder re-export)
 *
 * Related:
 *   - reference/design-mockups/page-platform.jsx:426-520 (ErrorPolicyPage source) + L410-424 (ERROR_CLASSES / CIRCUIT_BREAKERS fixtures)
 *   - reference/design-mockups/styles.css (.page-head .grid-stats .grid-main .card .table .col .row .spread .bar-track .thin-rule .mono .subtle)
 *   - frontend/src/styles-mockup.css (byte-identical copy; Sprint 57.28 4-layer foundation)
 *   - frontend/src/components/mockup-ui.tsx (Button / Badge / Card / Stat primitives)
 *   - docs/rules-on-demand/frontend-mockup-fidelity.md (AP-Phase2-A/B/C codified post-FIX-011)
 */

import type { FC } from "react";

import { AppShellV2 } from "@/components/AppShellV2";
import {
  Badge,
  Button,
  Card,
  Stat,
} from "@/components/mockup-ui";
import { RequireAuth } from "@/features/auth/components/RequireAuth";

// ───────────────── fixtures (verbatim port of page-platform.jsx:410-424) ─────────────────

interface ErrorClass {
  id: string;
  desc: string;
  count: number;
  c: string;
  pct: number;
}

const ERROR_CLASSES: ErrorClass[] = [
  { id: "TRANSIENT",        desc: "Network blip / 5xx · auto-retry with backoff",                count: 142, c: "var(--info)",     pct: 38 },
  { id: "LLM_RECOVERABLE",  desc: "Tool returned error · LLM self-corrects on next turn",         count: 84,  c: "var(--thinking)", pct: 22 },
  { id: "HITL_RECOVERABLE", desc: "User-fixable · missing creds / data · pauses loop for input",  count: 12,  c: "var(--warning)",  pct: 3 },
  { id: "FATAL",            desc: "Unrecoverable · loop terminates · session marked failed",       count: 2,   c: "var(--danger)",   pct: 1 },
];

interface CircuitBreaker {
  adapter: string;
  state: "closed" | "half_open" | "open";
  failures: number;
  threshold: number;
  lastTrip: string;
}

const CIRCUIT_BREAKERS: CircuitBreaker[] = [
  { adapter: "azure_openai", state: "closed",    failures: 2, threshold: 10, lastTrip: "—" },
  { adapter: "anthropic",    state: "closed",    failures: 0, threshold: 10, lastTrip: "—" },
  { adapter: "vector_db",    state: "closed",    failures: 1, threshold: 5,  lastTrip: "—" },
  { adapter: "tool.k8s",     state: "half_open", failures: 3, threshold: 5,  lastTrip: "2m ago · 4/5" },
  { adapter: "tool.zendesk", state: "open",      failures: 8, threshold: 5,  lastTrip: "8m ago · cooldown 22m" },
  { adapter: "tool.slack",   state: "closed",    failures: 0, threshold: 5,  lastTrip: "—" },
];

interface RetryBudget {
  name: string;
  used: number;
  max: number;
}

const RETRY_BUDGETS: RetryBudget[] = [
  { name: "Inference retries",  used: 18, max: 100 },
  { name: "Tool retries",       used: 84, max: 500 },
  { name: "Subagent re-spawns", used: 3,  max: 50 },
  { name: "HITL re-prompts",    used: 1,  max: 10 },
];

// ───────────────── page ─────────────────

const ErrorPolicyPageInner: FC = () => (
  <div>
    {/* page head — verbatim port of page-platform.jsx:428-440 */}
    <div className="page-head">
      <div>
        <div className="page-title">Error Policy</div>
        <div className="page-sub">
          Range 8 · 4-class taxonomy · Circuit breaker · Retry budget · Terminator
          <span className="route-pill">/error-policy</span>
        </div>
      </div>
      <div className="page-actions">
        <Button variant="outline" size="sm" icon="git">Edit policy</Button>
        <Button variant="outline" size="sm" icon="download">Export</Button>
      </div>
    </div>

    {/* AP-2 BackendGapBanner — error-policy is wired in agent_harness/_contracts/errors.py
        but no /api/v1/error-policy endpoint yet; data is fixture for now */}
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
      <strong>Backend gap</strong>: agent_harness/_contracts/errors.py wired but /api/v1/error-policy
      read API not yet shipped; class taxonomy + circuit breaker state + retry budgets shown from
      mockup fixtures. Backend pairing: Phase 58+ AD-ErrorPolicy-Backend-API.
    </div>

    {/* 4-stat strip — verbatim port of page-platform.jsx:442-447 */}
    <div className="grid-stats">
      <Stat label="Errors · 1h" value="240" delta="+12" deltaDir="down" />
      <Stat label="Auto-recovered" value="97.5" unit="%" delta="+0.8pp" deltaDir="up" />
      <Stat label="Circuits open" value="1" delta="+1" deltaDir="down" />
      <Stat label="Budget burn" value="12.4" unit="%" delta="-2pp" deltaDir="up" />
    </div>

    {/* 2-col main grid — verbatim port of page-platform.jsx:449-494 */}
    <div className="grid-main">
      <Card
        title="4-class taxonomy"
        subtitle="Where errors land · last 1h"
        actions={
          <Button variant="ghost" size="sm" icon="filter">Drill into class</Button>
        }
      >
        <div className="col" style={{ gap: 12 }}>
          {ERROR_CLASSES.map((c) => (
            <div key={c.id}>
              <div className="row" style={{ gap: 8, marginBottom: 4 }}>
                <span style={{ width: 8, height: 8, borderRadius: 2, background: c.c }} />
                <span className="mono" style={{ fontSize: 12, fontWeight: 600, color: c.c }}>{c.id}</span>
                <span className="muted" style={{ fontSize: 11.5, marginLeft: 6 }}>{c.desc}</span>
                <span className="mono tnum" style={{ marginLeft: "auto", fontSize: 11.5 }}>{c.count}</span>
              </div>
              <div className="bar-track">
                <span style={{ width: `${c.pct}%`, background: c.c }} />
              </div>
            </div>
          ))}
        </div>
        <div className="thin-rule" />
        <div className="muted" style={{ fontSize: 11.5, lineHeight: 1.55 }}>
          Sourced from <span className="mono">agent_harness/_contracts/errors.py</span>. ErrorClass enum drives{" "}
          <span className="mono">DefaultErrorPolicy.classify()</span> via MRO walk; adapters subclass{" "}
          <span className="mono">AuthenticationError</span> /{" "}
          <span className="mono">MissingDataError</span> /{" "}
          <span className="mono">ToolExecutionError</span>.
        </div>
      </Card>

      <Card title="Retry budget" subtitle="Per-tool circuit budget · 1h window" bodyClass="dense">
        <div className="col" style={{ gap: 10 }}>
          {RETRY_BUDGETS.map((b) => {
            const ratio = b.used / b.max;
            return (
              <div key={b.name}>
                <div className="spread" style={{ marginBottom: 3, fontSize: 12 }}>
                  <span>{b.name}</span>
                  <span className="mono tnum">
                    {b.used}
                    <span className="subtle">/{b.max}</span>
                  </span>
                </div>
                <div className="bar-track">
                  <span
                    style={{
                      width: `${ratio * 100}%`,
                      background: ratio > 0.7 ? "var(--warning)" : "var(--success)",
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </Card>
    </div>

    {/* spacer + circuit breakers table — verbatim port of page-platform.jsx:496-518 */}
    <div style={{ height: 14 }} />

    <Card
      title="Circuit breakers"
      subtitle="Per-adapter state · open = traffic blocked"
      bodyClass="flush"
    >
      <table className="table">
        <thead>
          <tr>
            <th>Adapter</th>
            <th>State</th>
            <th style={{ textAlign: "right" }}>Failures</th>
            <th style={{ textAlign: "right" }}>Threshold</th>
            <th>Last trip</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {CIRCUIT_BREAKERS.map((cb) => (
            <tr key={cb.adapter}>
              <td className="mono" style={{ fontSize: 12 }}>{cb.adapter}</td>
              <td>
                <Badge
                  tone={cb.state === "closed" ? "success" : cb.state === "half_open" ? "warning" : "danger"}
                  dot
                >
                  {cb.state}
                </Badge>
              </td>
              <td className="mono tnum" style={{ textAlign: "right" }}>{cb.failures}</td>
              <td className="mono tnum subtle" style={{ textAlign: "right" }}>{cb.threshold}</td>
              <td className="subtle mono" style={{ fontSize: 11 }}>{cb.lastTrip}</td>
              <td>
                {cb.state === "open" && (
                  <Button variant="outline" size="sm" icon="refresh">Force close</Button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  </div>
);

export default function ErrorPolicyPage(): JSX.Element {
  return (
    <RequireAuth>
      <AppShellV2 pageTitle="Error Policy">
        <ErrorPolicyPageInner />
      </AppShellV2>
    </RequireAuth>
  );
}
