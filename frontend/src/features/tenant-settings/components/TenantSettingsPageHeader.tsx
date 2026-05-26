/**
 * File: frontend/src/features/tenant-settings/components/TenantSettingsPageHeader.tsx
 * Purpose: Verbatim port of mockup tenant-settings page header (title + sub line w/ mono + route-pill + plan badge).
 * Category: Frontend / tenant-settings / components
 * Scope: Phase 57 / Sprint 57.44 Day 1 (mockup-fidelity rebuild)
 *
 * Description:
 *   Verbatim port of mockup `page-admin.jsx` L416-425. Renders title "Tenant
 *   Settings" + sub line with mono display_name + route-pill code + plan badge
 *   "{plan} · {N} seats". `displayName` / `code` / `plan` are live from backend;
 *   seats count is SEATS_FIXTURE pending Phase 58+ backend member enumeration.
 *
 * Key Components:
 *   - TenantSettingsPageHeader: stateless visual header
 *
 * Created: 2026-05-26 (Sprint 57.44 Day 1)
 * Last Modified: 2026-05-26
 *
 * Modification History (newest-first):
 *   - 2026-05-26: Initial creation (Sprint 57.44 Day 1) — tenant-settings full mockup-fidelity rebuild
 *
 * Related:
 *   - reference/design-mockups/page-admin.jsx L416-425
 *   - frontend/src/components/mockup-ui.tsx (Badge primitive)
 *   - ../_fixtures.ts (SEATS_FIXTURE)
 */

import { Badge } from "../../../components/mockup-ui";
import { SEATS_FIXTURE } from "../_fixtures";

export interface TenantSettingsPageHeaderProps {
  displayName: string;
  code: string;
  plan: string;
}

export function TenantSettingsPageHeader({
  displayName,
  code,
  plan,
}: TenantSettingsPageHeaderProps): JSX.Element {
  return (
    <div className="page-head">
      <div>
        <div className="page-title">Tenant Settings</div>
        <div className="page-sub">
          {/* eslint-disable-next-line no-restricted-syntax -- verbatim port: mockup uses inline style for mono color/weight */}
          <span className="mono" style={{ color: "var(--fg)", fontWeight: 500 }}>{displayName}</span>
          <span className="route-pill">{code}</span>
          <Badge tone="primary">{plan} · {SEATS_FIXTURE} seats</Badge>
        </div>
      </div>
    </div>
  );
}
