/**
 * File: frontend/src/features/admin-tenants/components/TenantListFilters.tsx
 * Purpose: Filter bar (state dropdown + plan dropdown + search input + Apply/Reset).
 * Category: Frontend / admin-tenants / components
 * Scope: Phase 57 / Sprint 57.4 US-3
 *
 * Description:
 *   Local form state for filter inputs; on Apply -> call store.setFilter
 *   (TanStack auto-refetches on queryKey change). On Reset -> store.reset
 *   (same auto-refetch). Search input has maxLength=128 (matches backend
 *   Query validation).
 *
 *   Note: 57.4 ships with explicit Apply button (no debounce) per
 *   AP-6 — debounce can be added later when search frequency tuning
 *   becomes a real need.
 *
 * Created: 2026-05-07 (Sprint 57.4 Day 3)
 * Last Modified: 2026-05-09
 *
 * Modification History (newest-first):
 *   - 2026-05-09: Sprint 57.9 US-6 Day 4 — drop loadData calls (TanStack auto-refetch on query change)
 *   - 2026-05-07: Initial creation (Sprint 57.4 Day 3)
 */

import { useState } from "react";

import { useAdminTenantsStore } from "../store/adminTenantsStore";
import { TenantPlan, TenantState } from "../types";

const ROW_STYLE: React.CSSProperties = {
  display: "flex",
  flexWrap: "wrap",
  gap: "0.75rem",
  alignItems: "flex-end",
  padding: "0.75rem",
  background: "#fafafa",
  border: "1px solid #ddd",
  borderRadius: "0.25rem",
};

const LABEL_STYLE: React.CSSProperties = {
  fontSize: "0.85rem",
  fontWeight: 600,
  color: "#444",
  display: "flex",
  flexDirection: "column",
};

export function TenantListFilters(): JSX.Element {
  const setFilter = useAdminTenantsStore((s) => s.setFilter);
  const reset = useAdminTenantsStore((s) => s.reset);

  const [stateInput, setStateInput] = useState<TenantState | "">("");
  const [planInput, setPlanInput] = useState<TenantPlan | "">("");
  const [searchInput, setSearchInput] = useState<string>("");

  const handleApply = (): void => {
    setFilter({
      state: stateInput === "" ? undefined : stateInput,
      plan: planInput === "" ? undefined : planInput,
      search: searchInput === "" ? undefined : searchInput,
    });
    // TanStack auto-refetches when queryKey (which includes store.query) changes
  };

  const handleReset = (): void => {
    setStateInput("");
    setPlanInput("");
    setSearchInput("");
    reset();
    // TanStack auto-refetches via queryKey change after store.reset
  };

  return (
    <div style={ROW_STYLE}>
      <label style={LABEL_STYLE}>
        State
        <select
          value={stateInput}
          onChange={(e) => setStateInput(e.target.value as TenantState | "")}
        >
          <option value="">All</option>
          <option value={TenantState.REQUESTED}>REQUESTED</option>
          <option value={TenantState.PROVISIONING}>PROVISIONING</option>
          <option value={TenantState.ACTIVE}>ACTIVE</option>
          <option value={TenantState.SUSPENDED}>SUSPENDED</option>
          <option value={TenantState.ARCHIVED}>ARCHIVED</option>
        </select>
      </label>

      <label style={LABEL_STYLE}>
        Plan
        <select
          value={planInput}
          onChange={(e) => setPlanInput(e.target.value as TenantPlan | "")}
        >
          <option value="">All</option>
          <option value={TenantPlan.STANDARD}>STANDARD</option>
          <option value={TenantPlan.ENTERPRISE}>ENTERPRISE</option>
        </select>
      </label>

      <label style={LABEL_STYLE}>
        Search
        <input
          type="text"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          maxLength={128}
          placeholder="Code or display name…"
          style={{ minWidth: "16rem" }}
        />
      </label>

      <button onClick={handleApply}>Apply</button>
      <button onClick={handleReset}>Reset</button>
    </div>
  );
}
