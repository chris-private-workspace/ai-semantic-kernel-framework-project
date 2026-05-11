/**
 * File: frontend/src/features/admin-tenants/components/TenantListPagination.tsx
 * Purpose: Prev/Next + page indicator for admin tenants list.
 * Category: Frontend / admin-tenants / components
 * Scope: Phase 57 / Sprint 57.4 US-4 → Sprint 57.9 US-6 Day 4 (TanStack hook)
 *
 * Description:
 *   Reads { query (limit/offset) } from store + total from useAdminTenants
 *   hook. Prev disabled at offset=0; Next disabled when offset + limit >=
 *   total. Indicator shows "{from}-{to} of {total}" range. setPagination
 *   triggers TanStack auto-refetch via queryKey change.
 *
 * Created: 2026-05-07 (Sprint 57.4 Day 3)
 * Last Modified: 2026-05-11
 *
 * Modification History (newest-first):
 *   - 2026-05-11: Sprint 57.15 — inline styles → Tailwind utility classes; `#666`→text-muted-foreground (AD-Inline-Style-Cleanup-Sweep)
 *   - 2026-05-09: Sprint 57.9 US-6 Day 4 — read total from useAdminTenants hook (drop store.total + loadData)
 *   - 2026-05-07: Initial creation (Sprint 57.4 Day 3)
 */

import { useAdminTenants } from "../hooks/useAdminTenants";
import { useAdminTenantsStore } from "../store/adminTenantsStore";

export function TenantListPagination(): JSX.Element {
  const query = useAdminTenantsStore((s) => s.query);
  const setPagination = useAdminTenantsStore((s) => s.setPagination);
  const { data } = useAdminTenants();
  const total = data?.total ?? 0;

  const { limit, offset } = query;
  const from = total === 0 ? 0 : offset + 1;
  const to = Math.min(offset + limit, total);
  const prevDisabled = offset === 0;
  const nextDisabled = offset + limit >= total;

  const handlePrev = (): void => {
    if (prevDisabled) return;
    setPagination({ offset: Math.max(0, offset - limit) });
  };

  const handleNext = (): void => {
    if (nextDisabled) return;
    setPagination({ offset: offset + limit });
  };

  return (
    <div className="mt-4 flex items-center gap-3 py-2">
      <button onClick={handlePrev} disabled={prevDisabled}>
        ← Prev
      </button>
      <button onClick={handleNext} disabled={nextDisabled}>
        Next →
      </button>
      <span className="text-sm text-muted-foreground">
        {from}-{to} of {total}
      </span>
    </div>
  );
}
