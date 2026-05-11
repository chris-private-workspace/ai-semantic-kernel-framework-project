/**
 * File: frontend/src/features/cost-dashboard/components/MonthPicker.tsx
 * Purpose: YYYY-MM month picker shared by Cost + SLA dashboards.
 * Category: Frontend / cost-dashboard / components (also imported by sla-dashboard)
 * Scope: Phase 57 / Sprint 57.1 US-1 (shared)
 *
 * Description:
 *   Per Day 0 verdict (frontend/src/features/shared/ does not exist),
 *   MonthPicker lives in cost-dashboard/components/ and is imported by
 *   sla-dashboard. Native <input type="month"> for browser-supported UX.
 *
 * Created: 2026-05-06 (Sprint 57.1 Day 1)
 * Last Modified: 2026-05-11
 *
 * Modification History (newest-first):
 *   - 2026-05-11: Sprint 57.15 — inline styles → Tailwind utility classes (AD-Inline-Style-Cleanup-Sweep)
 *   - 2026-05-06: Initial creation (Sprint 57.1 Day 1 / US-1 — shared MonthPicker)
 */

interface MonthPickerProps {
  value: string;
  onChange: (month: string) => void;
  disabled?: boolean;
}

export function MonthPicker({ value, onChange, disabled }: MonthPickerProps) {
  return (
    <label className="inline-flex items-center gap-2">
      <span>Month:</span>
      <input
        type="month"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        aria-label="Select month"
        className="px-2 py-1"
      />
    </label>
  );
}
