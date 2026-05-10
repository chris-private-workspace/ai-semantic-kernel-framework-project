/**
 * File: frontend/src/components/ui/empty-state.tsx
 * Purpose: <EmptyState> — centered "no data / no matches" panel with an optional action.
 * Category: Frontend / components / ui (design-system layer; Sprint 57.13 US-B2)
 * Scope: Phase 57 / Sprint 57.13 US-B2
 *
 * Description:
 *   Canonicalises STYLE.md §7. Render when a query returns 0 items. `title` is
 *   the headline ("No approvals match your filters."), `message` an optional
 *   secondary line, `icon` an optional element (e.g. a lucide icon), `action`
 *   an optional element (typically <Button variant="outline">Reset Filters</Button>).
 *   Always give the user a next step — bare "<p>No data</p>" is the anti-pattern
 *   STYLE.md §7 calls out.
 *
 * Created: 2026-05-10 (Sprint 57.13 Day 4)
 *
 * Related:
 *   - STYLE.md §7 (Empty State Pattern — canonical layout)
 *   - frontend/src/components/ui/button.tsx (typical `action` element)
 */

import type { FC, ReactNode } from "react";

import { cn } from "../../lib/utils";

export interface EmptyStateProps {
  title: string;
  message?: string;
  icon?: ReactNode;
  action?: ReactNode;
  className?: string;
}

export const EmptyState: FC<EmptyStateProps> = ({ title, message, icon, action, className }) => (
  <div className={cn("flex flex-col items-center justify-center py-12 text-center", className)}>
    {icon && <div className="mb-3 text-muted-foreground">{icon}</div>}
    <p className="mb-1 text-sm font-medium text-foreground">{title}</p>
    {message && <p className="mb-4 text-sm text-muted-foreground">{message}</p>}
    {action}
  </div>
);
