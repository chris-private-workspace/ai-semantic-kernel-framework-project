/**
 * File: frontend/tests/unit/chat_v2/chatService.parseSSEFrame.test.ts
 * Purpose: Vitest coverage for Sprint 57.66 SSE wire-type recognition — the 4
 *          new diagnostic events + cache fields flow through streamChat's frame
 *          parser (parseSSEFrame) instead of being silently dropped.
 * Category: Frontend / tests / unit / chat_v2
 * Scope: Phase 57 / Sprint 57.66 (Stage 2 — events → SSE serialize FE register)
 *
 * Description:
 *   parseSSEFrame is module-private; exercise it through the public streamChat
 *   path by mocking fetchWithAuth to return a ReadableStream of SSE frames and
 *   collecting the typed LoopEvents delivered to onEvent. Mirrors the frame
 *   wire format `event: <type>\ndata: <json>\n\n`. Confirms:
 *     - each of the 4 new wire types is recognized (NOT dropped)
 *     - llm_response carries cached_input_tokens (number)
 *     - loop_end carries cached_input_tokens + cache_hit_rate (numbers)
 *     - an unknown wire type is still dropped (gate intact)
 *
 * Created: 2026-06-02 (Sprint 57.66)
 *
 * Modification History:
 *   - 2026-06-02: Initial creation (Sprint 57.66 Stage 2)
 */

import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

import { streamChat } from "@/features/chat_v2/services/chatService";
import type { LoopEvent } from "@/features/chat_v2/types";

const { fetchWithAuthMock } = vi.hoisted(() => ({
  fetchWithAuthMock: vi.fn(),
}));

vi.mock("@/features/auth/services/authService", () => ({
  fetchWithAuth: fetchWithAuthMock,
}));

/** Build a single SSE frame string: `event: <type>\ndata: <json>\n\n`. */
const frame = (type: string, data: unknown): string =>
  `event: ${type}\ndata: ${JSON.stringify(data)}\n\n`;

/** A Response whose body is a ReadableStream emitting `frames` as UTF-8 bytes. */
const sseResponse = (frames: string[]): Response => {
  const encoder = new TextEncoder();
  const body = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const f of frames) controller.enqueue(encoder.encode(f));
      controller.close();
    },
  });
  return new Response(body, {
    status: 200,
    headers: { "Content-Type": "text/event-stream" },
  });
};

/** Drive streamChat over `frames` and return every LoopEvent delivered. */
const collectEvents = async (frames: string[]): Promise<LoopEvent[]> => {
  fetchWithAuthMock.mockResolvedValueOnce(sseResponse(frames));
  const events: LoopEvent[] = [];
  await streamChat(
    { message: "diag", mode: "real_llm" },
    { onEvent: (ev) => events.push(ev) },
  );
  return events;
};

describe("chatService parseSSEFrame — Sprint 57.66 diagnostic wire types", () => {
  beforeEach(() => {
    fetchWithAuthMock.mockReset();
  });
  afterEach(() => {
    vi.clearAllMocks();
  });

  // --- 4 new diagnostic events recognized (NOT dropped) -------------------

  test("prompt_built is recognized and typed (not dropped)", async () => {
    const events = await collectEvents([
      frame("prompt_built", {
        messages_count: 7,
        estimated_input_tokens: 14820,
        cache_breakpoints_count: 2,
        memory_layers_used: ["system", "tenant", "user"],
        position_strategy_used: "lost_in_middle",
        duration_ms: 12,
      }),
    ]);
    expect(events).toHaveLength(1);
    expect(events[0].type).toBe("prompt_built");
    if (events[0].type === "prompt_built") {
      expect(events[0].data.messages_count).toBe(7);
      expect(events[0].data.estimated_input_tokens).toBe(14820);
      expect(events[0].data.cache_breakpoints_count).toBe(2);
      expect(events[0].data.memory_layers_used).toEqual(["system", "tenant", "user"]);
      expect(events[0].data.position_strategy_used).toBe("lost_in_middle");
      expect(events[0].data.duration_ms).toBe(12);
    }
  });

  test("context_compacted is recognized and typed (not dropped)", async () => {
    const events = await collectEvents([
      frame("context_compacted", {
        tokens_before: 30000,
        tokens_after: 9000,
        compaction_strategy: "summarize",
        messages_compacted: 18,
        duration_ms: 340,
      }),
    ]);
    expect(events).toHaveLength(1);
    expect(events[0].type).toBe("context_compacted");
    if (events[0].type === "context_compacted") {
      expect(events[0].data.tokens_before).toBe(30000);
      expect(events[0].data.tokens_after).toBe(9000);
      expect(events[0].data.compaction_strategy).toBe("summarize");
      expect(events[0].data.messages_compacted).toBe(18);
      expect(events[0].data.duration_ms).toBe(340);
    }
  });

  test("state_checkpointed is recognized and typed (not dropped)", async () => {
    const events = await collectEvents([
      frame("state_checkpointed", { version: 3 }),
    ]);
    expect(events).toHaveLength(1);
    expect(events[0].type).toBe("state_checkpointed");
    if (events[0].type === "state_checkpointed") {
      expect(events[0].data.version).toBe(3);
      expect(typeof events[0].data.version).toBe("number");
    }
  });

  test("tripwire_triggered is recognized and typed (not dropped)", async () => {
    const events = await collectEvents([
      frame("tripwire_triggered", {
        violation_type: "token_budget",
        detail: "exceeded 200k input cap",
      }),
    ]);
    expect(events).toHaveLength(1);
    expect(events[0].type).toBe("tripwire_triggered");
    if (events[0].type === "tripwire_triggered") {
      expect(events[0].data.violation_type).toBe("token_budget");
      expect(events[0].data.detail).toBe("exceeded 200k input cap");
    }
  });

  // --- cache fields parse as numbers --------------------------------------

  test("llm_response carries cached_input_tokens as a number", async () => {
    const events = await collectEvents([
      frame("llm_response", {
        content: "ok",
        tool_calls: [],
        thinking: null,
        cached_input_tokens: 1024,
      }),
    ]);
    expect(events).toHaveLength(1);
    expect(events[0].type).toBe("llm_response");
    if (events[0].type === "llm_response") {
      expect(events[0].data.cached_input_tokens).toBe(1024);
      expect(typeof events[0].data.cached_input_tokens).toBe("number");
    }
  });

  test("loop_end carries cached_input_tokens + cache_hit_rate as numbers", async () => {
    const events = await collectEvents([
      frame("loop_end", {
        stop_reason: "end_turn",
        total_turns: 2,
        cached_input_tokens: 2048,
        cache_hit_rate: 0.5,
      }),
    ]);
    expect(events).toHaveLength(1);
    expect(events[0].type).toBe("loop_end");
    if (events[0].type === "loop_end") {
      expect(events[0].data.cached_input_tokens).toBe(2048);
      expect(typeof events[0].data.cached_input_tokens).toBe("number");
      expect(events[0].data.cache_hit_rate).toBe(0.5);
      expect(typeof events[0].data.cache_hit_rate).toBe("number");
    }
  });

  // --- gate intact: unknown wire type still dropped -----------------------

  test("unknown wire type is still dropped (gate intact)", async () => {
    const events = await collectEvents([
      frame("totally_unknown_event", { foo: "bar" }),
      // a known event after it confirms the stream itself is fine
      frame("state_checkpointed", { version: 1 }),
    ]);
    expect(events).toHaveLength(1);
    expect(events[0].type).toBe("state_checkpointed");
  });
});
