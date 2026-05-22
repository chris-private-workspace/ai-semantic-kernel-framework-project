/**
 * File: frontend/src/components/topbar/CommandPalette.tsx
 * Purpose: ⌘K command palette — fuzzy search over ROUTES + quick actions + tenant + session shortcuts.
 * Category: Frontend / components / topbar (Cat 12 cross-cutting UX)
 * Scope: Phase 57 / Sprint 57.19 Day 5 / US-D1
 *
 * Description:
 *   Verbatim re-point of `reference/design-mockups/topbar-overlays.jsx` CommandPalette.
 *   The palette shell (backdrop + card) now uses verbatim inline-style literals from
 *   the mockup. The cmdk / Radix Dialog interaction layer is kept unchanged:
 *   `<Dialog>` / `<DialogContent>` / `<DialogTitle className="sr-only">` /
 *   `<Command>` / `<Command.Input>` / `<Command.List>` / `<Command.Group>` /
 *   `<Command.Item>` / `<Command.Empty>` — only the rendered markup's wrapper
 *   class names and inline-style objects are re-pointed to the mockup literals.
 *
 *   Groups (filtered by query):
 *     - Actions (4 fixed: new chat / review HITL / onboard tenant / declare incident)
 *     - Pages (top 8 ROUTES matched by id / nameKey label / path)
 *     - Tenants (3 mockup fixtures — surfaced when query non-empty)
 *     - Sessions (3 mockup fixtures — surfaced when query starts with sess/s_/hex chars)
 *
 *   Keyboard: ↑↓ navigate, Enter open, Esc close. cmdk provides natively.
 *
 * Created: 2026-05-17 (Sprint 57.19 Day 5 / US-D1)
 * Last Modified: 2026-05-22
 *
 * Modification History:
 *   - 2026-05-22: Sprint 57.29 US-B4 — verbatim re-point palette shell to mockup topbar-overlays.jsx literals
 *   - 2026-05-17: Initial creation (Sprint 57.19 Day 5 / US-D1) — mockup port + cmdk integration
 *
 * Related:
 *   - reference/design-mockups/topbar-overlays.jsx §CommandPalette (canonical visual source)
 *   - reference/design-mockups/styles.css / frontend/src/styles-mockup.css (.kbd class)
 *   - frontend/src/components/AppShellV2.tsx (mounts CommandPalette + ⌘K hotkey)
 *   - frontend/src/routes.config.ts (ROUTES source for page group)
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: inline styles are mockup topbar-overlays.jsx visual-layer literals (backdrop, card shell, input row, group heading, result row, footer row) copied byte-for-byte; re-expressing as Tailwind IS the drift bug this epic kills (STYLE.md §1 escape hatch + frontend-mockup-fidelity.md) */

import { Command } from "cmdk";
import { type CSSProperties, type FC, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { Icon } from "@/components/mockup-ui";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui";
import { ROUTES } from "@/routes.config";

// ─── Verbatim mockup topbar-overlays.jsx inline-style literals ───────────────

// Input row
const INPUT_ROW_STYLE: CSSProperties = {
  gap: 10, padding: "12px 14px", borderBottom: "1px solid var(--border)",
};

// Input element
const INPUT_STYLE: CSSProperties = {
  flex: 1, background: "transparent", border: "none", outline: "none",
  color: "var(--fg)", fontSize: 14, fontFamily: "var(--font-sans)",
};

// Results scroll area
const RESULTS_STYLE: CSSProperties = { overflowY: "auto", padding: 4 };

// Empty state
const EMPTY_STYLE: CSSProperties = {
  gap: 6, alignItems: "center", padding: "32px 0", color: "var(--fg-subtle)",
};

// Group heading
const GROUP_HEADING_STYLE: CSSProperties = {
  padding: "8px 12px 4px",
  fontSize: 10, color: "var(--fg-subtle)", textTransform: "uppercase",
  letterSpacing: "0.06em", fontFamily: "var(--font-mono)",
};

// Result row (base; active variant adds bg)
const resultRowStyle = (active: boolean): CSSProperties => ({
  gap: 10, padding: "8px 12px", borderRadius: 6,
  background: active ? "var(--bg-hover)" : "transparent",
  cursor: "pointer", fontSize: 13,
});

// Footer row
const FOOTER_STYLE: CSSProperties = {
  gap: 14, padding: "8px 14px", borderTop: "1px solid var(--border)",
  fontSize: 10.5, color: "var(--fg-subtle)", fontFamily: "var(--font-mono)",
};

// ─────────────────────────────────────────────────────────────────────────────

interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface CmdItem {
  type: string;
  id: string;
  icon: string;
  label: string;
  hint: string;
  routeId: string;
}

const EXTRA_ACTIONS: CmdItem[] = [
  { type: "action", id: "act-new-chat",  icon: "chat",     label: "topbar.commandPalette.actions.newChat",       hint: "topbar.commandPalette.actions.newChatHint",       routeId: "chat-v2" },
  { type: "action", id: "act-review",    icon: "approval", label: "topbar.commandPalette.actions.reviewHitl",    hint: "topbar.commandPalette.actions.reviewHitlHint",    routeId: "governance" },
  { type: "action", id: "act-onboard",   icon: "plus",     label: "topbar.commandPalette.actions.onboardTenant", hint: "topbar.commandPalette.actions.onboardTenantHint", routeId: "tenant-onboarding" },
  { type: "action", id: "act-incident",  icon: "warn",     label: "topbar.commandPalette.actions.declareIncident", hint: "topbar.commandPalette.actions.declareIncidentHint", routeId: "incidents" },
];

const TENANT_FIXTURES = [
  { id: "t1", name: "acme-prod",  region: "ap-east-1",      plan: "Pro" },
  { id: "t2", name: "globex-eu",  region: "eu-west-1",      plan: "Pro" },
  { id: "t3", name: "initech-jp", region: "ap-northeast-1", plan: "Enterprise" },
];

const SESSION_FIXTURES = [
  { id: "sess_8a2f1c3", agent: "incident-responder", tenant: "acme-prod",  status: "running" },
  { id: "sess_7c11d9e", agent: "compliance-auditor", tenant: "globex-eu",  status: "hitl-paused" },
  { id: "sess_4f88c1a", agent: "rca-explorer",       tenant: "acme-prod",  status: "verifying" },
];

export const CommandPalette: FC<CommandPaletteProps> = ({ open, onOpenChange }) => {
  const { t } = useTranslation("common");
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [activeIdx, setActiveIdx] = useState(0);

  useEffect(() => {
    if (!open) { setQuery(""); setActiveIdx(0); }
  }, [open]);

  const lower = query.trim().toLowerCase();
  const matchesQuery = (s: string): boolean => lower === "" || s.toLowerCase().includes(lower);

  const goRoute = (routeId: string): void => {
    const route = ROUTES.find((r) => r.path.endsWith(routeId) || r.path.slice(1) === routeId);
    if (route) navigate(route.path);
    onOpenChange(false);
  };

  const matchedPages: CmdItem[] = ROUTES
    .filter((r) => r.active)
    .filter((r) => matchesQuery(r.path) || matchesQuery(t(r.nameKey)) || matchesQuery(r.name))
    .slice(0, 8)
    .map((r) => ({ type: "page", id: `pg-${r.path}`, icon: "dashboard", label: t(r.nameKey), hint: r.path, routeId: r.path.slice(1) }));

  const matchedActions: CmdItem[] = EXTRA_ACTIONS
    .filter((a) => matchesQuery(t(a.label)) || matchesQuery(t(a.hint)))
    .map((a) => ({ ...a, label: t(a.label), hint: t(a.hint) }));

  const matchedTenants: CmdItem[] = lower
    ? TENANT_FIXTURES.filter((tn) => matchesQuery(tn.name)).map((tn) => ({
        type: "tenant", id: `tn-${tn.id}`, icon: "tenants", label: tn.name, hint: `${tn.region} · ${tn.plan}`, routeId: "admin-tenants",
      }))
    : [];

  const matchedSessions: CmdItem[] = lower && /^(sess|s_|[a-f0-9]{2,})/i.test(lower)
    ? SESSION_FIXTURES.filter((s) => s.id.toLowerCase().includes(lower)).map((s) => ({
        type: "session", id: `ss-${s.id}`, icon: "loop", label: s.id, hint: `${s.agent} · ${s.status}`, routeId: "loop-debug",
      }))
    : [];

  const groups = [
    { label: t("topbar.commandPalette.groups.actions"),  items: matchedActions },
    { label: t("topbar.commandPalette.groups.pages"),    items: matchedPages },
    { label: t("topbar.commandPalette.groups.tenants"),  items: matchedTenants },
    { label: t("topbar.commandPalette.groups.sessions"), items: matchedSessions },
  ].filter((g) => g.items.length > 0);

  const flat = groups.flatMap((g) => g.items);
  const totalCount = flat.length;

  const onKey = (e: React.KeyboardEvent): void => {
    if (e.key === "ArrowDown") { e.preventDefault(); setActiveIdx((i) => Math.min(flat.length - 1, i + 1)); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setActiveIdx((i) => Math.max(0, i - 1)); }
    else if (e.key === "Enter") { e.preventDefault(); if (flat[activeIdx]) goRoute(flat[activeIdx].routeId); }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="overflow-hidden p-0 sm:max-w-xl">
        <DialogTitle className="sr-only">{t("topbar.commandPalette.title")}</DialogTitle>
        <Command shouldFilter={false}>
          {/* Input row — verbatim mockup structure */}
          <div className="row" style={INPUT_ROW_STYLE}>
            <Icon name="search" size={15} className="subtle" />
            <Command.Input
              value={query}
              onValueChange={(v) => { setQuery(v); setActiveIdx(0); }}
              onKeyDown={onKey}
              placeholder={t("topbar.commandPalette.placeholder")}
              style={INPUT_STYLE}
              // eslint-disable-next-line jsx-a11y/no-autofocus -- modal dialog first-input autofocus is the a11y-correct pattern (per mockup parity + WCAG 2.4.3)
              autoFocus
            />
            <span className="kbd" style={{ fontSize: 10 }}>ESC</span>
          </div>

          {/* Results */}
          <Command.List style={RESULTS_STYLE}>
            {totalCount === 0 ? (
              <Command.Empty>
                <div className="col" style={EMPTY_STYLE}>
                  <Icon name="search" size={20} />
                  <div style={{ fontSize: 12.5 }}>{t("topbar.commandPalette.empty")}</div>
                </div>
              </Command.Empty>
            ) : (
              groups.map((g) => (
                <Command.Group key={g.label}>
                  <div style={GROUP_HEADING_STYLE}>{g.label}</div>
                  {g.items.map((item) => {
                    const idx = flat.indexOf(item);
                    const active = idx === activeIdx;
                    return (
                      <Command.Item
                        key={item.id}
                        value={item.id}
                        onSelect={() => goRoute(item.routeId)}
                        onMouseEnter={() => setActiveIdx(idx)}
                      >
                        <div className="row" style={resultRowStyle(active)}>
                          <Icon name={item.icon as Parameters<typeof Icon>[0]["name"]} size={14} className="subtle" />
                          <span style={{ flex: 1 }}>{item.label}</span>
                          <span className="mono subtle" style={{ fontSize: 11 }}>{item.hint}</span>
                          {active && <Icon name="arrow_right" size={11} className="subtle" />}
                        </div>
                      </Command.Item>
                    );
                  })}
                </Command.Group>
              ))
            )}
          </Command.List>

          {/* Footer */}
          <div className="row" style={FOOTER_STYLE}>
            <span><span className="kbd" style={{ fontSize: 9 }}>↑↓</span> {t("topbar.commandPalette.footer.navigate")}</span>
            <span><span className="kbd" style={{ fontSize: 9 }}>↵</span> {t("topbar.commandPalette.footer.open")}</span>
            <span><span className="kbd" style={{ fontSize: 9 }}>ESC</span> {t("topbar.commandPalette.footer.close")}</span>
            <span style={{ flex: 1 }} />
            <span>{totalCount} {t("topbar.commandPalette.footer.results")}</span>
          </div>
        </Command>
      </DialogContent>
    </Dialog>
  );
};
