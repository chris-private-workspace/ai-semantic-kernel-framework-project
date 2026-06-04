/**
 * File: frontend/tests/e2e/memory/memory-ops.spec.ts
 * Purpose: Hermetic Playwright e2e for the memory ops-history wiring (Sprint 57.77).
 * Category: Frontend / e2e / memory
 * Scope: Phase 57 / Sprint 57.77 (AD-Memory-OpsHistory-Backend frontend half)
 *
 * Description:
 *   Mocks the two backend calls the memory page makes — GET /api/v1/memory/matrix
 *   (header total + 5×3 grid) and GET /api/v1/memory/ops (RecentOps rows +
 *   TimeTravel marks). Auth gate passes via seedAuthJwt (mocks /auth/me).
 *   Scenarios:
 *     1. happy  → real op rows render (WRITE/EVICT, key column)
 *     2. scrub  → dragging the scrubber to the oldest time filters RecentOps to
 *                 ops at/before the cursor (the newer op disappears)
 *     3. error  → /ops 403 (require_audit_role denial) surfaces the error row
 *
 *   The matrix call is always mocked 200 so the page chrome renders; the /ops
 *   call carries the assertions.
 *
 * Created: 2026-06-04 (Sprint 57.77)
 *
 * Related:
 *   - frontend/src/features/memory/components/{RecentMemoryOpsCard,TimeTravelScrubber,MemoryView}.tsx
 *   - frontend/tests/e2e/fixtures/auth-fixtures.ts (seedAuthJwt)
 *   - playwright.config.ts (webServer + baseURL)
 */

import { expect, test } from "@playwright/test";

import { seedAuthJwt } from "../fixtures/auth-fixtures";

const MATRIX_PAYLOAD = {
  cells: [
    { layer: "system", time_scale: "permanent", count: 1 },
    { layer: "user", time_scale: "permanent", count: 2 },
  ],
  total: 3,
  gapped_layers: ["role", "session"],
};

// Two ops with distinct created_at_ms 10s apart so the scrub has a real domain.
const OLDER_MS = 1_700_000_000_000;
const NEWER_MS = 1_700_000_010_000;
const OPS_PAYLOAD = {
  ops: [
    {
      op: "WRITE",
      scope: "user",
      key: "preferences.rca_format",
      time_scale: "permanent",
      value_snapshot: "5-whys + timeline",
      actor: "incident-responder",
      created_at_ms: NEWER_MS,
    },
    {
      op: "EVICT",
      scope: "tenant",
      key: "anomaly.token_spike",
      time_scale: null,
      value_snapshot: null,
      actor: null,
      created_at_ms: OLDER_MS,
    },
  ],
  next_cursor: null,
};

test.describe("Sprint 57.77 memory ops-history wiring", () => {
  test.beforeEach(async ({ page }) => {
    await seedAuthJwt(page);
    // Matrix always 200 so the page chrome renders in every scenario.
    await page.route("**/api/v1/memory/matrix", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(MATRIX_PAYLOAD),
      }),
    );
  });

  test("happy: real op rows render", async ({ page }) => {
    await page.route("**/api/v1/memory/ops**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(OPS_PAYLOAD),
      }),
    );

    await page.goto("/memory");

    await expect(page.getByText("Recent memory ops")).toBeVisible();
    await expect(page.getByText("preferences.rca_format")).toBeVisible();
    await expect(page.getByText("anomaly.token_spike")).toBeVisible();
    await expect(page.getByText("WRITE")).toBeVisible();
    await expect(page.getByText("EVICT")).toBeVisible();
  });

  test("scrub: dragging to the oldest time filters out the newer op", async ({ page }) => {
    await page.route("**/api/v1/memory/ops**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(OPS_PAYLOAD),
      }),
    );

    await page.goto("/memory");
    await expect(page.getByText("preferences.rca_format")).toBeVisible();

    // Set the slider to 0 → cursor = minMs (oldest op time). The newer WRITE op
    // (NEWER_MS > cursor) is filtered out; the older EVICT op survives.
    const slider = page.getByRole("slider", { name: /time travel scrubber/i });
    await slider.fill("0");

    await expect(page.getByText("preferences.rca_format")).toBeHidden();
    await expect(page.getByText("anomaly.token_spike")).toBeVisible();
  });

  test("error: /ops 403 surfaces the error row", async ({ page }) => {
    await page.route("**/api/v1/memory/ops**", (route) =>
      route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({ detail: "auditor role required" }),
      }),
    );

    await page.goto("/memory");

    await expect(page.getByTestId("memory-ops-error")).toBeVisible();
    await expect(page.getByText("auditor role required")).toBeVisible();
  });
});
