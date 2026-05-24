/* eslint-disable no-restricted-syntax -- verbatim re-point: inline styles are mockup page-platform2.jsx visual-layer literals copied byte-for-byte; re-expressing as Tailwind IS the drift bug this epic kills (STYLE.md §1 escape hatch + frontend-mockup-fidelity.md AP-Phase2-C) */
/**
 * File: frontend/src/pages/redaction/index.tsx
 * Purpose: Observation Masker — verbatim mockup port of `reference/design-mockups/page-platform2.jsx:254 RedactionPage` (PROP→real).
 * Category: Frontend / pages / redaction
 * Scope: Phase 57 / Sprint 57.39 Day 2 / Domain C (PROP→real promotion)
 *
 * Description:
 *   Sprint 57.39 Day 2 promotes the 1-line ComingSoonPlaceholder re-export to a real-ship
 *   verbatim mockup port. Replaces the Sprint 57.18 PROP stub. Page renders:
 *
 *     1. AuthGate + AppShellV2 wrap (pageTitle "Redaction"; sidebar + sticky header from
 *        Sprint 57.8 US-2 UserMenu architecture)
 *     2. `.page-head` with title "Observation Masker" + subtitle "Range 3 · PII + secret
 *        redaction · runs on every tool input / output" + `.route-pill` /redaction +
 *        Export/New-pattern actions (AP-2 BackendGapBanner appended above — backend not
 *        wired; data is fixture-based per CLAUDE.md §Frontend Mockup-Fidelity Hard
 *        Constraint "後端尚未支援的 widget → 仍依 mockup 視覺實作，data 用 fixture")
 *     3. 4-stat `.grid-stats` strip (Redactions / Patterns active / Critical hits /
 *        False-positive rate)
 *     4. 2-col `.grid-main` grid:
 *        - Left: `Card` "Patterns" `bodyClass="flush"` containing `.table` with 6 columns
 *          (Id / Kind / Pattern / Severity / Hits / Enabled) × 8 fixture rows
 *        - Right: `Card` "Recent redactions" with 5-event `.col` of redaction events;
 *          each event has Badge tone="memory" pattern + caller + at + struck-through
 *          original + arrow-prefix redacted (line-through + var(--success))
 *
 *   AP-Phase2-A: NO outer padding wrapper — AppShellV2 `.content` already provides padding.
 *   AP-Phase2-B: Inline mixed-font rows (caller mono + at sans) use `.row` flex baseline.
 *   AP-Phase2-C: All borders via mockup tokens (`.card` → `--border`); zero shadcn classes.
 *
 *   Data fixtures (REDACT_PATTERNS / REDACT_RECENT) are mockup verbatim from page-platform2.jsx:235-252.
 *
 * Created: 2026-05-24 (Sprint 57.39 Day 2 / Domain C — PROP→real promotion)
 * Last Modified: 2026-05-24
 *
 * Modification History (newest-first):
 *   - 2026-05-24: Sprint 57.39 Day 2 — PROP→real promotion: verbatim mockup port from page-platform2.jsx:254 RedactionPage (replaces 1-line ComingSoonPlaceholder re-export)
 *
 * Related:
 *   - reference/design-mockups/page-platform2.jsx:254-313 (RedactionPage source) + L235-252 (REDACT_PATTERNS / REDACT_RECENT fixtures)
 *   - reference/design-mockups/styles.css (.page-head .grid-stats .grid-main .card .table .col .row .mono .subtle)
 *   - frontend/src/styles-mockup.css (byte-identical copy; Sprint 57.28 4-layer foundation)
 *   - frontend/src/components/mockup-ui.tsx (Button / Badge / Card / Stat / RiskBadge / Switch primitives)
 *   - docs/rules-on-demand/frontend-mockup-fidelity.md (AP-Phase2-A/B/C codified post-FIX-011)
 */

import type { FC } from "react";

import { AppShellV2 } from "@/components/AppShellV2";
import {
  Badge,
  Button,
  Card,
  RiskBadge,
  type RiskLevel,
  Stat,
  Switch,
} from "@/components/mockup-ui";
import { RequireAuth } from "@/features/auth/components/RequireAuth";

// ───────────────── fixtures (verbatim port of page-platform2.jsx:235-252) ─────────────────

interface RedactPattern {
  id: string;
  kind: "PII" | "secret";
  pattern: string;
  count: number;
  severity: RiskLevel;
  enabled: boolean;
}

const REDACT_PATTERNS: RedactPattern[] = [
  { id: "email",       kind: "PII",    pattern: "[a-z0-9._%+-]+@[a-z0-9.-]+\\.[a-z]{2,}",          count: 1820, severity: "medium",   enabled: true },
  { id: "credit_card", kind: "PII",    pattern: "\\b\\d{4}[ -]?\\d{4}[ -]?\\d{4}[ -]?\\d{4}\\b",   count: 18,   severity: "critical", enabled: true },
  { id: "ssn",         kind: "PII",    pattern: "\\b\\d{3}-\\d{2}-\\d{4}\\b",                       count: 4,    severity: "critical", enabled: true },
  { id: "ipv4",        kind: "PII",    pattern: "\\b(?:\\d{1,3}\\.){3}\\d{1,3}\\b",                 count: 2840, severity: "low",      enabled: true },
  { id: "aws_key",     kind: "secret", pattern: "AKIA[0-9A-Z]{16}",                                  count: 2,    severity: "critical", enabled: true },
  { id: "bearer",      kind: "secret", pattern: "(?i)bearer\\s+[a-z0-9._-]+",                        count: 184,  severity: "high",     enabled: true },
  { id: "github_pat",  kind: "secret", pattern: "ghp_[A-Za-z0-9]{36}",                               count: 0,    severity: "critical", enabled: true },
  { id: "private_key", kind: "secret", pattern: "-----BEGIN .+ PRIVATE KEY-----",                    count: 0,    severity: "critical", enabled: true },
];

interface RedactEvent {
  at: string;
  caller: string;
  pattern: string;
  original: string;
  redacted: string;
  agent: string;
}

const REDACT_RECENT: RedactEvent[] = [
  { at: "now",     caller: "tools.zendesk", pattern: "email",       original: "jamie@acme.com",       redacted: "[EMAIL]",        agent: "incident-responder" },
  { at: "1m ago",  caller: "tools.metrics", pattern: "ipv4",        original: "10.0.5.42",            redacted: "[IPV4]",         agent: "incident-responder" },
  { at: "2m ago",  caller: "memory.write",  pattern: "bearer",      original: "Bearer eyJ...…wK4",    redacted: "[BEARER_TOKEN]", agent: "compliance-auditor" },
  { at: "8m ago",  caller: "tools.slack",   pattern: "credit_card", original: "4532 1234 5678 9012", redacted: "[CC]",           agent: "billing-helper" },
  { at: "12m ago", caller: "memory.read",   pattern: "email",       original: "support@globex.eu",   redacted: "[EMAIL]",        agent: "support-triage" },
];

// ───────────────── page ─────────────────

const RedactionPageInner: FC = () => {
  const activePatterns = REDACT_PATTERNS.filter((p) => p.enabled).length;
  const criticalHits = REDACT_PATTERNS
    .filter((p) => p.severity === "critical")
    .reduce((s, p) => s + p.count, 0);

  return (
    <div>
      {/* page head — verbatim port of page-platform2.jsx:256-268 */}
      <div className="page-head">
        <div>
          <div className="page-title">Observation Masker</div>
          <div className="page-sub">
            Range 3 · PII + secret redaction · runs on every tool input / output
            <span className="route-pill">/redaction</span>
          </div>
        </div>
        <div className="page-actions">
          <Button variant="outline" size="sm" icon="download">Export</Button>
          <Button variant="primary" size="sm" icon="plus">New pattern</Button>
        </div>
      </div>

      {/* AP-2 BackendGapBanner — backend not yet wired; data is fixture-based per
          CLAUDE.md §Frontend Mockup-Fidelity Hard Constraint */}
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
        <strong>Backend gap</strong>: observation-masker API not yet shipped; pattern catalog +
        recent events shown from mockup fixtures. Backend pairing: Phase 58+ AD-Redaction-Backend-API.
      </div>

      {/* 4-stat strip — verbatim port of page-platform2.jsx:270-275 */}
      <div className="grid-stats">
        <Stat label="Redactions · 1h" value="4,870" delta="+220" deltaDir="up" />
        <Stat label="Patterns active" value={String(activePatterns)} unit={`/${REDACT_PATTERNS.length}`} />
        <Stat label="Critical hits · 24h" value={String(criticalHits)} delta="+2" deltaDir="down" />
        <Stat label="False-positive rate" value="0.4" unit="%" delta="-0.1pp" deltaDir="up" />
      </div>

      {/* 2-col main grid — verbatim port of page-platform2.jsx:277-311 */}
      <div className="grid-main">
        <Card
          title="Patterns"
          subtitle={`${REDACT_PATTERNS.length} regex + classifier rules`}
          bodyClass="flush"
        >
          <table className="table">
            <thead>
              <tr>
                <th>Id</th>
                <th>Kind</th>
                <th>Pattern</th>
                <th>Severity</th>
                <th style={{ textAlign: "right" }}>Hits · 24h</th>
                <th>Enabled</th>
              </tr>
            </thead>
            <tbody>
              {REDACT_PATTERNS.map((p) => (
                <tr key={p.id}>
                  <td className="mono" style={{ fontSize: 12 }}>{p.id}</td>
                  <td>
                    <Badge tone={p.kind === "secret" ? "danger" : "warning"}>{p.kind}</Badge>
                  </td>
                  <td
                    className="mono subtle"
                    style={{
                      fontSize: 11,
                      maxWidth: 240,
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {p.pattern}
                  </td>
                  <td><RiskBadge level={p.severity} /></td>
                  <td className="mono tnum" style={{ textAlign: "right" }}>{p.count.toLocaleString()}</td>
                  <td><Switch on={p.enabled} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>

        <Card title="Recent redactions" subtitle="Last 5 events · WORM logged">
          <div className="col" style={{ gap: 10 }}>
            {REDACT_RECENT.map((r, i) => (
              <div
                key={`${r.at}-${i}`}
                style={{
                  padding: 10,
                  background: "var(--bg-2)",
                  border: "1px solid var(--border)",
                  borderRadius: 6,
                }}
              >
                <div className="row" style={{ gap: 6, marginBottom: 4 }}>
                  <Badge tone="memory">{r.pattern}</Badge>
                  <span className="mono subtle" style={{ fontSize: 10.5 }}>{r.caller}</span>
                  <span className="subtle" style={{ marginLeft: "auto", fontSize: 10.5 }}>{r.at}</span>
                </div>
                <div
                  className="mono"
                  style={{
                    fontSize: 11,
                    color: "var(--fg-muted)",
                    textDecoration: "line-through",
                  }}
                >
                  {r.original}
                </div>
                <div
                  className="mono"
                  style={{ fontSize: 11, color: "var(--success)", marginTop: 2 }}
                >
                  → {r.redacted}
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
};

export default function RedactionPage(): JSX.Element {
  return (
    <RequireAuth>
      <AppShellV2 pageTitle="Redaction">
        <RedactionPageInner />
      </AppShellV2>
    </RequireAuth>
  );
}
