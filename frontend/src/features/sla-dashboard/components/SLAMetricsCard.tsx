/* eslint-disable no-restricted-syntax -- AD-Inline-Style-Cleanup-Sweep-Round2: inline styles deferred (includes dynamic bar widths — CSS-custom-property migration in a follow-up sprint). */
/**
 * File: frontend/src/features/sla-dashboard/components/SLAMetricsCard.tsx
 * Purpose: Render single SLA metric with pass-fail color indicator.
 * Category: Frontend / sla-dashboard / components
 * Scope: Phase 57 / Sprint 57.1 US-3
 *
 * Description:
 *   Pass-fail rule:
 *   - mode="gte": pass if value >= threshold (e.g. availability_pct ≥ 99.5%)
 *   - mode="lte": pass if value !== null && value <= threshold (latency p99)
 *   Null value → muted display with "no data" note.
 *
 * Created: 2026-05-06 (Sprint 57.1 Day 2)
 * Last Modified: 2026-05-06
 *
 * Modification History:
 *   - 2026-05-06: Initial creation (Sprint 57.1 Day 2 / US-3 — metric card)
 */

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

export function SLAMetricsCard({ label, value, threshold, unit, mode }: SLAMetricsCardProps) {
  const passing = isPassing(value, threshold, mode);
  const noData = value === null;

  const color = noData ? "#888" : passing ? "#1a7f37" : "#a00";
  const bg = noData ? "#f6f6f6" : passing ? "#e6f4ea" : "#fce8e6";
  const status = noData ? "no data" : passing ? "PASS" : "FAIL";

  return (
    <div
      style={{
        padding: "1rem",
        border: `2px solid ${color}`,
        backgroundColor: bg,
        borderRadius: "0.5rem",
        minWidth: "200px",
      }}
      data-testid={`sla-card-${label.toLowerCase().replace(/\s+/g, "-")}`}
    >
      <p style={{ margin: 0, fontSize: "0.85rem", color: "#444" }}>{label}</p>
      <p style={{ margin: "0.5rem 0", fontSize: "1.5rem", fontWeight: "bold", color }}>
        {noData ? "—" : `${value}${unit}`}
      </p>
      <p style={{ margin: 0, fontSize: "0.8rem", color }}>
        {status} (threshold {mode === "gte" ? "≥" : "≤"} {threshold}{unit})
      </p>
    </div>
  );
}
