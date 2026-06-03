/* eslint-disable no-restricted-syntax -- mockup verbatim CSS literals + per-cell font-size + max-width clamp; mockup-fidelity (Sprint 57.42). See reference/design-mockups/page-governance.jsx L557-579. */
/**
 * File: frontend/src/features/memory/components/RecentMemoryOpsCard.tsx
 * Purpose: Recent memory ops sidebar Card — 6-col table (Op / Scope / Key / Value / By / When) with 5 fixture rows + AP-2 banner.
 * Category: Frontend / memory / components
 * Scope: Phase 57 / Sprint 57.42 Day 1 (mockup-fidelity rebuild)
 *
 * Description:
 *   Verbatim port of `reference/design-mockups/page-governance.jsx:557-579`
 *   (Recent memory ops Card). Subtitle "Live · last 100"; bodyClass "flush";
 *   actions "View all" ghost Button. Table is 6-col:
 *     - Op: Badge tone="memory" (WRITE / READ / EXPIRE)
 *     - Scope: mono fontSize 11
 *     - Key: mono fontSize 11.5
 *     - Value: subtle mono fontSize 11, maxWidth 240 with ellipsis
 *     - By: mono fontSize 11 var(--fg-muted)
 *     - When: subtle fontSize 11
 *
 *   AP-2 fixture (5 rows hand-ported from mockup inline table at L561-566).
 *   BackendGapBanner declared inside Card for deferred ops timeline endpoint.
 *
 * Key Components:
 *   - RecentMemoryOpsCard: stateless functional component, no props (pure fixture)
 *
 * Created: 2026-05-25 (Sprint 57.42 Day 1)
 * Last Modified: 2026-06-03
 *
 * Modification History (newest-first):
 *   - 2026-06-03: Sprint 57.73 Track C — reword AP-2 banner to deferred ops-history feature (no backend producer)
 *   - 2026-05-25: Initial creation (Sprint 57.42 Day 1) — memory matrix full mockup-fidelity rebuild
 *
 * Related:
 *   - reference/design-mockups/page-governance.jsx L557-579
 *   - ../_fixtures.ts (RECENT_MEMORY_OPS)
 *   - ../../../components/mockup-ui.tsx (Card + Badge + Button primitives)
 *   - ../../../components/ui/BackendGapBanner.tsx (AP-2 declaration)
 */

import { Badge, Button, Card } from "../../../components/mockup-ui";
import { BackendGapBanner } from "../../../components/ui/BackendGapBanner";
import { RECENT_MEMORY_OPS } from "../_fixtures";

export function RecentMemoryOpsCard(): JSX.Element {
  return (
    <Card
      title="Recent memory ops"
      subtitle="Live · last 100"
      bodyClass="flush"
      actions={
        <Button variant="ghost" size="sm">
          View all
        </Button>
      }
    >
      <table className="table">
        <thead>
          <tr>
            <th>Op</th>
            <th>Scope</th>
            <th>Key</th>
            <th>Value</th>
            <th>By</th>
            <th>When</th>
          </tr>
        </thead>
        <tbody>
          {RECENT_MEMORY_OPS.map((m, i) => (
            <tr key={i}>
              <td>
                <Badge tone="memory">{m.op}</Badge>
              </td>
              <td className="mono" style={{ fontSize: 11 }}>
                {m.scope}
              </td>
              <td className="mono" style={{ fontSize: 11.5 }}>
                {m.k}
              </td>
              <td
                className="subtle mono"
                style={{
                  fontSize: 11,
                  maxWidth: 240,
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
              >
                {m.v}
              </td>
              <td className="mono" style={{ fontSize: 11, color: "var(--fg-muted)" }}>
                {m.by}
              </td>
              <td className="subtle" style={{ fontSize: 11 }}>
                {m.at}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <BackendGapBanner reason="Memory operation history (per-op audit / version log) is a deferred backend feature — see AD-Memory-OpsHistory-Backend. Memory writes currently emit zero audit rows; rows below are fixtures." />
    </Card>
  );
}
