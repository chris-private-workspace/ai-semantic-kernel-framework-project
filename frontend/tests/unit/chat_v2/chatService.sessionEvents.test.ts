/**
 * File: frontend/tests/unit/chat_v2/chatService.sessionEvents.test.ts
 * Purpose: Vitest coverage for fetchSessionEvents (Sprint 57.126 history replay service).
 * Category: Frontend / tests / unit / chat_v2
 * Scope: Phase 57 / Sprint 57.126 (US-3)
 *
 * Description:
 *   fetchSessionEvents GETs /api/v1/sessions/{id}/events via fetchWithAuth and
 *   returns the `events` array (the persisted transcript the replay reducer consumes).
 *   A non-2xx throws so the caller can surface it.
 *
 * Modification History:
 *   - 2026-06-16: Initial creation (Sprint 57.126)
 */

import { afterEach, describe, expect, test, vi } from "vitest";

vi.mock("@/features/auth/services/authService", () => ({
  fetchWithAuth: vi.fn(),
}));

import { fetchWithAuth } from "@/features/auth/services/authService";
import { fetchSessionEvents } from "@/features/chat_v2/services/chatService";

const mockFetch = vi.mocked(fetchWithAuth);

afterEach(() => vi.restoreAllMocks());

describe("fetchSessionEvents (Sprint 57.126)", () => {
  test("returns the events array on 200", async () => {
    const events = [
      { type: "user_message", data: { text: "hi" }, sequence_num: 1, timestamp_ms: 1000 },
      { type: "loop_start", data: { session_id: "s1" }, sequence_num: 2, timestamp_ms: 1001 },
    ];
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ events }),
    } as Response);

    const result = await fetchSessionEvents("s1");

    expect(mockFetch).toHaveBeenCalledWith("/api/v1/sessions/s1/events", { method: "GET" });
    expect(result).toEqual(events);
  });

  test("throws on a non-2xx response", async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 404,
      text: async () => "not found",
    } as Response);

    await expect(fetchSessionEvents("nope")).rejects.toThrow(/HTTP 404/);
  });
});
