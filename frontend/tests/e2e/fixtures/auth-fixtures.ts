/**
 * File: frontend/tests/e2e/fixtures/auth-fixtures.ts
 * Purpose: Auth JWT seeder + clearer for e2e tests gated by isAuthenticated().
 * Category: Frontend / e2e / fixtures
 * Scope: Phase 57 / Sprint 57.8 US-5 Day 3
 *
 * Description:
 *   Sprint 57.8 introduces the first auth gate (chat-v2 page). E2e tests
 *   that target authenticated routes must seed a JWT into localStorage
 *   BEFORE page.goto() — Playwright's `addInitScript` runs in every new
 *   document, so this seeder works across navigations within a test.
 *
 *   The helper writes to the same key (`v2_jwt`) consumed by
 *   features/auth/services/authService.ts → isAuthenticated(). Backend
 *   network calls go through `fetchWithAuth` which reads the same key,
 *   so chatService SSE requests will carry the seeded token.
 *
 *   For tests that need to exercise the unauthenticated path (auth-gate
 *   redirect to /auth/login), simply skip seeding (or call clearAuthJwt
 *   to be explicit about intent).
 *
 * Created: 2026-05-09 (Sprint 57.8 Day 3)
 *
 * Related:
 *   - frontend/src/features/auth/services/authService.ts
 *   - frontend/src/pages/chat-v2/index.tsx (first consumer of auth gate)
 */

import type { Page } from "@playwright/test";

const JWT_KEY = "v2_jwt";

/**
 * Seed a JWT into localStorage so isAuthenticated() returns true and
 * fetchWithAuth attaches Authorization: Bearer <token>. Safe default
 * token for tests that only need to bypass the gate (network is mocked).
 */
export async function seedAuthJwt(
  page: Page,
  token: string = "test-jwt-token-do-not-trust",
): Promise<void> {
  await page.addInitScript(
    ({ key, value }: { key: string; value: string }) => {
      window.localStorage.setItem(key, value);
    },
    { key: JWT_KEY, value: token },
  );
}

/** Explicit clear — for tests asserting the unauthenticated redirect path. */
export async function clearAuthJwt(page: Page): Promise<void> {
  await page.addInitScript((key: string) => {
    window.localStorage.removeItem(key);
  }, JWT_KEY);
}
