/**
 * File: frontend/src/components/ui/BackendGapBanner.tsx
 * Purpose: Warning-tone banner declaring backend-gap fixtures per AP-2 honesty.
 * Category: Frontend / components / ui (design-system layer)
 * Scope: Phase 57 / Sprint 57.24 Day 1 US-B3 (used wherever mockup widget renders fixture data)
 *
 * Description:
 *   Per CLAUDE.md §Frontend Mockup-Fidelity Hard Constraint + .claude/rules/
 *   anti-patterns-checklist.md AP-2 (no Potemkin): when a widget ships with
 *   fixture data because the backend API is not yet implemented, the widget
 *   MUST visibly mark itself as fixture / pending so reviewers + operators
 *   aren't misled by mock-looking real data.
 *
 *   Used by Sprint 57.24 Day 1.3 30d AreaChart + Day 2 TenantTopTable /
 *   ProviderMixCard. Reusable for all Sprint 57.25-57.28 backend-gap widgets.
 *
 * Created: 2026-05-19 (Sprint 57.24 Day 1 US-B3)
 *
 * Modification History (newest-first):
 *   - 2026-05-19: Initial creation (Sprint 57.24 Day 1 US-B3)
 */

import type { FC } from "react";

export interface BackendGapBannerProps {
  reason: string;
}

export const BackendGapBanner: FC<BackendGapBannerProps> = ({ reason }) => (
  <div
    role="note"
    data-testid="backend-gap-banner"
    className="mt-2 rounded-md border border-warning/40 bg-warning/5 px-3 py-2 text-xs text-warning"
  >
    <span aria-hidden>⚠️ </span>
    {reason}
  </div>
);
