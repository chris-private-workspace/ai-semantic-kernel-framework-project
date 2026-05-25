/**
 * File: frontend/src/features/admin-tenants/components/TenantsStatsStrip.tsx
 * Purpose: Verbatim port of admin tenants 4-stat strip (Active tenants / Total seats / Agents / Anomalies).
 * Category: Frontend / admin-tenants / components
 * Scope: Phase 57 / Sprint 57.43 Day 1 (mockup-fidelity rebuild)
 *
 * Description:
 *   Verbatim port of mockup `page-admin.jsx` L350-355 — 4 Stat primitives in
 *   a `.grid-stats` container. Data from STATS_FIXTURE (Option A fixture-first
 *   per D-DAY0-6). Reuses Stat primitive from mockup-ui.tsx.
 *
 * Key Components:
 *   - TenantsStatsStrip: stateless visual stats grid
 *
 * Created: 2026-05-25 (Sprint 57.43 Day 1)
 * Last Modified: 2026-05-25
 *
 * Modification History (newest-first):
 *   - 2026-05-25: Initial creation (Sprint 57.43 Day 1) — admin-tenants full mockup-fidelity rebuild
 *
 * Related:
 *   - reference/design-mockups/page-admin.jsx L350-355
 *   - frontend/src/features/admin-tenants/_fixtures.ts (STATS_FIXTURE)
 *   - frontend/src/components/mockup-ui.tsx (Stat primitive)
 */

import { Stat } from "../../../components/mockup-ui";
import { STATS_FIXTURE } from "../_fixtures";

export function TenantsStatsStrip(): JSX.Element {
  return (
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
  );
}
