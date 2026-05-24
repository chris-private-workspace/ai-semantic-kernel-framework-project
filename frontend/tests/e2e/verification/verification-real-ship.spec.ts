/**
 * File: frontend/tests/e2e/verification/verification-real-ship.spec.ts
 * Purpose: Playwright e2e — Sprint 57.11 US-6 verification page real ship.
 * Category: Frontend / e2e / verification
 * Scope: Phase 57 / Sprint 57.11 Day 4 / US-6
 *
 * Description:
 *   Validates Sprint 57.11 verification page (US-4 standalone) ships:
 *     1. Auth gate redirects to /auth/login when unauthenticated
 *        (Sprint 57.8 US-5 + Sprint 57.9 D-PRE-16 cascade lesson — JWT seed
 *        required for authenticated tests)
 *     2. Recent tab renders mocked rows on happy path (filter form + table)
 *     3. Empty state with Reset Filters button when filter excludes all rows
 *     4. Click recent row navigates to /verification/timeline?session_id=...
 *
 *   Backend network calls mocked at browser layer via page.route() (~5x
 *   faster than booting backend per memory feedback_e2e_network_mocking_pattern).
 *
 *   AD-Verification-RealShip-E2E (POTENTIAL DEFERRAL): chat-v2 inline panel
 *   SSE injection test was scoped as STRETCH per plan §4.2; deferred to
 *   Phase 57.12+ as SSE mock at Playwright layer is brittle (3 prior sprints
 *   show similar deferrals).
 *
 * Created: 2026-05-10 (Sprint 57.11 Day 4 / US-6)
 *
 * Modification History (newest-first):
 *   - 2026-05-10: Initial creation (Sprint 57.11 Day 4 / US-6)
 *
 * Related:
 *   - frontend/src/pages/verification/index.tsx (auth gate + nested routes)
 *   - frontend/src/features/verification/components/VerificationList.tsx
 *   - frontend/src/features/verification/components/CorrectionTraceView.tsx
 *   - tests/e2e/fixtures/auth-fixtures.ts (seedAuthJwt)
 */

import { expect, test, type Page } from "@playwright/test";

import { seedAuthJwt } from "../fixtures/auth-fixtures";

const SAMPLE_RECENT_PAGE = {
  items: [
    {
      id: 7,
      tenant_id: "11111111-1111-4111-8111-111111111111",
      session_id: "22222222-2222-4222-8222-222222222222",
      turn_index: 0,
      verifier_name: "pii_redaction",
      verifier_type: "rules_based",
      passed: true,
      score: 0.99,
      reason: null,
      suggested_correction: null,
      correction_attempt: 0,
      created_at_ms: Date.UTC(2026, 4, 10, 8, 0, 0),
    },
    {
      id: 8,
      tenant_id: "11111111-1111-4111-8111-111111111111",
      session_id: "33333333-3333-4333-8333-333333333333",
      turn_index: 0,
      verifier_name: "off_topic",
      verifier_type: "llm_judge",
      passed: false,
      score: null,
      reason: "drifted from original topic",
      suggested_correction: null,
      correction_attempt: 0,
      created_at_ms: Date.UTC(2026, 4, 10, 8, 5, 0),
    },
  ],
  total: 2,
  has_more: false,
  next_offset: null,
  page_size: 50,
};

async function mockVerificationRecent(
  page: Page,
  body: typeof SAMPLE_RECENT_PAGE | { items: never[]; total: 0; has_more: false; next_offset: null; page_size: number },
): Promise<void> {
  await page.route("**/api/v1/verification/recent**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(body),
    });
  });
}

async function mockCorrectionTrace404(page: Page): Promise<void> {
  await page.route("**/api/v1/verification/*/correction-trace", async (route) => {
    await route.fulfill({
      status: 404,
      contentType: "application/json",
      body: JSON.stringify({ detail: "No verification entries for this session." }),
    });
  });
}

test.describe("Sprint 57.11 US-6 — Verification page real ship", () => {
  test("auth gate redirects to /auth/login when unauthenticated", async ({ page }) => {
    // No seedAuthJwt — simulate unauthenticated visitor
    await page.goto("/verification");
    await expect(page).toHaveURL(/\/auth\/login/);
  });

  test("recent tab renders 2 mocked rows on happy path", async ({ page }) => {
    await seedAuthJwt(page);
    await mockVerificationRecent(page, SAMPLE_RECENT_PAGE);

    await page.goto("/verification");

    // Auth gate passed; AppShellV2 renders + 2 tabs visible
    // Sprint 57.39: tab-shell swapped to mockup-ui Tabs primitive (role="tab" not role="link")
    await expect(page.getByRole("tab", { name: "Recent" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "Correction Trace" })).toBeVisible();

    // VerificationList rendered + 2 rows visible
    await expect(page.getByTestId("verification-table")).toBeVisible();
    await expect(page.getByText("pii_redaction")).toBeVisible();
    await expect(page.getByText("off_topic")).toBeVisible();
    await expect(page.getByText("drifted from original topic")).toBeVisible();
  });

  test("empty state with Reset Filters button when no rows match", async ({ page }) => {
    await seedAuthJwt(page);
    await mockVerificationRecent(page, {
      items: [],
      total: 0,
      has_more: false,
      next_offset: null,
      page_size: 50,
    });

    await page.goto("/verification");

    await expect(page.getByText("No verification entries match the filters.")).toBeVisible();
    await expect(page.getByTestId("empty-reset")).toBeVisible();
  });

  test("click recent table row navigates to /verification/timeline?session_id=...", async ({
    page,
  }) => {
    await seedAuthJwt(page);
    await mockVerificationRecent(page, SAMPLE_RECENT_PAGE);
    await mockCorrectionTrace404(page);

    await page.goto("/verification");
    await expect(page.getByTestId("row-7")).toBeVisible();

    await page.getByTestId("row-7").click();

    // URL changes to /verification/timeline with session_id query param
    await expect(page).toHaveURL(/\/verification\/timeline\?session_id=22222222/);
    // CorrectionTraceView renders 404 empty state (mocked)
    await expect(page.getByTestId("trace-empty")).toBeVisible();
  });
});
