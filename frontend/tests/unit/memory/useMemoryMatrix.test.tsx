/**
 * File: frontend/tests/unit/memory/useMemoryMatrix.test.tsx
 * Purpose: Vitest tests for useMemoryMatrix TanStack Query hook (Sprint 57.73 Track C).
 * Category: Frontend / tests / unit / memory
 * Scope: Phase 57 / Sprint 57.73 Track C (A-6b frontend half)
 *
 * Description:
 *   Mirrors useCostSummary / useAdminTenants test pattern (TanStack hook +
 *   QueryClientProvider wrapper). Asserts query key single-source, success
 *   data shape (cells / total / gapped_layers), and error surface.
 *
 * Created: 2026-06-03 (Sprint 57.73 Track C)
 *
 * Modification History (newest-first):
 *   - 2026-06-03: Initial creation (Sprint 57.73 Track C)
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, test, vi } from "vitest";

import { memoryService } from "@/features/memory/services/memoryService";
import { MEMORY_MATRIX_QUERY_KEY, useMemoryMatrix } from "@/features/memory/hooks/useMemoryMatrix";
import type { MemoryMatrixResponse } from "@/features/memory/types";

function makeWrapper() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
}

const SAMPLE: MemoryMatrixResponse = {
  cells: [
    { layer: "system", time_scale: "permanent", count: 1 },
    { layer: "tenant", time_scale: "permanent", count: 2 },
    { layer: "user", time_scale: "permanent", count: 1 },
    { layer: "user", time_scale: "quarterly", count: 1 },
    { layer: "user", time_scale: "daily", count: 2 },
  ],
  total: 7,
  gapped_layers: ["role", "session"],
};

describe("useMemoryMatrix (Sprint 57.73 Track C)", () => {
  test("MEMORY_MATRIX_QUERY_KEY is single-source ['memory', 'matrix']", () => {
    expect(MEMORY_MATRIX_QUERY_KEY).toEqual(["memory", "matrix"]);
  });

  test("returns matrix response on success (cells / total / gapped_layers)", async () => {
    const spy = vi.spyOn(memoryService, "fetchMatrix").mockResolvedValueOnce(SAMPLE);

    const { result } = renderHook(() => useMemoryMatrix(), { wrapper: makeWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(spy).toHaveBeenCalledTimes(1);
    expect(result.current.data).toEqual(SAMPLE);
    expect(result.current.data?.total).toBe(7);
    expect(result.current.data?.gapped_layers).toEqual(["role", "session"]);
  });

  test("error state surfaces (HTTP 403 auditor RBAC simulation)", async () => {
    vi.spyOn(memoryService, "fetchMatrix").mockRejectedValueOnce(
      new Error("HTTP 403: auditor role required"),
    );

    const { result } = renderHook(() => useMemoryMatrix(), { wrapper: makeWrapper() });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toBe("HTTP 403: auditor role required");
  });
});
