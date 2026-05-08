/**
 * File: frontend/tests/e2e/chat/chat-v2-ship.spec.ts
 * Purpose: Playwright e2e — Sprint 57.8 chat-v2 real-ship coverage (auth gate + AppShellV2 + happy path + network error).
 * Category: Frontend / e2e / chat
 * Scope: Phase 57 / Sprint 57.8 US-5 Day 3
 *
 * Description:
 *   Sprint 57.8 promotes /chat-v2 from skeleton to real ship:
 *     1. Page wraps in AppShellV2 (sidebar + sticky header with pageTitle="Chat (V2)")
 *     2. Auth gate via Navigate when isAuthenticated() === false
 *     3. ChatLayout body (sessions placeholder + main + inspector placeholder)
 *     4. chatService swapped raw fetch → fetchWithAuth (Sprint 57.7 IAM JWT injection)
 *
 *   This spec OWNS Day 3 ship verification. ApprovalCard regression tests
 *   live in approval-card.spec.ts (4 cases, updated with seedAuthJwt
 *   beforeEach in Sprint 57.8).
 *
 *   Network mocking strategy matches Sprint 53.6 D11 rationale (see
 *   approval-fixtures.ts header) — Playwright page.route() over real
 *   backend boot.
 *
 * Created: 2026-05-09 (Sprint 57.8 Day 3)
 *
 * Related:
 *   - frontend/src/pages/chat-v2/index.tsx (auth gate + AppShellV2 wrap)
 *   - frontend/src/features/chat_v2/components/ChatLayout.tsx (D11 surgical)
 *   - frontend/src/features/chat_v2/services/chatService.ts (D3 fetchWithAuth)
 *   - tests/e2e/fixtures/auth-fixtures.ts
 */

import { expect, test } from "@playwright/test";

import { mockChatSSE } from "../fixtures/approval-fixtures";
import { clearAuthJwt, seedAuthJwt } from "../fixtures/auth-fixtures";

test.describe("Sprint 57.8 US-5 — chat-v2 real ship", () => {
  test("auth gate: unauthenticated visit redirects to /auth/login", async ({ page }) => {
    // Explicit no-seed: ensure localStorage is empty for this test.
    await clearAuthJwt(page);

    await page.goto("/chat-v2/");

    // Navigate component fires; URL should change to /auth/login.
    await expect(page).toHaveURL(/\/auth\/login/);
  });

  test("happy path: authenticated visit renders AppShellV2 + ChatLayout body", async ({
    page,
  }) => {
    await seedAuthJwt(page);

    await page.goto("/chat-v2/");

    // AppShellV2 page-level title (sticky header h1).
    const pageTitle = page.getByRole("heading", { level: 1, name: "Chat (V2)" });
    await expect(pageTitle).toBeVisible();

    // ChatLayout body — sessions placeholder visible (Phase 51.x carryover label).
    await expect(page.getByRole("heading", { level: 3, name: "Sessions" })).toBeVisible();

    // ChatLayout body — inspector placeholder visible.
    await expect(page.getByRole("heading", { level: 3, name: "Inspector" })).toBeVisible();

    // InputBar present (Sprint 50.2 component) — placeholder text "Ask the agent…".
    await expect(page.getByPlaceholder(/Ask the agent/i)).toBeVisible();
  });

  test("happy path: send message → SSE stream consumed (chatService via fetchWithAuth)", async ({
    page,
  }) => {
    await seedAuthJwt(page);

    // Mock backend SSE — minimal loop_start + loop_end sequence.
    await mockChatSSE(page, [
      {
        event: "loop_start",
        data: { session_id: "ssn-test-1", request_id: "req-1", trace_id: null },
      },
      { event: "turn_start", data: { turn_num: 1, trace_id: null } },
      {
        event: "loop_end",
        data: { stop_reason: "end_turn", total_turns: 1, trace_id: null },
      },
    ]);

    await page.goto("/chat-v2/");

    const textarea = page.getByPlaceholder(/Ask the agent/i);
    await textarea.fill("Hello agent");
    await textarea.press("Enter");

    // User message rendered in MessageList; assert presence.
    await expect(page.getByText("Hello agent")).toBeVisible();
  });

  test("network error: backend returns 500 → service onError surfaces gracefully", async ({
    page,
  }) => {
    await seedAuthJwt(page);

    // Mock backend POST /chat/ to return 500.
    await page.route("**/api/v1/chat/", async (route) => {
      if (route.request().method() !== "POST") {
        await route.fallback();
        return;
      }
      await route.fulfill({
        status: 500,
        contentType: "text/plain",
        body: "Internal Server Error",
      });
    });

    await page.goto("/chat-v2/");

    // Page should remain on /chat-v2/ after the error (no crash redirect);
    // page-level h1 still visible (AppShellV2 unaffected by service error).
    const textarea = page.getByPlaceholder(/Ask the agent/i);
    await textarea.fill("Triggers 500");
    await textarea.press("Enter");

    await expect(page).toHaveURL(/\/chat-v2/);
    await expect(
      page.getByRole("heading", { level: 1, name: "Chat (V2)" }),
    ).toBeVisible();
  });
});
