/**
 * File: frontend/tests/unit/memory/useMemoryOps.test.tsx
 * Purpose: Vitest tests for useMemoryOps TanStack Query hook (Sprint 57.77).
 * Category: Frontend / tests / unit / memory
 * Scope: Phase 57 / Sprint 57.77 (AD-Memory-OpsHistory-Backend frontend half)
 *
 * Description:
 *   Mirrors useMemoryMatrix test pattern (TanStack hook + QueryClientProvider
 *   wrapper). Asserts query key single-source, that queryFn forwards to
 *   memoryService.fetchOps (with the default limit + no cursor), success data
 *   shape, and error surface.
 *
 * Created: 2026-06-04 (Sprint 57.77)
 *
 * Modification History (newest-first):
 *   - 2026-06-04: Initial creation (Sprint 57.77)
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, test, vi } from "vitest";

import { MEMORY_OPS_QUERY_KEY, useMemoryOps } from "@/features/memory/hooks/useMemoryOps";
import { memoryService } from "@/features/memory/services/memoryService";
import type { MemoryOpsResponse } from "@/features/memory/types";

function makeWrapper() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
}

const SAMPLE: MemoryOpsResponse = {
  ops: [
    {
      op: "WRITE",
      scope: "user",
      key: "preferences.rca_format",
      time_scale: "permanent",
      value_snapshot: "5-whys + timeline",
      actor: "incident-responder",
      created_at_ms: 1_700_000_002_000,
    },
  ],
  next_cursor: null,
};

describe("useMemoryOps (Sprint 57.77)", () => {
  test("MEMORY_OPS_QUERY_KEY is single-source ['memory', 'ops']", () => {
    expect(MEMORY_OPS_QUERY_KEY).toEqual(["memory", "ops"]);
  });

  test("queryFn calls memoryService.fetchOps and returns the ops response", async () => {
    const spy = vi.spyOn(memoryService, "fetchOps").mockResolvedValueOnce(SAMPLE);

    const { result } = renderHook(() => useMemoryOps(), { wrapper: makeWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(spy).toHaveBeenCalledTimes(1);
    // Hook calls fetchOps(50, undefined, signal) — default page, no cursor.
    expect(spy.mock.calls[0][0]).toBe(50);
    expect(spy.mock.calls[0][1]).toBeUndefined();
    expect(result.current.data).toEqual(SAMPLE);
  });

  test("error state surfaces (HTTP 403 auditor RBAC simulation)", async () => {
    vi.spyOn(memoryService, "fetchOps").mockRejectedValueOnce(
      new Error("auditor role required"),
    );

    const { result } = renderHook(() => useMemoryOps(), { wrapper: makeWrapper() });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toBe("auditor role required");
  });
});
