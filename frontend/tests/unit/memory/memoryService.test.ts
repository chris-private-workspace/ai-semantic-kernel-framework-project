/**
 * File: frontend/tests/unit/memory/memoryService.test.ts
 * Purpose: Unit test for memoryService — URL building + 4xx/5xx error surface + fetchWithAuth integration.
 * Category: Frontend / tests / unit / memory
 * Scope: Phase 57 / Sprint 57.12 Day 2 / US-3
 *
 * Created: 2026-05-10 (Sprint 57.12 Day 2 / US-3)
 *
 * Modification History:
 *   - 2026-06-04: Sprint 57.77 — add fetchOps describe (limit / before URL build + parse + error)
 *   - 2026-05-10: Initial creation (Sprint 57.12 Day 2 / US-3)
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  _testing,
  memoryService,
} from "../../../src/features/memory/services/memoryService";
import type { MemoryOpsResponse } from "../../../src/features/memory/types";

const PAGE_BODY = {
  items: [],
  total: 0,
  has_more: false,
  next_offset: null,
  page_size: 50,
};

describe("memoryService", () => {
  let fetchSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    fetchSpy = vi.spyOn(global, "fetch");
  });

  afterEach(() => {
    fetchSpy.mockRestore();
  });

  it("_buildPageParams sets limit + offset", () => {
    const params = _testing._buildPageParams(25, 10);
    expect(params.get("limit")).toBe("25");
    expect(params.get("offset")).toBe("10");
  });

  it("fetchRecent builds /recent?layer=...&limit=...&offset=... + returns parsed JSON on 200", async () => {
    fetchSpy.mockResolvedValueOnce(new Response(JSON.stringify(PAGE_BODY), { status: 200 }));
    const result = await memoryService.fetchRecent({ layer: "user", limit: 50, offset: 0 });
    const calledUrl = fetchSpy.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/memory/recent?");
    expect(calledUrl).toContain("layer=user");
    expect(calledUrl).toContain("limit=50");
    expect(calledUrl).toContain("offset=0");
    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/memory/recent?"),
      expect.objectContaining({ credentials: "include" }),
    );
    expect(result).toEqual(PAGE_BODY);
  });

  it("fetchByScope builds /scope/{layer}/{scope_id} path with URI-encoded scope_id", async () => {
    fetchSpy.mockResolvedValueOnce(new Response(JSON.stringify(PAGE_BODY), { status: 200 }));
    await memoryService.fetchByScope("user", "abc 123", 50, 0);
    const calledUrl = fetchSpy.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/memory/scope/user/abc%20123?");
  });

  it("fetchByTime builds /by-time/{layer}/{time_scale} path", async () => {
    fetchSpy.mockResolvedValueOnce(new Response(JSON.stringify(PAGE_BODY), { status: 200 }));
    await memoryService.fetchByTime("user", "permanent", 50, 0);
    const calledUrl = fetchSpy.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/memory/by-time/user/permanent?");
  });

  it("throws Error with detail message on 403 (auditor RBAC denial)", async () => {
    fetchSpy.mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: "Audit role required" }), { status: 403 }),
    );
    await expect(memoryService.fetchRecent({ layer: "user", limit: 50, offset: 0 })).rejects.toThrow(
      "Audit role required",
    );
  });

  it("throws Error with detail message on 501 (layer not yet wired)", async () => {
    fetchSpy.mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: "layer=role not yet supported (Phase 58+ scope)" }), {
        status: 501,
      }),
    );
    await expect(memoryService.fetchRecent({ layer: "role", limit: 50, offset: 0 })).rejects.toThrow(
      "layer=role not yet supported (Phase 58+ scope)",
    );
  });
});

const MOCK_OPS: MemoryOpsResponse = {
  ops: [
    {
      op: "WRITE",
      scope: "user",
      key: "preferences.rca_format",
      time_scale: "permanent",
      value_snapshot: "5-whys + timeline",
      actor: "incident-responder",
      created_at_ms: 1_700_000_002_000,
    },
    {
      op: "EVICT",
      scope: "tenant",
      key: "anomaly.token_spike",
      time_scale: null,
      value_snapshot: null,
      actor: null,
      created_at_ms: 1_700_000_001_000,
    },
  ],
  next_cursor: 1_700_000_001_000,
};

describe("memoryService.fetchOps (Sprint 57.77)", () => {
  let fetchSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    fetchSpy = vi.spyOn(global, "fetch");
  });

  afterEach(() => {
    fetchSpy.mockRestore();
  });

  it("builds /ops?limit=50 with no before + parses MemoryOpsResponse", async () => {
    fetchSpy.mockResolvedValueOnce(new Response(JSON.stringify(MOCK_OPS), { status: 200 }));
    const result = await memoryService.fetchOps();
    const calledUrl = fetchSpy.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/memory/ops?");
    expect(calledUrl).toContain("limit=50");
    expect(calledUrl).not.toContain("before=");
    expect(result).toEqual(MOCK_OPS);
  });

  it("builds /ops?limit=50&before=<n> when a cursor is provided", async () => {
    fetchSpy.mockResolvedValueOnce(
      new Response(JSON.stringify({ ops: [], next_cursor: null }), { status: 200 }),
    );
    await memoryService.fetchOps(50, 1_700_000_001_000);
    const calledUrl = fetchSpy.mock.calls[0][0] as string;
    expect(calledUrl).toContain("limit=50");
    expect(calledUrl).toContain("before=1700000001000");
  });

  it("surfaces the backend detail message on a non-ok (403) response", async () => {
    fetchSpy.mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: "auditor role required" }), { status: 403 }),
    );
    await expect(memoryService.fetchOps()).rejects.toThrow("auditor role required");
  });
});
