/**
 * File: frontend/tests/e2e/chat/chat-v2-real-backend.spec.ts
 * Purpose: Unmocked chat-v2 e2e regression net — drives the REAL chat UI against a
 *   LIVE backend (no page.route / no mockChatSSE) so the front-to-back agent-loop
 *   wiring (UI send → POST /api/v1/chat/ → AgentLoopImpl → real SSE → store render)
 *   is exercised end-to-end, not asserted against a fabricated fixture.
 * Category: Frontend / e2e / chat
 * Scope: Phase 57+ — closes the "every chat-v2 spec mocks the backend" gap
 *   (v2-overall-progress-gap-assessment-20260606.md §2: UI-driven path had NO
 *   unmocked test at any layer).
 *
 * Description:
 *   The rest of the chat-v2 e2e suite (chat-v2-ship / -loop-inline / -subagent-inline
 *   / -inspector-trace-memory) intercepts /api/v1/chat/ with Playwright page.route()
 *   + mockChatSSE — so a hand-crafted SSE fixture, never the real loop, is what those
 *   tests verify. This spec is the inverse: it hits a *live* backend so the genuine
 *   wiring is proven.
 *
 *   It uses `mode='echo_demo'` deliberately: echo_demo drives a REAL AgentLoopImpl
 *   over the REAL POST /api/v1/chat/ SSE endpoint, but with the offline MockChatClient
 *   (handler.build_echo_demo_handler: turn 1 → echo_tool(text=message); turn 2 →
 *   END_TURN). That gives a deterministic, Azure-free, CI-safe round-trip that still
 *   exercises the full server-side stack + SSE serializer + frontend stream parser +
 *   Zustand Turn reducer. The real_llm (real Azure) path is covered separately by the
 *   manual UI smoke + .github/workflows/e2e-real-llm-smoke.yml (opt-in, secrets-gated).
 *
 *   Opt-in like connectivity.spec.ts — skipped unless RUN_CONNECTIVITY is set, so
 *   `npm run test:e2e` / CI stay hermetic. Auth is the real dev-login cookie path
 *   (POST /api/v1/auth/dev-login → v2_jwt cookie), NOT the mocked /auth/me fixture.
 *
 *   Run it after the backend is up (python scripts/dev.py start → backend :8000):
 *
 *       RUN_CONNECTIVITY=1 npm run e2e -- chat-v2-real-backend
 *
 * Created: 2026-06-06
 *
 * Related:
 *   - frontend/tests/e2e/connectivity/connectivity.spec.ts (sibling opt-in live-backend spec)
 *   - frontend/tests/e2e/chat/chat-v2-ship.spec.ts (the MOCKED counterpart)
 *   - backend/src/api/v1/chat/handler.py (build_echo_demo_handler — scripted echo loop)
 *   - backend/src/api/v1/chat/router.py (POST /api/v1/chat/ SSE endpoint)
 *   - frontend/src/features/chat_v2/services/chatService.ts (real fetch + SSE parser)
 *   - frontend/src/features/chat_v2/store/chatStore.ts (mergeEvent Turn reducer)
 *   - claudedocs/5-status/v2-overall-progress-gap-assessment-20260606.md §2 / §7
 */

import { expect, test } from "@playwright/test";

test.describe("chat-v2 unmocked regression net (opt-in, live backend)", () => {
  test.skip(
    !process.env.RUN_CONNECTIVITY,
    "Set RUN_CONNECTIVITY=1 (and start the backend on :8000) to run against a live backend",
  );

  test("echo_demo: real dev-login → send → real SSE round-trip renders agent turn + completes", async ({
    page,
  }) => {
    // 1) Authenticate via the REAL dev fake-login — sets the v2_jwt cookie on the
    //    browser context (same path as connectivity.spec). NO /auth/me mock.
    const loginResp = await page.request.post("/api/v1/auth/dev-login");
    expect(loginResp.ok(), `dev-login failed: ${loginResp.status()}`).toBeTruthy();

    // 2) Open the real chat page; the auth gate must pass via the cookie (not bounce).
    await page.goto("/chat-v2/");
    expect(page.url(), "auth gate bounced to /auth/login").not.toContain("/auth/login");
    await expect(
      page.getByRole("heading", { level: 1, name: "Chat (V2)" }),
    ).toBeVisible();

    // 3) Explicitly select echo_demo mode (also the store default) — exercises the
    //    real mode toggle and pins the deterministic, Azure-free path.
    await page.getByRole("button", { name: "echo_demo", exact: true }).click();

    // 4) Send a message through the real composer → real POST /api/v1/chat/ → real SSE.
    const prompt = "regression-net ping — unmocked e2e";
    const textarea = page.getByPlaceholder(/Ask the agent/i);
    await textarea.fill(prompt);
    await textarea.press("Enter");

    // 5) The user turn renders immediately (pushUserMessage).
    await expect(page.getByText(prompt)).toBeVisible();

    // 6) PROOF the live loop ran end-to-end over real SSE (not a fixture):
    //    loop_end → stopReason="end_turn" → AgentTurn shows the "stop: end_turn"
    //    badge. This frame only arrives if POST succeeded, the AgentLoopImpl ran,
    //    and the SSE serializer + frontend parser + Turn reducer all worked.
    await expect(page.getByText(/stop:\s*end_turn/i)).toBeVisible({ timeout: 20_000 });

    // 7) The composer status pill flips to "completed" (loop_end → status="completed").
    //    Scoped to the input bar so it can't match anything else.
    const inputBar = page.getByTestId("input-bar");
    await expect(inputBar.getByText(/completed/i)).toBeVisible({ timeout: 20_000 });

    // 8) Negative guard: the stream must NOT have errored (status="error" → "● error"
    //    pill). Mutually exclusive with "completed", but assert explicitly for clarity.
    await expect(inputBar.getByText(/●\s*error/i)).toHaveCount(0);
  });
});
