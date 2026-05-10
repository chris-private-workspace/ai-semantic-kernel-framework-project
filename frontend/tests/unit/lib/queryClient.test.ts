/**
 * File: frontend/tests/unit/lib/queryClient.test.ts
 * Purpose: Unit test for lib/queryClient — defaults + mutationCache.onError toasts.
 * Category: Frontend / tests / unit / lib
 * Scope: Phase 57 / Sprint 57.13 US-B1
 *
 * Created: 2026-05-10 (Sprint 57.13 Day 3)
 */

import { describe, expect, it, vi } from "vitest";

const toastErrorMock = vi.fn();
vi.mock("../../../src/lib/toast", () => ({
  toastError: (msg: string) => toastErrorMock(msg),
  errorMessage: (err: unknown) => (err instanceof Error ? err.message : "fallback"),
}));

import { queryClient } from "../../../src/lib/queryClient";

describe("lib/queryClient", () => {
  it("query defaults: staleTime 30s, no refetch on focus, no retry", () => {
    const q = queryClient.getDefaultOptions().queries;
    expect(q?.staleTime).toBe(30_000);
    expect(q?.refetchOnWindowFocus).toBe(false);
    expect(q?.retry).toBe(false);
  });

  it("mutation defaults: no retry", () => {
    expect(queryClient.getDefaultOptions().mutations?.retry).toBe(false);
  });

  it("mutationCache.onError surfaces a toast with the error message", () => {
    const onError = queryClient.getMutationCache().config.onError;
    expect(onError).toBeTypeOf("function");
    // MutationCache.onError(error, variables, context, mutation)
    onError?.(new Error("save failed"), undefined, undefined, {} as never);
    expect(toastErrorMock).toHaveBeenCalledWith("save failed");
  });
});
