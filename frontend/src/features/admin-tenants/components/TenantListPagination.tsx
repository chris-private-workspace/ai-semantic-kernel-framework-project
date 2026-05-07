/**
 * File: frontend/src/features/admin-tenants/components/TenantListPagination.tsx
 * Purpose: Prev/Next + page indicator for admin tenants list.
 * Category: Frontend / admin-tenants / components
 * Scope: Phase 57 / Sprint 57.4 US-4
 *
 * Description:
 *   Reads { query (limit/offset), total } from store. Prev disabled at
 *   offset=0; Next disabled when offset + limit >= total. Indicator shows
 *   "{from}-{to} of {total}" range.
 *
 * Created: 2026-05-07 (Sprint 57.4 Day 3)
 */

import { useAdminTenantsStore } from "../store/adminTenantsStore";

const ROW_STYLE: React.CSSProperties = {
  display: "flex",
  gap: "0.75rem",
  alignItems: "center",
  marginTop: "1rem",
  padding: "0.5rem 0",
};

export function TenantListPagination(): JSX.Element {
  const { query, total, setPagination, loadData } = useAdminTenantsStore();

  const { limit, offset } = query;
  const from = total === 0 ? 0 : offset + 1;
  const to = Math.min(offset + limit, total);
  const prevDisabled = offset === 0;
  const nextDisabled = offset + limit >= total;

  const handlePrev = (): void => {
    if (prevDisabled) return;
    setPagination({ offset: Math.max(0, offset - limit) });
    void loadData();
  };

  const handleNext = (): void => {
    if (nextDisabled) return;
    setPagination({ offset: offset + limit });
    void loadData();
  };

  return (
    <div style={ROW_STYLE}>
      <button onClick={handlePrev} disabled={prevDisabled}>
        ← Prev
      </button>
      <button onClick={handleNext} disabled={nextDisabled}>
        Next →
      </button>
      <span style={{ color: "#666", fontSize: "0.9rem" }}>
        {from}-{to} of {total}
      </span>
    </div>
  );
}
