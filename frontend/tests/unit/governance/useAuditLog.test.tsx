/**
 * File: frontend/tests/unit/governance/useAuditLog.test.tsx
 * Purpose: Vitest tests for useAuditLog TanStack Query hook (Sprint 57.9 US-4).
 * Category: Frontend / tests / unit / governance
 * Scope: Phase 57 / Sprint 57.9 US-4 Day 3
 *
 * Description:
 *   Mirrors useApprovals.test.tsx pattern (Sprint 57.9 US-3 Day 2 — first
 *   TanStack hook test in V2 frontend). Per D-PRE-10 lesson: refetch test
 *   uses delta assertion (`callsBefore < callsAfter`) not exact count to
 *   tolerate TanStack v5 internal mount-time refetches.
 *
 * Created: 2026-05-09 (Sprint 57.9 Day 3 US-4)
 *
 * Modification History:
 *   - 2026-05-09: Initial creation (Sprint 57.9 US-4)
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, test, vi } from "vitest";

import { auditService } from "@/features/governance/services/auditService";
import { AUDIT_LOG_QUERY_KEY_BASE, useAuditLog } from "@/features/governance/hooks/useAuditLog";
import type { AuditLogPage } from "@/features/governance/types";

function makeWrapper() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
}

const SAMPLE_PAGE: AuditLogPage = {
  items: [
    {
      id: 42,
      tenant_id: "11111111-1111-4111-8111-111111111111",
      user_id: "22222222-2222-4222-8222-222222222222",
      session_id: null,
      operation: "tool_executed",
      resource_type: "tool",
      resource_id: "salesforce_query",
      operation_data: { args: { q: "SELECT Id FROM Lead" } },
      operation_result: "success",
      previous_log_hash: "0000000000000000",
      current_log_hash: "abcdef1234567890abcdef",
      timestamp_ms: Date.UTC(2026, 4, 9, 10, 0, 0),
    },
  ],
  has_more: false,
  next_offset: null,
  page_size: 50,
};

describe("useAuditLog (Sprint 57.9 US-4)", () => {
  test("AUDIT_LOG_QUERY_KEY_BASE is single-source ['governance', 'audit-log']", () => {
    expect(AUDIT_LOG_QUERY_KEY_BASE).toEqual(["governance", "audit-log"]);
  });

  test("initial fetch returns audit page on success", async () => {
    const spy = vi.spyOn(auditService, "fetchAuditLog").mockResolvedValueOnce(SAMPLE_PAGE);

    const { result } = renderHook(() => useAuditLog({ offset: 0, page_size: 50 }), {
      wrapper: makeWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(spy).toHaveBeenCalledTimes(1);
    expect(result.current.data).toEqual(SAMPLE_PAGE);
    expect(result.current.error).toBeNull();
  });

  test("error state surfaces when service throws (e.g. 403 auditor RBAC)", async () => {
    vi.spyOn(auditService, "fetchAuditLog").mockRejectedValueOnce(
      new Error("HTTP 403: auditor role required"),
    );

    const { result } = renderHook(() => useAuditLog({ offset: 0, page_size: 50 }), {
      wrapper: makeWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toBe("HTTP 403: auditor role required");
    expect(result.current.data).toBeUndefined();
  });

  test("refetch() triggers an additional service call", async () => {
    // Per D-PRE-10 lesson: TanStack v5 may make internal mount-time refetches;
    // use mockResolvedValue (not Once) + delta assertion (callsBefore < callsAfter)
    // not exact pre-refetch count.
    const spy = vi.spyOn(auditService, "fetchAuditLog").mockResolvedValue(SAMPLE_PAGE);

    const { result } = renderHook(() => useAuditLog({ offset: 0, page_size: 50 }), {
      wrapper: makeWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    const callsBefore = spy.mock.calls.length;

    await result.current.refetch();
    expect(spy.mock.calls.length).toBeGreaterThan(callsBefore);
    expect(result.current.data).toEqual(SAMPLE_PAGE);
  });
});
