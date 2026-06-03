/**
 * File: frontend/src/features/admin-tenants/components/TenantsStatsStrip.tsx
 * Purpose: Admin tenants 4-stat strip wired to the real fleet stats aggregate (3 real stats + honest-gapped Anomalies/deltas).
 * Category: Frontend / admin-tenants / components
 * Scope: Phase 57 / Sprint 57.43 Day 1 (mockup-fidelity rebuild) → Sprint 57.74 (real-data wiring)
 *
 * Description:
 *   Verbatim port of mockup `page-admin.jsx` L350-355 — 4 Stat primitives in
 *   a `.grid-stats` container. Sprint 57.74 (A-6a) wires the strip to the real
 *   GET /api/v1/admin/tenants/stats fleet aggregate via a `fleet` prop:
 *     - Active tenants ← fleet.active_tenants  (REAL, number-formatted)
 *     - Total seats    ← fleet.total_seats     (REAL)
 *     - Agents deployed ← fleet.agents_deployed (REAL)
 *     - Anomalies      → subtle "—" placeholder (no backend source; never a
 *                        fabricated number)
 *   Every stat's trend delta / arrow is OMITTED (no historical/period source)
 *   — the Stat primitive renders no arrow when `delta` is undefined. An AP-2
 *   BackendGapBanner names the gapped bits (Anomalies + trend deltas).
 *   Loading / error states are MOCKUP-NATIVE (subtle "···" / "—" in the same
 *   .grid-stats markup), NOT a shadcn skeleton (keeps this verbatim-mockup
 *   page residue-free — same D8/D10 rule as TenantsTable).
 *
 * Key Components:
 *   - TenantsStatsStrip: prop-driven visual stats grid (real fleet data + states)
 *
 * Created: 2026-05-25 (Sprint 57.43 Day 1)
 * Last Modified: 2026-06-03
 *
 * Modification History (newest-first):
 *   - 2026-06-03: Sprint 57.74 — take fleet prop, 3 real stats, Anomalies + deltas honest-gapped, mockup-native states (A-6a)
 *   - 2026-06-03: Sprint 57.73 — add BackendGapBanner (no aggregate-stats endpoint; stats stay placeholder) (A-6a)
 *   - 2026-05-25: Initial creation (Sprint 57.43 Day 1) — admin-tenants full mockup-fidelity rebuild
 *
 * Related:
 *   - reference/design-mockups/page-admin.jsx L350-355
 *   - frontend/src/features/admin-tenants/hooks/useAdminTenantsStats.ts (fleet source)
 *   - frontend/src/components/mockup-ui.tsx (Stat primitive)
 *   - frontend/src/components/ui/BackendGapBanner.tsx (AP-2 honesty banner)
 */

/* eslint-disable no-restricted-syntax -- subtle gap-placeholder spans reuse the mockup --fg-subtle/--danger token literals (Anomalies "—" + loading "···" + error); STYLE.md §3 escape hatch + frontend-mockup-fidelity.md verbatim-CSS method */

import { Stat } from "../../../components/mockup-ui";
import { BackendGapBanner } from "../../../components/ui/BackendGapBanner";
import type { FleetStats } from "../types";

// Subtle "—" placeholder for the un-backable Anomalies stat — rendered as the
// stat value instead of a fabricated number (AP-2 honesty / user-locked gap).
const ANOMALIES_GAP = <span style={{ color: "var(--fg-subtle)" }}>—</span>;

export interface TenantsStatsStripProps {
  /** Real fleet aggregate from GET /api/v1/admin/tenants/stats (Sprint 57.74). */
  fleet?: FleetStats;
  /** TanStack query loading flag (shows subtle "···" stat values). */
  isLoading?: boolean;
  /** TanStack query error flag (shows subtle error placeholders). */
  isError?: boolean;
}

export function TenantsStatsStrip({
  fleet,
  isLoading = false,
  isError = false,
}: TenantsStatsStripProps): JSX.Element {
  // Mockup-native loading / error placeholder for the 3 real value slots.
  // Trend deltas are always omitted (no historical source — honest gap).
  const loadingValue = <span style={{ color: "var(--fg-subtle)" }}>···</span>;
  const errorValue = <span style={{ color: "var(--danger)" }}>—</span>;

  // Resolve each real stat value: error → subtle "—"; loading → "···";
  // success → the number-formatted fleet count.
  const realValue = (n: number | undefined): JSX.Element | string => {
    if (isError) return errorValue;
    if (isLoading || n === undefined) return loadingValue;
    return n.toLocaleString();
  };

  return (
    <div>
      <div className="grid-stats">
        <Stat label="Active tenants" value={realValue(fleet?.active_tenants)} />
        <Stat label="Total seats" value={realValue(fleet?.total_seats)} />
        <Stat label="Agents deployed" value={realValue(fleet?.agents_deployed)} />
        <Stat label="Anomalies" value={ANOMALIES_GAP} />
      </div>
      <BackendGapBanner reason="Anomalies stat + per-stat trend deltas have no backend source — Active tenants / Total seats / Agents deployed are now real GET /api/v1/admin/tenants/stats data; see AD-AdminTenants-Anomalies-Stat-Backend + AD-AdminTenants-Stats-Trend-Deltas" />
    </div>
  );
}
