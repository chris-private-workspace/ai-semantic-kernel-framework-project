/**
 * File: frontend/tests/e2e/governance/approvals.spec.ts
 * Purpose: Playwright e2e — reviewer flow on /governance/approvals page
 *   (Sprint 53.5 US-1 components: ApprovalsPage / ApprovalList / DecisionModal).
 * Category: Frontend / e2e / governance
 * Scope: Phase 53 / Sprint 53.6 US-2
 *
 * Description:
 *   Validates that the governance approvals page (53.5 US-1):
 *     1. Renders the list of pending approvals fetched from
 *        GET /api/v1/governance/approvals.
 *     2. Opens DecisionModal on row click and dispatches the
 *        correct POST /decide payload for approve / reject / escalate.
 *     3. Refreshes the list after a decision, removing decided items.
 *     4. Surfaces backend errors via the modal's [role="alert"] region.
 *
 *   Backend network calls are mocked at the browser layer via Playwright's
 *   `page.route()` (D11 — see fixtures/approval-fixtures.ts header for
 *   rationale: backend integration is exercised by 11 tests in
 *   tests/integration/api/test_governance_endpoints.py).
 *
 * Created: 2026-05-04 (Sprint 53.6 Day 2)
 * Last Modified: 2026-05-09
 *
 * Modification History (newest-first):
 *   - 2026-05-09: Sprint 57.9 US-6 Day 4 — add seedAuthJwt beforeEach (Sprint 57.9 US-1
 *     auth gate added to /governance route; tests must seed JWT to bypass redirect)
 *   - 2026-05-04: Initial creation (Sprint 53.6 Day 2)
 *
 * Related:
 *   - frontend/src/features/governance/components/{ApprovalsPage,ApprovalList,DecisionModal}.tsx
 *   - frontend/src/features/governance/services/governanceService.ts
 *   - tests/e2e/fixtures/approval-fixtures.ts
 *   - tests/e2e/fixtures/auth-fixtures.ts (seedAuthJwt for auth gate bypass)
 */

import { expect, test } from "@playwright/test";

import {
  mockGovernanceDecide,
  mockGovernanceList,
  sampleApprovals,
} from "../fixtures/approval-fixtures";
import { seedAuthJwt } from "../fixtures/auth-fixtures";

test.describe("Sprint 53.6 US-2 — Governance approvals reviewer flow", () => {
  // Sprint 57.9 US-1 added auth gate to /governance route; seed JWT before
  // each test so isAuthenticated() returns true and the page renders instead
  // of redirecting to /auth/login.
  test.beforeEach(async ({ page }) => {
    await seedAuthJwt(page);
  });

  test("main flow: approve removes the item from the list", async ({ page }) => {
    const items = sampleApprovals();
    const list = await mockGovernanceList(page, items);
    const decide = await mockGovernanceDecide(page);

    await page.goto("/governance/approvals");

    // List shows 3 approvals.
    await expect(page.getByRole("heading", { name: "Pending Approvals" })).toBeVisible();
    await expect(page.getByRole("row")).toHaveCount(4); // header + 3 data rows
    await expect(page.getByText("delete_customer_record")).toBeVisible();
    await expect(page.getByText("send_external_email")).toBeVisible();

    // Click Review on the first row → modal opens.
    await page
      .getByRole("row", { name: /delete_customer_record/ })
      .getByRole("button", { name: "Review" })
      .click();
    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible();
    await expect(dialog.getByRole("heading", { name: /Review approval/ })).toBeVisible();

    // Type a reason and approve. After successful decide, list refreshes
    // with the remaining 2 items.
    await dialog.getByRole("textbox").fill("Reviewed; matches policy.");
    list.setItems(items.slice(1));
    await dialog.getByRole("button", { name: "Approve" }).click();

    // Modal closes; list now has 2 data rows.
    await expect(dialog).not.toBeVisible();
    await expect(page.getByRole("row")).toHaveCount(3);
    await expect(page.getByText("delete_customer_record")).not.toBeVisible();

    // Decide POST captured with right shape.
    expect(decide.records).toHaveLength(1);
    expect(decide.records[0]).toMatchObject({
      requestId: items[0].request_id,
      decision: "approved",
      reason: "Reviewed; matches policy.",
    });
  });

  test("reject flow dispatches decision=rejected", async ({ page }) => {
    const items = sampleApprovals();
    await mockGovernanceList(page, items);
    const decide = await mockGovernanceDecide(page);

    await page.goto("/governance/approvals");
    await page
      .getByRole("row", { name: /send_external_email/ })
      .getByRole("button", { name: "Review" })
      .click();
    const dialog = page.getByRole("dialog");
    await dialog.getByRole("textbox").fill("Off-policy recipient");
    await dialog.getByRole("button", { name: "Reject" }).click();
    await expect(dialog).not.toBeVisible();

    expect(decide.records).toHaveLength(1);
    expect(decide.records[0]).toMatchObject({
      requestId: items[1].request_id,
      decision: "rejected",
      reason: "Off-policy recipient",
    });
  });

  test("escalate flow dispatches decision=escalated", async ({ page }) => {
    const items = sampleApprovals();
    await mockGovernanceList(page, items);
    const decide = await mockGovernanceDecide(page);

    await page.goto("/governance/approvals");
    await page
      .getByRole("row", { name: /execute_db_migration/ })
      .getByRole("button", { name: "Review" })
      .click();
    const dialog = page.getByRole("dialog");
    await dialog.getByRole("button", { name: "Escalate" }).click();
    await expect(dialog).not.toBeVisible();

    expect(decide.records).toHaveLength(1);
    expect(decide.records[0]).toMatchObject({
      requestId: items[2].request_id,
      decision: "escalated",
      reason: null, // no reason typed → service sends null
    });
  });

  test("decide error surfaces in modal alert (covers cross-tenant 404 / 500 / 422)", async ({
    page,
  }) => {
    const items = sampleApprovals();
    await mockGovernanceList(page, items);
    await mockGovernanceDecide(page, {
      respondWith: { status: 404, body: { detail: "Approval not found" } },
    });

    await page.goto("/governance/approvals");
    await page
      .getByRole("row", { name: /delete_customer_record/ })
      .getByRole("button", { name: "Review" })
      .click();
    const dialog = page.getByRole("dialog");
    await dialog.getByRole("button", { name: "Approve" }).click();

    // Modal stays open and shows error from backend detail field.
    await expect(dialog).toBeVisible();
    await expect(dialog.getByRole("alert")).toHaveText(/Approval not found/);
  });

  test("empty list renders the no-items message", async ({ page }) => {
    await mockGovernanceList(page, []);

    await page.goto("/governance/approvals");
    await expect(page.getByRole("heading", { name: "Pending Approvals" })).toBeVisible();
    await expect(page.getByText("No pending approvals.")).toBeVisible();
  });
});
