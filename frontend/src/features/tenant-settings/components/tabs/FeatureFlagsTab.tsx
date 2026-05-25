/**
 * File: frontend/src/features/tenant-settings/components/tabs/FeatureFlagsTab.tsx
 * Purpose: Feature flags tab — table of 8 tenant-scoped flag overrides (mockup verbatim).
 * Category: Frontend / tenant-settings / components / tabs
 * Scope: Phase 57 / Sprint 57.44 Day 1 (mockup-fidelity rebuild — D-DAY0-4 Option A)
 *
 * Description:
 *   Verbatim port of mockup `page-admin.jsx` L476-505. Single Card with 4-col
 *   table (Flag / Description / Default / Tenant override). Boolean flags render
 *   <Switch>; numeric flags (`ctl === "num"`) render mono <input>. All flag
 *   values are read-only display fixtures pending Phase 58+ backend.
 *
 * Created: 2026-05-26 (Sprint 57.44 Day 1)
 * Last Modified: 2026-05-26
 *
 * Modification History (newest-first):
 *   - 2026-05-26: Initial creation (Sprint 57.44 Day 1) — tenant-settings full mockup-fidelity rebuild
 *
 * Related:
 *   - reference/design-mockups/page-admin.jsx L476-505
 *   - ../../_fixtures.ts (FEATURE_FLAGS)
 */

import { Badge, Card, Switch } from "../../../../components/mockup-ui";
import { BackendGapBanner } from "../../../../components/ui/BackendGapBanner";
import { FEATURE_FLAGS } from "../../_fixtures";

export function FeatureFlagsTab(): JSX.Element {
  return (
    <Card title="Feature flags" subtitle="Tenant-scoped overrides">
      <BackendGapBanner reason="Feature flag overrides: backend extension Phase 58+ — values shown are mockup defaults" />
      <table className="table">
        <thead>
          <tr>
            <th>Flag</th>
            <th>Description</th>
            <th>Default</th>
            <th>Tenant override</th>
          </tr>
        </thead>
        <tbody>
          {FEATURE_FLAGS.map((f) => (
            <tr key={f.k}>
              {/* eslint-disable-next-line no-restricted-syntax -- verbatim port: mono fontSize */}
              <td className="mono" style={{ fontSize: 12 }}>{f.k}</td>
              {/* eslint-disable-next-line no-restricted-syntax -- verbatim port: subtle fontSize */}
              <td className="subtle" style={{ fontSize: 12 }}>{f.desc}</td>
              <td><Badge>{f.def}</Badge></td>
              <td>
                {f.ctl === "num" ? (
                  // eslint-disable-next-line no-restricted-syntax -- verbatim port: input width + fontSize
                  <input className="input mono" style={{ width: 80, fontSize: 12 }} defaultValue={String(f.on)} />
                ) : (
                  <Switch on={Boolean(f.on)} />
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}
