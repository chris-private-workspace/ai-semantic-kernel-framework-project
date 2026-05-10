/**
 * File: frontend/tests/unit/lib/toast.test.ts
 * Purpose: Unit test for lib/toast — wrappers delegate to sonner; errorMessage normalises.
 * Category: Frontend / tests / unit / lib
 * Scope: Phase 57 / Sprint 57.13 US-B1
 *
 * Created: 2026-05-10 (Sprint 57.13 Day 3)
 */

import { beforeEach, describe, expect, it, vi } from "vitest";

const { errorMock, successMock, baseMock } = vi.hoisted(() => ({
  errorMock: vi.fn(),
  successMock: vi.fn(),
  baseMock: vi.fn(),
}));

vi.mock("sonner", () => {
  const toast = Object.assign(baseMock, { error: errorMock, success: successMock });
  return { toast };
});

import { errorMessage, toastError, toastInfo, toastSuccess } from "../../../src/lib/toast";

describe("lib/toast", () => {
  beforeEach(() => {
    errorMock.mockReset();
    successMock.mockReset();
    baseMock.mockReset();
  });

  it("toastError → toast.error", () => {
    toastError("boom");
    expect(errorMock).toHaveBeenCalledWith("boom");
  });

  it("toastSuccess → toast.success", () => {
    toastSuccess("done");
    expect(successMock).toHaveBeenCalledWith("done");
  });

  it("toastInfo → toast()", () => {
    toastInfo("fyi");
    expect(baseMock).toHaveBeenCalledWith("fyi");
  });

  describe("errorMessage", () => {
    it("uses Error.message", () => {
      expect(errorMessage(new Error("nope"))).toBe("nope");
    });

    it("uses a raw string", () => {
      expect(errorMessage("plain string")).toBe("plain string");
    });

    it("falls back for empty/unknown values", () => {
      expect(errorMessage(new Error(""))).toBe("發生未預期的錯誤");
      expect(errorMessage(undefined)).toBe("發生未預期的錯誤");
      expect(errorMessage({ weird: true }, "custom fallback")).toBe("custom fallback");
    });
  });
});
