/**
 * File: frontend/tests/unit/sla-dashboard/useSLAReport.test.tsx
 * Purpose: Vitest tests for useSLAReport TanStack Query hook (Sprint 57.9 US-6).
 * Category: Frontend / tests / unit / sla-dashboard
 * Scope: Phase 57 / Sprint 57.9 US-6 Day 4
 *
 * Created: 2026-05-09 (Sprint 57.9 Day 4 US-6)
 *
 * Modification History:
 *   - 2026-05-09: Initial creation (Sprint 57.9 US-6)
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, test, vi } from "vitest";

import * as slaService from "@/features/sla-dashboard/services/slaService";
import { SLA_REPORT_QUERY_KEY_BASE, useSLAReport } from "@/features/sla-dashboard/hooks/useSLAReport";
import type { SLAReportResponse } from "@/features/sla-dashboard/types";

function makeWrapper() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
}

const SAMPLE_REPORT: SLAReportResponse = {
  tenant_id: "11111111-1111-4111-8111-111111111111",
  month: "2026-05",
  availability_pct: 99.7,
  api_p99_ms: 850,
  loop_simple_p99_ms: 4200,
  loop_medium_p99_ms: 28000,
  loop_complex_p99_ms: 110000,
  hitl_queue_notif_p99_ms: 45000,
  violations_count: 0,
};

describe("useSLAReport (Sprint 57.9 US-6)", () => {
  test("SLA_REPORT_QUERY_KEY_BASE is single-source ['sla-dashboard', 'report']", () => {
    expect(SLA_REPORT_QUERY_KEY_BASE).toEqual(["sla-dashboard", "report"]);
  });

  test("disabled when tenantId is empty (admin hasn't selected tenant)", async () => {
    const spy = vi.spyOn(slaService, "fetchSLAReport").mockResolvedValue(SAMPLE_REPORT);

    const { result } = renderHook(() => useSLAReport("", "2026-05"), {
      wrapper: makeWrapper(),
    });

    await waitFor(() => expect(result.current.isFetching).toBe(false));
    expect(spy).not.toHaveBeenCalled();
    expect(result.current.data).toBeUndefined();
  });

  test("fetches when tenantId provided + returns data on success", async () => {
    const spy = vi.spyOn(slaService, "fetchSLAReport").mockResolvedValueOnce(SAMPLE_REPORT);

    const { result } = renderHook(() => useSLAReport("tenant-uuid", "2026-05"), {
      wrapper: makeWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(spy).toHaveBeenCalledTimes(1);
    expect(result.current.data).toEqual(SAMPLE_REPORT);
  });

  test("error state surfaces (HTTP 403 admin-platform RBAC simulation)", async () => {
    vi.spyOn(slaService, "fetchSLAReport").mockRejectedValueOnce(
      new Error("HTTP 403: admin role required"),
    );

    const { result } = renderHook(() => useSLAReport("tenant-uuid", "2026-05"), {
      wrapper: makeWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toBe("HTTP 403: admin role required");
  });
});
