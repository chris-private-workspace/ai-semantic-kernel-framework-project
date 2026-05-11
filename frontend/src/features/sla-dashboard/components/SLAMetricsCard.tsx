/**
 * File: frontend/src/features/sla-dashboard/components/SLAMetricsCard.tsx
 * Purpose: Render single SLA metric with pass-fail color indicator.
 * Category: Frontend / sla-dashboard / components
 * Scope: Phase 57 / Sprint 57.1 US-3 → Sprint 57.16 Tailwind migration
 *
 * Description:
 *   Pass-fail rule:
 *   - mode="gte": pass if value >= threshold (e.g. availability_pct ≥ 99.5%)
 *   - mode="lte": pass if value !== null && value <= threshold (latency p99)
 *   Null value → muted display with "no data" note.
 *
 *   Sprint 57.16 (AD-Inline-Style-Cleanup-Sweep-Round2): migrated to Tailwind
 *   utility classes; the 3-way state (noData / pass / fail) drives a finite
 *   class lookup (SLA_STATE) — text/border/bg classes per state, 57.15 vocab
 *   for visual continuity with TenantListTable's badge palette.
 *
 * Created: 2026-05-06 (Sprint 57.1 Day 2)
 * Last Modified: 2026-05-11
 *
 * Modification History (newest-first):
 *   - 2026-05-11: Sprint 57.16 — inline styles → Tailwind utility classes; 3-way enum colour → SLA_STATE finite lookup (AD-Inline-Style-Cleanup-Sweep-Round2)
 *   - 2026-05-06: Initial creation (Sprint 57.1 Day 2 / US-3 — metric card)
 */

import { cn } from "../../../lib/utils";

interface SLAMetricsCardProps {
  label: string;
  value: number | null;
  threshold: number;
  unit: string;
  mode: "gte" | "lte"; // gte = higher is better (availability); lte = lower is better (latency)
}

function isPassing(value: number | null, threshold: number, mode: "gte" | "lte"): boolean {
  if (value === null) return false;
  return mode === "gte" ? value >= threshold : value <= threshold;
}

// 3-way SLA state → {text, border, bg} Tailwind class triple. Finite lookup
// per STYLE.md §1 "Inline-style escape hatches" → "finite class lookup"; 57.15
// vocab for visual continuity with TenantListTable.
const SLA_STATE = {
  noData: { text: "text-muted-foreground", border: "border-border", bg: "bg-muted" },
  pass: { text: "text-success", border: "border-success", bg: "bg-success/10" },
  fail: { text: "text-danger", border: "border-danger", bg: "bg-danger/10" },
} as const;

export function SLAMetricsCard({ label, value, threshold, unit, mode }: SLAMetricsCardProps) {
  const passing = isPassing(value, threshold, mode);
  const noData = value === null;
  const status = noData ? "no data" : passing ? "PASS" : "FAIL";
  const st = noData ? SLA_STATE.noData : passing ? SLA_STATE.pass : SLA_STATE.fail;

  return (
    <div
      className={cn("min-w-[200px] rounded-lg border-2 p-4", st.border, st.bg)}
      data-testid={`sla-card-${label.toLowerCase().replace(/\s+/g, "-")}`}
    >
      <p className="m-0 text-[0.85rem] text-muted-foreground">{label}</p>
      <p className={cn("my-2 text-2xl font-bold", st.text)}>
        {noData ? "—" : `${value}${unit}`}
      </p>
      <p className={cn("m-0 text-xs", st.text)}>
        {status} (threshold {mode === "gte" ? "≥" : "≤"} {threshold}{unit})
      </p>
    </div>
  );
}
