/**
 * File: frontend/src/features/cost-dashboard/components/MonthPicker.tsx
 * Purpose: YYYY-MM month picker shared by Cost + SLA dashboards; mockup-token styled (Sprint 57.31).
 * Category: Frontend / cost-dashboard / components (also imported by sla-dashboard)
 * Scope: Phase 57 / Sprint 57.1 US-1 → 57.31 Day 1 (verbatim re-point to mockup vocabulary)
 *
 * Description:
 *   Per Day 0 verdict (frontend/src/features/shared/ does not exist),
 *   MonthPicker lives in cost-dashboard/components/ and is imported by
 *   sla-dashboard. Native <input type="month"> for browser-supported UX.
 *
 *   Sprint 57.31 Day 1 verbatim re-point: switched to mockup token vocabulary
 *   (var(--fg-muted) / var(--border) / var(--bg-1) / mono class) — production
 *   widget without a mockup equivalent (Day 0 D5 finding) so no AP-2 banner
 *   needed. Re-uses .btn ghost-adjacent visual shape (subtle outline pill).
 *
 * Created: 2026-05-06 (Sprint 57.1 Day 1)
 * Last Modified: 2026-05-23
 *
 * Modification History (newest-first):
 *   - 2026-05-23: Sprint 57.31 Day 1 — verbatim re-point to mockup token vocabulary (var(--*) inline; drop Tailwind utility classes)
 *   - 2026-05-11: Sprint 57.15 — inline styles → Tailwind utility classes (AD-Inline-Style-Cleanup-Sweep)
 *   - 2026-05-06: Initial creation (Sprint 57.1 Day 1 / US-1 — shared MonthPicker)
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: inline-style literals use mockup var(--*) tokens; production-only widget with no mockup equivalent (frontend-mockup-fidelity.md STYLE.md §1 escape hatch) */

import type { CSSProperties } from "react";

interface MonthPickerProps {
  value: string;
  onChange: (month: string) => void;
  disabled?: boolean;
}

const wrapStyle: CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: 6,
  fontSize: 12,
  color: "var(--fg-muted)",
};

const inputStyle: CSSProperties = {
  fontFamily:
    "ui-monospace, SFMono-Regular, Menlo, monospace",
  fontSize: 12,
  padding: "4px 8px",
  borderRadius: 6,
  border: "1px solid var(--border)",
  background: "var(--bg-1)",
  color: "var(--fg)",
};

export function MonthPicker({ value, onChange, disabled }: MonthPickerProps) {
  return (
    <label style={wrapStyle}>
      <span>Month:</span>
      <input
        type="month"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        aria-label="Select month"
        style={inputStyle}
      />
    </label>
  );
}
