/**
 * File: frontend/tests/e2e/chat/approval-card.spec.ts
 * Purpose: Playwright e2e — chat-v2 inline ApprovalCard (Sprint 53.5 US-2 component).
 * Category: Frontend / e2e / chat
 * Scope: Phase 53 / Sprint 53.6 US-3
 *
 * Description:
 *   Validates the SSE-driven approval card lifecycle on /chat-v2:
 *     1. User sends a message → chat router emits SSE stream
 *     2. ApprovalRequested event → ApprovalCard renders with risk badge
 *     3. User clicks Approve / Reject → governanceService.decide POST fires
 *        + optimistic store update flips card to "Decision" state
 *     4. ApprovalReceived event (server confirms decision) → store reconciles
 *     5. Risk badge color matches per-level palette
 *
 *   Backend POST /api/v1/chat/ is mocked at the network layer using
 *   Playwright `page.route()` (D11 — see fixtures/approval-fixtures.ts).
 *   The mock returns a canned SSE body containing the event sequence;
 *   the SPA's chatService parser drives the store + ApprovalCard render.
 *
 * Created: 2026-05-04 (Sprint 53.6 Day 3)
 *
 * Related:
 *   - frontend/src/features/chat_v2/components/{ApprovalCard,MessageList,InputBar}.tsx
 *   - frontend/src/features/chat_v2/services/chatService.ts (SSE parser)
 *   - frontend/src/features/chat_v2/store/chatStore.ts (approvals slice)
 *   - tests/e2e/fixtures/approval-fixtures.ts
 */

import { expect, test } from "@playwright/test";

import {
  approvalSseSequence,
  mockChatSSE,
  mockGovernanceDecide,
} from "../fixtures/approval-fixtures";
import { seedAuthJwt } from "../fixtures/auth-fixtures";

const APPROVAL_ID = "11111111-1111-4111-8111-111111111111";

async function sendChatMessage(page: import("@playwright/test").Page, message: string) {
  // Find the textarea by its placeholder and submit via Enter (matches InputBar).
  const textarea = page.getByPlaceholder(/Ask the agent/i);
  await textarea.fill(message);
  await textarea.press("Enter");
}

test.describe("Sprint 53.6 US-3 — ChatV2 inline ApprovalCard", () => {
  // Sprint 57.8 Day 3: chat-v2 now has auth gate; seed JWT in every test
  // so isAuthenticated() returns true before navigation.
  test.beforeEach(async ({ page }) => {
    await seedAuthJwt(page);
  });

  test("approve flow: card appears via SSE, decide POST fires, card flips to Decision state", async ({
    page,
  }) => {
    await mockChatSSE(
      page,
      approvalSseSequence({ approvalId: APPROVAL_ID, riskLevel: "HIGH" }),
    );
    const decide = await mockGovernanceDecide(page);

    await page.goto("/chat-v2/");
    await sendChatMessage(page, "Run the sensitive tool");

    // Card renders from approval_requested event.
    const card = page.getByRole("region", { name: "HITL approval" });
    await expect(card).toBeVisible();
    await expect(card).toContainText(APPROVAL_ID);
    await expect(card).toContainText("HIGH");

    // Click Approve → governance decide POST captured.
    await card.getByRole("button", { name: "Approve" }).click();
    await expect.poll(() => decide.records.length).toBe(1);
    expect(decide.records[0]).toMatchObject({
      requestId: APPROVAL_ID,
      decision: "approved",
    });

    // Optimistic store update: card flips to Decision badge state.
    await expect(card).toContainText(/Decision/);
    await expect(card).toContainText(/APPROVED/);
  });

  test("reject flow: decide POST captures decision=rejected", async ({ page }) => {
    await mockChatSSE(
      page,
      approvalSseSequence({ approvalId: APPROVAL_ID, riskLevel: "MEDIUM" }),
    );
    const decide = await mockGovernanceDecide(page);

    await page.goto("/chat-v2/");
    await sendChatMessage(page, "Trigger approval");

    const card = page.getByRole("region", { name: "HITL approval" });
    await expect(card).toBeVisible();
    await card.getByRole("button", { name: "Reject" }).click();

    await expect.poll(() => decide.records.length).toBe(1);
    expect(decide.records[0]).toMatchObject({
      requestId: APPROVAL_ID,
      decision: "rejected",
    });
    await expect(card).toContainText(/REJECTED/);
  });

  test("risk badge text + color reflects risk level (CRITICAL → dark red)", async ({ page }) => {
    await mockChatSSE(
      page,
      approvalSseSequence({ approvalId: APPROVAL_ID, riskLevel: "CRITICAL" }),
    );
    await mockGovernanceDecide(page);

    await page.goto("/chat-v2/");
    await sendChatMessage(page, "Critical tool call");

    const card = page.getByRole("region", { name: "HITL approval" });
    await expect(card).toBeVisible();
    // Risk text is rendered in a span styled with the CRITICAL palette
    // entry (#b71c1c). Locate the span and assert its computed color.
    const riskText = card.getByText("CRITICAL", { exact: true });
    await expect(riskText).toBeVisible();
    const colorRgb = await riskText.evaluate(
      (el) => window.getComputedStyle(el).color,
    );
    // #b71c1c → rgb(183, 28, 28)
    expect(colorRgb.replace(/\s+/g, "")).toBe("rgb(183,28,28)");
  });

  test("approval_received SSE flips card without user click (server-driven decision)", async ({
    page,
  }) => {
    await mockChatSSE(
      page,
      approvalSseSequence({
        approvalId: APPROVAL_ID,
        riskLevel: "LOW",
        decision: "APPROVED",
      }),
    );
    await mockGovernanceDecide(page);

    await page.goto("/chat-v2/");
    await sendChatMessage(page, "Auto-approved tool");

    const card = page.getByRole("region", { name: "HITL approval" });
    await expect(card).toBeVisible();
    // approval_received event already in the stream → card lands directly
    // in decision state; no Approve button visible.
    await expect(card).toContainText(/APPROVED/);
    await expect(card.getByRole("button", { name: "Approve" })).toHaveCount(0);
  });
});
