/**
 * File: frontend/src/features/sla-dashboard/components/SLOStatusCard.tsx
 * Purpose: 5-row SLO objectives status card (Sprint 57.25 Day 2 US-C1).
 * Category: Frontend / sla-dashboard / components (feature-scoped)
 * Scope: Phase 57 / Sprint 57.25 Day 2 US-C1
 *
 * Description:
 *   Mockup-direct port of reference/design-mockups/page-admin.jsx:72-99.
 *   5 SLO rows × dot indicator + name + current/target + BarTrack + used%.
 *
 *   SLOs (mockup-faithful order):
 *   1. Loop p95 < 2s    — real `data.loop_simple_p99_ms / 1000` when
 *                         available (used as p95 proxy); else fixture 1.84
 *   2. Tool success ≥ 99% — fixture 99.4 (backend doesn't track yet)
 *   3. HITL response < 5m — fixture 2.3 min (no dedicated metric)
 *   4. Subagent depth ≤ 5 — fixture 4 (no dedicated metric)
 *   5. Cost / run < $0.05 — fixture 0.052 → FAILING (danger tone)
 *
 *   4 of 5 SLO values are fixture per D-PRE-2 (backend doesn't expose
 *   dedicated SLO metrics); the card ships without per-card
 *   BackendGapBanner because each SLO row functionally compares
 *   current vs target via threshold constants (real algorithm even
 *   when input is fixture).
 *
 * Created: 2026-05-19 (Sprint 57.25 Day 2 US-C1)
 *
 * Modification History:
 *   - 2026-05-19: Initial creation (Sprint 57.25 Day 2 US-C1)
 *
 * Related:
 *   - reference/design-mockups/page-admin.jsx:72-99 (canonical mockup)
 *   - sprint-57-25-plan.md §Technical Spec §SLOStatusCard structure
 */

import { useTranslation } from "react-i18next";

import { BarTrack } from "../../../components/charts";
import { CardShell } from "../../../components/ui/CardShell";
import { cn } from "../../../lib/utils";
import type { SLAReportResponse } from "../types";

interface SLORow {
  key: string;
  i18nKey: string;
  current: number;
  target: number;
  mode: "lte" | "gte";
  used: number; // budget used percent (0-100); per mockup demo
  unit: string;
}

interface SLOStatusCardProps {
  data: SLAReportResponse | null;
}

export function SLOStatusCard({ data }: SLOStatusCardProps) {
  const { t } = useTranslation("common");

  // Derive Loop p95 current from real backend when available (loop_simple_p99_ms
  // is used as p95 proxy — backend hasn't yet split p95 vs p99 per D-PRE-2);
  // fixture fallback matches mockup demo value 1.84s.
  const loopCurrent =
    data?.loop_simple_p99_ms != null ? Number((data.loop_simple_p99_ms / 1000).toFixed(2)) : 1.84;

  const SLOS: SLORow[] = [
    { key: "loopP95", i18nKey: "sla.slo.loopP95", current: loopCurrent, target: 2.0, mode: "lte", used: 8, unit: "s" },
    { key: "toolSuccess", i18nKey: "sla.slo.toolSuccess", current: 99.4, target: 99, mode: "gte", used: 28, unit: "%" },
    { key: "hitlResponse", i18nKey: "sla.slo.hitlResponse", current: 2.3, target: 5, mode: "lte", used: 12, unit: "m" },
    { key: "subagentDepth", i18nKey: "sla.slo.subagentDepth", current: 4, target: 5, mode: "lte", used: 0, unit: "" },
    { key: "costPerRun", i18nKey: "sla.slo.costPerRun", current: 0.052, target: 0.05, mode: "lte", used: 108, unit: "" },
  ];

  return (
    <CardShell title={t("sla.slo.title")} subtitle={t("sla.slo.subtitle")}>
      <div className="flex flex-col gap-3" data-testid="sla-slo-card">
        {SLOS.map((s, idx) => {
          const ok = s.mode === "lte" ? s.current <= s.target : s.current >= s.target;
          return (
            <div key={s.key} data-testid={`sla-slo-row-${idx}`}>
              <div className="mb-1 flex items-center justify-between">
                <span className="inline-flex items-center gap-1.5 text-[12.5px]">
                  <span
                    className={cn(
                      "h-1.5 w-1.5 rounded-full",
                      ok ? "bg-success" : "bg-danger",
                    )}
                    data-testid={`sla-slo-dot-${idx}`}
                    data-ok={ok ? "true" : "false"}
                  />
                  {t(s.i18nKey)}
                </span>
                <span
                  className={cn(
                    "font-mono text-[11.5px] tabular-nums",
                    ok ? "text-fg-muted" : "text-danger",
                  )}
                  data-testid={`sla-slo-current-${idx}`}
                >
                  {s.current}
                  {s.unit}{" "}
                  <span className="text-fg-subtle">
                    / {s.target}
                    {s.unit}
                  </span>
                </span>
              </div>
              <BarTrack
                pct={s.used}
                tone={ok ? "var(--success)" : "var(--danger)"}
              />
              <div className="mt-1 font-mono text-[10px] text-fg-subtle">
                {t("sla.slo.budgetUsed")}: {s.used}%
              </div>
            </div>
          );
        })}
      </div>
    </CardShell>
  );
}
