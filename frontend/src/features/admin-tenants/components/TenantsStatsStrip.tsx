/**
 * File: frontend/src/features/admin-tenants/components/TenantsStatsStrip.tsx
 * Purpose: Verbatim port of admin tenants 4-stat strip (Active tenants / Total seats / Agents / Anomalies).
 * Category: Frontend / admin-tenants / components
 * Scope: Phase 57 / Sprint 57.43 Day 1 (mockup-fidelity rebuild)
 *
 * Description:
 *   Verbatim port of mockup `page-admin.jsx` L350-355 — 4 Stat primitives in
 *   a `.grid-stats` container. Data stays on STATS_FIXTURE: there is NO
 *   aggregate-stats endpoint (the list endpoint returns per-tenant rows only),
 *   so the strip marks itself placeholder via AP-2 BackendGapBanner (Sprint
 *   57.73). Reuses Stat primitive from mockup-ui.tsx.
 *
 * Key Components:
 *   - TenantsStatsStrip: stateless visual stats grid (placeholder data)
 *
 * Created: 2026-05-25 (Sprint 57.43 Day 1)
 * Last Modified: 2026-06-03
 *
 * Modification History (newest-first):
 *   - 2026-06-03: Sprint 57.73 — add BackendGapBanner (no aggregate-stats endpoint; stats stay placeholder) (A-6a)
 *   - 2026-05-25: Initial creation (Sprint 57.43 Day 1) — admin-tenants full mockup-fidelity rebuild
 *
 * Related:
 *   - reference/design-mockups/page-admin.jsx L350-355
 *   - frontend/src/features/admin-tenants/_fixtures.ts (STATS_FIXTURE)
 *   - frontend/src/components/mockup-ui.tsx (Stat primitive)
 *   - frontend/src/components/ui/BackendGapBanner.tsx (AP-2 honesty banner)
 */

import { Stat } from "../../../components/mockup-ui";
import { BackendGapBanner } from "../../../components/ui/BackendGapBanner";
import { STATS_FIXTURE } from "../_fixtures";

export function TenantsStatsStrip(): JSX.Element {
  return (
    <div>
      <div className="grid-stats">
        {STATS_FIXTURE.map((s) => (
          <Stat
            key={s.label}
            label={s.label}
            value={s.value}
            delta={s.delta}
            deltaDir={s.deltaDir}
          />
        ))}
      </div>
      <BackendGapBanner reason="Stats strip (Active tenants / Total seats / Agents deployed / Anomalies) is placeholder — no aggregate-stats endpoint yet; see AD-AdminTenants-Backend-Schema-Extension" />
    </div>
  );
}
