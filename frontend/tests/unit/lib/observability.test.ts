/**
 * File: frontend/tests/unit/lib/observability.test.ts
 * Purpose: Unit tests for lib/observability — initObservability / reportError / reportWebVitals.
 * Category: Frontend / tests / unit / lib
 * Scope: Phase 57 / Sprint 57.13 US-B4
 *
 * Created: 2026-05-10 (Sprint 57.13 Day 6)
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// Mock web-vitals so reportWebVitals' dynamic import resolves to spies; onCLS
// fires its callback synchronously with a fake metric so we can observe the beacon.
const fakeMetric = {
  name: "CLS",
  value: 0.05,
  id: "v5-fake",
  rating: "good",
  navigationType: "navigate",
};
vi.mock("web-vitals", () => ({
  onCLS: (cb: (m: typeof fakeMetric) => void) => cb(fakeMetric),
  onFCP: vi.fn(),
  onLCP: vi.fn(),
  onINP: vi.fn(),
  onTTFB: vi.fn(),
}));

import { initObservability, reportError, reportWebVitals } from "../../../src/lib/observability";

describe("lib/observability", () => {
  let sendBeacon: ReturnType<typeof vi.fn>;
  let consoleErr: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    sendBeacon = vi.fn(() => true);
    Object.defineProperty(globalThis.navigator, "sendBeacon", {
      value: sendBeacon,
      configurable: true,
    });
    consoleErr = vi.spyOn(console, "error").mockImplementation(() => {});
    vi.stubEnv("VITE_SENTRY_DSN", "");
  });

  afterEach(() => {
    consoleErr.mockRestore();
    vi.unstubAllEnvs();
  });

  it("initObservability is a no-op (resolves, no beacon) when VITE_SENTRY_DSN is empty", async () => {
    await initObservability();
    expect(sendBeacon).not.toHaveBeenCalled();
  });

  it("reportError always console.errors and beacons to /frontend-error", () => {
    reportError(new Error("kaboom"), { source: "test" });
    expect(consoleErr).toHaveBeenCalled();
    expect(sendBeacon).toHaveBeenCalledWith("/api/v1/telemetry/frontend-error", expect.any(Blob));
  });

  it("reportError tolerates non-Error values", () => {
    expect(() => reportError("string error")).not.toThrow();
    expect(sendBeacon).toHaveBeenCalledWith("/api/v1/telemetry/frontend-error", expect.any(Blob));
  });

  it("reportWebVitals beacons each metric to /telemetry/frontend", async () => {
    reportWebVitals();
    await vi.waitFor(() => {
      expect(sendBeacon).toHaveBeenCalledWith("/api/v1/telemetry/frontend", expect.any(Blob));
    });
  });

  it("falls back to fetch keepalive when sendBeacon is unavailable", async () => {
    Object.defineProperty(globalThis.navigator, "sendBeacon", {
      value: undefined,
      configurable: true,
    });
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(null, { status: 204 }));
    reportError(new Error("net"));
    expect(fetchSpy).toHaveBeenCalledWith(
      "/api/v1/telemetry/frontend-error",
      expect.objectContaining({ method: "POST", keepalive: true }),
    );
    fetchSpy.mockRestore();
  });
});
