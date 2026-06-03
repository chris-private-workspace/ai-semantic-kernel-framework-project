/**
 * File: frontend/tests/e2e/chat/chat-v2-inspector-trace-memory.spec.ts
 * Purpose: Playwright e2e — Sprint 57.75 A-5 Inspector Trace + Memory tabs (span/memory SSE).
 * Category: Frontend / e2e / chat
 * Scope: Phase 57 / Sprint 57.75 Day 4 / US-1 + US-2
 *
 * Description:
 *   Validates the chat-v2 Inspector Trace + Memory tabs end-to-end via a mocked
 *   SSE stream (page.route() per the established network-mock pattern):
 *     - A real_llm-shaped stream carrying span_started/span_ended (LOOP→TURN→
 *       LLM_CALL/TOOL_EXEC) + memory_accessed → Trace tab shows the span
 *       waterfall + Memory tab lists the accesses.
 *     - An echo_demo-shaped stream (no memory_accessed) → Memory tab shows the
 *       honest empty state (Sprint 57.75 D-DAY0-5).
 *
 *   The real-backend span/memory emit path is exercised by the backend unit
 *   tests (Track A); this spec OWNS the frontend consumer behavior. SSE mock at
 *   the network layer keeps the spec fast + isolated (no backend boot).
 *
 * Created: 2026-06-03 (Sprint 57.75 Day 4)
 *
 * Modification History (newest-first):
 *   - 2026-06-03: Initial creation (Sprint 57.75 Day 4 / US-1 + US-2)
 *
 * Related:
 *   - frontend/src/features/chat_v2/components/inspector/{InspectorTrace,InspectorMemory}.tsx
 *   - frontend/src/features/chat_v2/store/chatStore.ts (spans + memoryOps slices)
 *   - tests/e2e/fixtures/approval-fixtures.ts (mockChatSSE)
 *   - tests/e2e/fixtures/auth-fixtures.ts (seedAuthJwt)
 */

import { expect, test } from "@playwright/test";

import { mockChatSSE } from "../fixtures/approval-fixtures";
import { seedAuthJwt } from "../fixtures/auth-fixtures";

test.describe("Sprint 57.75 A-5 — chat-v2 Inspector Trace + Memory", () => {
  test("real_llm stream → Trace waterfall + Memory ops list render", async ({ page }) => {
    await seedAuthJwt(page);
    await mockChatSSE(page, [
      { event: "loop_start", data: { session_id: "ssn-tm-1", request_id: "req-tm-1", trace_id: null } },
      {
        event: "span_started",
        data: { span_id: "sp-loop", parent_span_id: "", span_type: "LOOP", span_name: "agent_loop", trace_id: null },
      },
      { event: "turn_start", data: { turn_num: 1, trace_id: null } },
      {
        event: "span_started",
        data: { span_id: "sp-turn", parent_span_id: "sp-loop", span_type: "TURN", span_name: "agent_loop.turn", trace_id: null },
      },
      {
        event: "span_started",
        data: { span_id: "sp-llm", parent_span_id: "sp-turn", span_type: "LLM_CALL", span_name: "agent_loop.llm_call", trace_id: null },
      },
      {
        event: "memory_accessed",
        data: {
          layer: "user",
          operation: "READ",
          key: "preferences.rca_format",
          summary: "5-whys + timeline",
          time_scale: "permanent",
          trace_id: null,
        },
      },
      {
        event: "span_ended",
        data: { span_id: "sp-llm", span_type: "LLM_CALL", span_name: "agent_loop.llm_call", duration_ms: 910, trace_id: null },
      },
      {
        event: "span_ended",
        data: { span_id: "sp-turn", span_type: "TURN", span_name: "agent_loop.turn", duration_ms: 1200, trace_id: null },
      },
      {
        event: "span_ended",
        data: { span_id: "sp-loop", span_type: "LOOP", span_name: "agent_loop", duration_ms: 1420, trace_id: null },
      },
      { event: "loop_end", data: { stop_reason: "end_turn", total_turns: 1, trace_id: null } },
    ]);

    await page.goto("/chat-v2/");
    await expect(page.getByRole("heading", { level: 1, name: "Chat (V2)" })).toBeVisible();

    const textarea = page.getByPlaceholder(/Ask the agent/i);
    await textarea.fill("investigate INC-4087");
    await textarea.press("Enter");

    // Trace tab → span waterfall with the 3 nested spans.
    await page.getByRole("tab", { name: "Trace" }).click();
    await expect(page.getByTestId("inspector-trace")).toBeVisible();
    await expect(page.getByTestId("inspector-trace-span-sp-loop")).toBeVisible();
    await expect(page.getByTestId("inspector-trace-span-sp-turn")).toBeVisible();
    await expect(page.getByTestId("inspector-trace-span-sp-llm")).toBeVisible();
    await expect(page.getByText("1.42s")).toBeVisible();

    // Memory tab → the READ access. Scope the text assertions to the first op
    // row: under the dev-server (vite + React StrictMode), the SSE mock stream
    // can be consumed twice (StrictMode double-mount / EventSource reconnect),
    // appending a duplicate memory row. Memory ops are an append-only log —
    // correctly NOT deduped (a genuine repeat-read is a distinct event; only
    // spans dedup, by span_id) — so a page-wide getByText would hit a strict-mode
    // violation on the replayed row. Production SSE does not replay; op-0 is the
    // deterministic first access and the assertion stays strict-mode-safe.
    await page.getByRole("tab", { name: "Memory" }).click();
    await expect(page.getByTestId("inspector-memory")).toBeVisible();
    const memOp0 = page.getByTestId("inspector-memory-op-0");
    await expect(memOp0).toBeVisible();
    await expect(memOp0).toContainText("preferences.rca_format");
    await expect(memOp0).toContainText("5-whys + timeline");
  });

  test("echo_demo stream (no memory_accessed) → Memory tab honest empty state", async ({ page }) => {
    await seedAuthJwt(page);
    await mockChatSSE(page, [
      { event: "loop_start", data: { session_id: "ssn-tm-2", request_id: "req-tm-2", trace_id: null } },
      {
        event: "span_started",
        data: { span_id: "sp-loop2", parent_span_id: "", span_type: "LOOP", span_name: "agent_loop", trace_id: null },
      },
      { event: "turn_start", data: { turn_num: 1, trace_id: null } },
      {
        event: "span_ended",
        data: { span_id: "sp-loop2", span_type: "LOOP", span_name: "agent_loop", duration_ms: 30, trace_id: null },
      },
      { event: "loop_end", data: { stop_reason: "end_turn", total_turns: 1, trace_id: null } },
    ]);

    await page.goto("/chat-v2/");
    const textarea = page.getByPlaceholder(/Ask the agent/i);
    await textarea.fill("hello");
    await textarea.press("Enter");

    // Trace tab still works (spans always open).
    await page.getByRole("tab", { name: "Trace" }).click();
    await expect(page.getByTestId("inspector-trace-span-sp-loop2")).toBeVisible();

    // Memory tab → honest empty state (no fabricated row).
    await page.getByRole("tab", { name: "Memory" }).click();
    await expect(page.getByTestId("inspector-memory-empty")).toBeVisible();
    await expect(page.getByText("no memory accesses this session")).toBeVisible();
  });
});
