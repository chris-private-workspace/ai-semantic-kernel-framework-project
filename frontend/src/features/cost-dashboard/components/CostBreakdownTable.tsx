/**
 * File: frontend/src/features/cost-dashboard/components/CostBreakdownTable.tsx
 * Purpose: Render 2-level nested cost breakdown (cost_type → sub_type → AggregatedSlice).
 * Category: Frontend / cost-dashboard / components
 * Scope: Phase 57 / Sprint 57.1 US-2
 *
 * Description:
 *   Iterates by_type 2-level dict per Day 0 D9 finding (NOT flat).
 *   Each row: cost_type / sub_type / quantity / total_cost_usd / entry_count.
 *
 * Created: 2026-05-06 (Sprint 57.1 Day 1)
 * Last Modified: 2026-05-11
 *
 * Modification History (newest-first):
 *   - 2026-05-11: Sprint 57.15 — inline styles → Tailwind utility classes; `#666`→text-muted-foreground (AD-Inline-Style-Cleanup-Sweep)
 *   - 2026-05-06: Initial creation (Sprint 57.1 Day 1 / US-2 — breakdown table)
 */

import type { CostSummaryResponse } from "../types";

interface CostBreakdownTableProps {
  data: CostSummaryResponse;
}

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
    return <p className="italic text-muted-foreground">No cost entries for this month.</p>;
  }

  return (
    <table className="mt-4 w-full border-collapse">
      <thead>
        <tr className="border-b-2 border-border text-left">
          <th className="p-2">Cost Type</th>
          <th className="p-2">Sub Type</th>
          <th className="p-2 text-right">Quantity</th>
          <th className="p-2 text-right">Total (USD)</th>
          <th className="p-2 text-right">Entries</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row, idx) => (
          <tr key={`${row.costType}-${row.subType}-${idx}`} className="border-b border-border">
            <td className="p-2">{row.costType}</td>
            <td className="p-2">{row.subType}</td>
            <td className="p-2 text-right">{row.quantity}</td>
            <td className="p-2 text-right">${row.totalCostUsd}</td>
            <td className="p-2 text-right">{row.entryCount}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
