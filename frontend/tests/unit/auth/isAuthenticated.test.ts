/**
 * File: frontend/tests/unit/auth/isAuthenticated.test.ts
 * Purpose: Unit test — authService.isAuthenticated() reflects authStore.status.
 * Category: Frontend / tests / unit / auth
 * Scope: Phase 57 / Sprint 57.13 US-A1
 *
 * Created: 2026-05-10 (Sprint 57.13 Day 1)
 */

import { afterEach, describe, expect, it } from "vitest";

import { isAuthenticated } from "../../../src/features/auth/services/authService";
import { useAuthStore } from "../../../src/features/auth/store/authStore";

describe("isAuthenticated()", () => {
  afterEach(() => {
    useAuthStore.setState({ status: "unknown", user: null, tenant: null, roles: [] });
  });

  it("false while status is 'unknown' (bootstrap not done)", () => {
    useAuthStore.setState({ status: "unknown" });
    expect(isAuthenticated()).toBe(false);
  });

  it("false when status is 'anonymous'", () => {
    useAuthStore.setState({ status: "anonymous" });
    expect(isAuthenticated()).toBe(false);
  });

  it("true when status is 'authenticated'", () => {
    useAuthStore.setState({ status: "authenticated" });
    expect(isAuthenticated()).toBe(true);
  });
});
