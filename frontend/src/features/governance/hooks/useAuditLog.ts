/**
 * File: frontend/src/features/governance/hooks/useAuditLog.ts
 * Purpose: TanStack Query hook for paginated audit_log read (consumed by AuditLogViewer).
 * Category: Frontend / governance / hooks
 * Scope: Phase 57 / Sprint 57.9 US-4 Day 3
 *
 * Description:
 *   Wraps `auditService.fetchAuditLog` with:
 *   - `queryKey: [...AUDIT_LOG_QUERY_KEY_BASE, filter]` — TanStack auto-refetches
 *     when any filter field changes (form submit produces a new filter object →
 *     new key → fresh fetch). Single-source `AUDIT_LOG_QUERY_KEY_BASE` exported
 *     so a future invalidation hook (e.g. on retention purge) can target the
 *     base prefix without depending on a specific filter shape.
 *   - `signal` forwarded for auto-cancellation on stale query / unmount
 *   - `keepPreviousData: true` (TanStack v5: `placeholderData: keepPreviousData`)
 *     so paginating offset doesn't flash empty state — preserves prior page
 *     while next loads. Mirror Sprint 57.4 admin-tenants UX intent (without
 *     the dedicated D8 fix; AuditLogViewer is read-only so simpler).
 *
 *   No refetchInterval — audit log is heavy + chain verify is heavier; UX is
 *   "load on demand" not "poll". User can hit Refresh button to manually
 *   re-trigger via `refetch()`.
 *
 * Created: 2026-05-09 (Sprint 57.9 Day 3 US-4)
 *
 * Modification History (newest-first):
 *   - 2026-05-09: Initial creation (Sprint 57.9 US-4)
 *
 * Related:
 *   - ../services/auditService.ts (fetchAuditLog source)
 *   - ../components/AuditLogViewer.tsx (consumer)
 *   - ../types.ts (AuditLogFilter / AuditLogPage)
 */

import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { auditService } from "../services/auditService";
import type { AuditLogFilter, AuditLogPage } from "../types";

/**
 * Single-source query key prefix for audit log queries. Exported so a future
 * invalidation hook (Phase 58+) can `qc.invalidateQueries({ queryKey: AUDIT_LOG_QUERY_KEY_BASE })`
 * to clear ALL filter combinations without enumerating each.
 */
export const AUDIT_LOG_QUERY_KEY_BASE = ["governance", "audit-log"] as const;

export function useAuditLog(filter: AuditLogFilter) {
  return useQuery<AuditLogPage, Error>({
    queryKey: [...AUDIT_LOG_QUERY_KEY_BASE, filter],
    queryFn: ({ signal }) => auditService.fetchAuditLog(filter, signal),
    placeholderData: keepPreviousData,
  });
}
