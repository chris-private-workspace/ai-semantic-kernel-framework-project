/**
 * File: frontend/tests/unit/chat_v2/chatService.cancelSession.test.ts
 * Purpose: Vitest coverage for cancelSession (Sprint 57.143 user-Stop interrupt marker).
 * Category: Frontend / tests / unit / chat_v2
 * Scope: Phase 57 / Sprint 57.143 (AD-UserStop-Resume-Context, US-2)
 *
 * Description:
 *   cancelSession POSTs /api/v1/chat/sessions/{id}/cancel via fetchWithAuth so the
 *   server records a `[Request interrupted by user]` marker. A non-2xx throws so the
 *   Stop handler can choose to surface / ignore it (the hook ignores it).
 *
 * Modification History:
 *   - 2026-06-25: Initial creation (Sprint 57.143)
 */

import { afterEach, describe, expect, test, vi } from "vitest";

vi.mock("@/features/auth/services/authService", () => ({
  fetchWithAuth: vi.fn(),
}));

import { fetchWithAuth } from "@/features/auth/services/authService";
import { cancelSession } from "@/features/chat_v2/services/chatService";

const mockFetch = vi.mocked(fetchWithAuth);

afterEach(() => vi.restoreAllMocks());

describe("cancelSession (Sprint 57.143)", () => {
  test("POSTs the cancel endpoint on success", async () => {
    mockFetch.mockResolvedValue({ ok: true } as Response);

    await cancelSession("s1");

    expect(mockFetch).toHaveBeenCalledWith("/api/v1/chat/sessions/s1/cancel", {
      method: "POST",
    });
  });

  test("throws on a non-2xx response", async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 404,
      text: async () => "not found",
    } as Response);

    await expect(cancelSession("nope")).rejects.toThrow(/HTTP 404/);
  });
});
