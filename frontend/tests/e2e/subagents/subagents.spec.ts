/**
 * File: frontend/tests/e2e/subagents/subagents.spec.ts
 * Purpose: Hermetic Playwright e2e for the subagents registry real-data wiring (Sprint 57.78 Track B).
 * Category: Frontend / e2e / subagents
 * Scope: Phase 57 / Sprint 57.78 (re-point STUB → agent_catalog registry)
 *
 * Description:
 *   Mocks the backend calls the page makes — GET /api/v1/auth/me (so the
 *   authStore bootstraps an authenticated user and RequireAuth passes) and
 *   GET /api/v1/subagents (the agent_catalog registry the page consumes).
 *   Scenarios:
 *     1. happy → real catalog rows render (role/model/modes/status); a null-model
 *        row shows "—"; clicking a row selects it; detail spec shows the prompt.
 *     2. error → 403 surfaces the inline error banner.
 *
 *   A dev token is seeded via addInitScript so fetchWithAuth attaches
 *   Authorization and the mocked /auth/me drives status=authenticated.
 *
 * Created: 2026-06-04 (Sprint 57.78 Track B)
 *
 * Modification History (newest-first):
 *   - 2026-06-04: Initial creation (Sprint 57.78 Track B) — subagents registry real-data wiring e2e
 *
 * Related:
 *   - frontend/src/pages/subagents/SubagentsPage.tsx
 *   - frontend/src/features/subagents/services/subagentsService.ts
 *   - frontend/tests/e2e/admin-tenants.spec.ts (route-mock + seedAuthJwt pattern)
 *   - playwright.config.ts (webServer + baseURL)
 */

import { expect, test } from "@playwright/test";

const USER_ME = {
  user: { id: "u-1", email: "user@example.test", display_name: "User" },
  tenant: { id: "t-1", name: "Acme", code: "ACME" },
  roles: ["tenant_member"],
};

const SUBAGENTS_PAYLOAD = {
  items: [
    {
      key: "researcher",
      name: "Researcher",
      model: "claude-sonnet-4-5",
      allowed_modes: ["handoff", "as_tool"],
      status: "live",
      system_prompt: "Investigate and gather evidence for the orchestrator.",
      budget: { max_tokens: 8000, max_duration: 240, max_concurrent: 4, max_depth: 2 },
      tools: ["log.tail", "metrics.query"],
    },
    {
      key: "reviewer",
      name: "Reviewer",
      model: null,
      allowed_modes: ["fork", "teammate"],
      status: "staging",
      system_prompt: "Review the produced artifact before handoff.",
      budget: null,
      tools: [],
    },
  ],
  gapped: ["calls_24h", "p95_latency", "success_rate", "avg_tokens", "top_orchestrator"],
};

test.describe("Sprint 57.78 subagents registry real-data wiring", () => {
  test.beforeEach(async ({ page }) => {
    // Seed dev token so fetchWithAuth attaches Authorization (no /auth/login bounce).
    await page.addInitScript(() => {
      window.localStorage.setItem("v2_jwt", "e2e-fake-token");
    });
    // Authenticated tenant user so RequireAuth renders the view.
    await page.route("**/api/v1/auth/me", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(USER_ME),
      }),
    );
  });

  test("happy: real catalog rows render + row-click selects + detail spec", async ({ page }) => {
    await page.route("**/api/v1/subagents", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(SUBAGENTS_PAYLOAD),
      }),
    );

    await page.goto("/subagents");

    // Real rows render (role + model + status).
    await expect(page.getByText("researcher").first()).toBeVisible();
    await expect(page.getByText("reviewer").first()).toBeVisible();
    // model shows in the row cell AND the detail spec-tab <option> → first().
    await expect(page.getByText("claude-sonnet-4-5").first()).toBeVisible();
    await expect(page.getByText("live")).toBeVisible();
    await expect(page.getByText("staging")).toBeVisible();
    // null-model row shows the honest-gap "—".
    await expect(page.getByText("—").first()).toBeVisible();

    // Click the reviewer row → detail card header reflects the selection.
    await page.getByText("reviewer").first().click();
    // Detail card shows the selected spec's system prompt (in the textarea).
    await expect(
      page.locator("textarea.textarea"),
    ).toHaveValue(/Review the produced artifact/);
  });

  test("error: 403 surfaces the inline error banner", async ({ page }) => {
    await page.route("**/api/v1/subagents", (route) =>
      route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Forbidden" }),
      }),
    );

    await page.goto("/subagents");

    await expect(page.getByRole("alert")).toBeVisible();
    await expect(page.getByRole("alert")).toContainText(/Forbidden/);
  });
});
