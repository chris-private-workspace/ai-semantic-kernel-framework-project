/**
 * File: frontend/src/components/ui/CardShell.tsx
 * Purpose: Reusable mockup-fidelity card shell (title + subtitle + actions + body slot).
 * Category: Frontend / components / ui (design-system layer)
 * Scope: Phase 57 / Sprint 57.24 Day 1 US-B3 (1st consumer: /cost-dashboard widget cards)
 *
 * Description:
 *   Mockup-direct port of inline Card helper pattern established by
 *   Sprint 57.20 OverviewPage.tsx (page-overview.jsx canonical Card).
 *
 *   API matches mockup Card({ title, subtitle, actions, bodyClass, children }):
 *   - Header row (title + optional subtitle + optional actions) renders only
 *     when title or actions present
 *   - Body uses `bodyClass` override or default `p-4` padding
 *
 *   Tailwind tokens (Sprint 57.18 wired):
 *   - rounded-[12px] / border border-border / bg-bg-1 / text-foreground
 *   - Header: border-b border-border / px-4 py-3
 *   - Title: text-sm font-semibold; subtitle: text-[11px] text-fg-muted
 *
 *   Planned reuse: Sprint 57.24 Day 2 (CategoryBarsCard / TenantTopTable /
 *   ProviderMixCard wrap CardShell) + Sprint 57.25-57.28 dashboards.
 *
 * Created: 2026-05-19 (Sprint 57.24 Day 1 US-B3)
 * Last Modified: 2026-05-21
 *
 * Modification History (newest-first):
 *   - 2026-05-21: Sprint 57.27 Day 3 — card-title text-sm → text-[12.5px] (R9 / closes D8 toward mockup .card-title)
 *   - 2026-05-19: Initial creation (Sprint 57.24 Day 1 US-B3) — 1st consumer cost-dashboard
 *
 * Related:
 *   - frontend/src/pages/overview/OverviewPage.tsx (Sprint 57.20 inline Card pattern reference)
 *   - reference/design-mockups/page-overview.jsx (Card canonical mockup)
 */

import type { FC, ReactNode } from "react";

export interface CardShellProps {
  title?: ReactNode;
  subtitle?: ReactNode;
  actions?: ReactNode;
  bodyClass?: string;
  children: ReactNode;
}

export const CardShell: FC<CardShellProps> = ({
  title,
  subtitle,
  actions,
  bodyClass,
  children,
}) => (
  <div
    data-testid="card-shell"
    className="rounded-[12px] border border-border bg-bg-1 text-foreground"
  >
    {(title || actions) && (
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <div>
          {title && <div className="text-[12.5px] font-semibold">{title}</div>}
          {subtitle && <div className="text-[11px] text-fg-muted">{subtitle}</div>}
        </div>
        {actions}
      </div>
    )}
    <div className={bodyClass ?? "p-4"}>{children}</div>
  </div>
);
