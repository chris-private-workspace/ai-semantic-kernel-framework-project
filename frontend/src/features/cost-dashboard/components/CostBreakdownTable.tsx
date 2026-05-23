/**
 * File: frontend/src/features/cost-dashboard/components/CostBreakdownTable.tsx
 * Purpose: 2-level nested cost breakdown (cost_type → sub_type → AggregatedSlice) — production-only backend drill-down.
 * Category: Frontend / cost-dashboard / components
 * Scope: Phase 57 / Sprint 57.1 US-2 → 57.31 Day 1 (verbatim re-point to mockup .table vocabulary)
 *
 * Description:
 *   Iterates by_type 2-level dict per Day 0 D9 finding (NOT flat).
 *   Each row: cost_type / sub_type / quantity / total_cost_usd / entry_count.
 *
 *   Sprint 57.31 Day 1 verbatim re-point decision (c) production-only-by-design:
 *   no mockup equivalent (Day 0 D4 RED finding). This widget renders the REAL
 *   backend by_type drill-down (single-tenant, current month); distinct from
 *   the cross-tenant fixture TenantTopTable above. Re-pointed to mockup .table
 *   vocabulary (verbatim from styles.css .table rule) so the visual layer
 *   matches the rest of the cost-dashboard. NO AP-2 BackendGapBanner — this
 *   widget shows actual backend data, not a fixture; e2e contract proves it.
 *
 * Created: 2026-05-06 (Sprint 57.1 Day 1)
 * Last Modified: 2026-05-23
 *
 * Modification History (newest-first):
 *   - 2026-05-23: Sprint 57.31 Day 1 — verbatim re-point to mockup .table; decision (c) production-only-by-design (no AP-2 banner)
 *   - 2026-05-19: Sprint 57.24 Day 3 — add data-testid="cost-breakdown-table" for e2e selector scoping
 *   - 2026-05-11: Sprint 57.15 — inline styles → Tailwind utility classes; `#666`→text-muted-foreground (AD-Inline-Style-Cleanup-Sweep)
 *   - 2026-05-06: Initial creation (Sprint 57.1 Day 1 / US-2 — breakdown table)
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: inline-style literals for right-aligned columns are mockup styles.css .table visual-layer literals; STYLE.md §1 escape hatch + frontend-mockup-fidelity.md */

import type { CSSProperties } from "react";

import type { CostSummaryResponse } from "../types";

interface CostBreakdownTableProps {
  data: CostSummaryResponse;
}

const RIGHT: CSSProperties = { textAlign: "right" };

export function CostBreakdownTable({ data }: CostBreakdownTableProps) {
  const rows: Array<{
    costType: string;
    subType: string;
    quantity: string;
    totalCostUsd: string;
    entryCount: number;
  }> = [];

  for (const [costType, subTypeMap] of Object.entries(data.by_type)) {
    for (const [subType, slice] of Object.entries(subTypeMap)) {
      rows.push({
        costType,
        subType,
        quantity: slice.quantity,
        totalCostUsd: slice.total_cost_usd,
        entryCount: slice.entry_count,
      });
    }
  }

  if (rows.length === 0) {
    return (
      <p className="subtle" style={{ fontStyle: "italic" } satisfies CSSProperties}>
        No cost entries for this month.
      </p>
    );
  }

  return (
    <table className="table" data-testid="cost-breakdown-table">
      <thead>
        <tr>
          <th>Cost Type</th>
          <th>Sub Type</th>
          <th style={RIGHT}>Quantity</th>
          <th style={RIGHT}>Total (USD)</th>
          <th style={RIGHT}>Entries</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row, idx) => (
          <tr key={`${row.costType}-${row.subType}-${idx}`}>
            <td className="mono" style={{ fontSize: 12 } satisfies CSSProperties}>
              {row.costType}
            </td>
            <td className="mono" style={{ fontSize: 12 } satisfies CSSProperties}>
              {row.subType}
            </td>
            <td className="mono tnum" style={RIGHT}>
              {row.quantity}
            </td>
            <td className="mono tnum" style={RIGHT}>
              ${row.totalCostUsd}
            </td>
            <td className="mono tnum subtle" style={RIGHT}>
              {row.entryCount}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
