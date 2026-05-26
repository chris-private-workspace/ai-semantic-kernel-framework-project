/**
 * File: frontend/src/features/tenant-settings/components/tabs/DangerZoneTab.tsx
 * Purpose: Danger zone tab — 4 destructive operation boxes (mockup verbatim).
 * Category: Frontend / tenant-settings / components / tabs
 * Scope: Phase 57 / Sprint 57.44 Day 1 (mockup-fidelity rebuild — D-DAY0-4 Option A)
 *
 * Description:
 *   Verbatim port of mockup `page-admin.jsx` L603-620. Single Card "Danger zone"
 *   actions={null} containing 4 sub-boxes each w/ danger-tone left-border +
 *   title + description + danger Button. Operations: Suspend tenant / Rotate
 *   API keys / Tombstone PII / Delete tenant.
 *
 *   No BackendGapBanner — these operations are intentionally disabled-by-design
 *   AP-2 stubs (window.alert); the entire tab is the gap declaration. Per Phase
 *   58+ backend will wire these endpoints.
 *
 * Created: 2026-05-26 (Sprint 57.44 Day 1)
 * Last Modified: 2026-05-26
 *
 * Modification History (newest-first):
 *   - 2026-05-26: Initial creation (Sprint 57.44 Day 1) — tenant-settings full mockup-fidelity rebuild
 *
 * Related:
 *   - reference/design-mockups/page-admin.jsx L603-620
 *   - ../../_fixtures.ts (DANGER_OPS)
 */

import { Button, Card } from "../../../../components/mockup-ui";
import { DANGER_OPS } from "../../_fixtures";

export function DangerZoneTab(): JSX.Element {
  const handleDangerOp = (label: string): void => {
    window.alert(`${label}: backend gap (Phase 58+) — destructive operation endpoint pending`);
  };

  return (
    <Card title="Danger zone" actions={null}>
      {/* eslint-disable-next-line no-restricted-syntax -- verbatim port: col gap + maxWidth */}
      <div className="col" style={{ gap: 20, maxWidth: 540 }}>
        {DANGER_OPS.map((z) => (
          <div
            key={z.k}
            // eslint-disable-next-line no-restricted-syntax -- verbatim port: danger left-border box layout
            style={{
              padding: 14,
              border: "1px solid var(--border)",
              borderLeft: `2px solid var(--danger)`,
              borderRadius: "var(--radius)",
            }}
          >
            {/* eslint-disable-next-line no-restricted-syntax -- verbatim port: title fontSize + weight */}
            <div style={{ fontWeight: 500, fontSize: 13, marginBottom: 4 }}>{z.k}</div>
            {/* eslint-disable-next-line no-restricted-syntax -- verbatim port: muted description fontSize */}
            <div className="muted" style={{ fontSize: 12, marginBottom: 10 }}>{z.v}</div>
            <Button variant="danger" size="sm" onClick={() => handleDangerOp(z.btn)}>
              {z.btn}
            </Button>
          </div>
        ))}
      </div>
    </Card>
  );
}
