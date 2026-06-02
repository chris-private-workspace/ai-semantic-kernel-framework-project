/**
 * File: frontend/tests/unit/chat_v2/eventSchema.generated.test.ts
 * Purpose: Assert the generated SSE event contract re-exported via chat_v2/types.
 * Category: Frontend / chat_v2 / tests
 * Scope: Phase 57 / Sprint 57.67 (A-5b — event schema codegen, US-4)
 *
 * Description:
 *   The 18 event types + KNOWN_LOOP_EVENT_TYPES are generated from the backend
 *   wire-schema registry (backend/src/api/v1/chat/event_wire_schema.py) and
 *   re-exported through ../types. This test imports from the SAME path every
 *   downstream consumer uses (@/features/chat_v2/types), proving the Stage-2
 *   re-export swap is transparent + the generated set has the expected
 *   18 wire-types including the 4 newest diagnostic events (Sprint 57.66).
 *
 * Created: 2026-06-02 (Sprint 57.67)
 * Modified: 2026-06-02
 */

import { describe, expect, test } from "vitest";

import { KNOWN_LOOP_EVENT_TYPES } from "@/features/chat_v2/types";

describe("generated SSE event schema (re-exported via chat_v2/types)", () => {
  test("KNOWN_LOOP_EVENT_TYPES has exactly 18 wire-types", () => {
    expect(KNOWN_LOOP_EVENT_TYPES.size).toBe(18);
  });

  test("recognizes the 4 newest diagnostic events (Sprint 57.66)", () => {
    for (const t of [
      "prompt_built",
      "context_compacted",
      "state_checkpointed",
      "tripwire_triggered",
    ]) {
      expect(KNOWN_LOOP_EVENT_TYPES.has(t)).toBe(true);
    }
  });

  test("recognizes core loop wire-types", () => {
    for (const t of [
      "loop_start",
      "llm_response",
      "tool_call_result",
      "loop_end",
    ]) {
      expect(KNOWN_LOOP_EVENT_TYPES.has(t)).toBe(true);
    }
  });

  test("does not recognize an unknown / unwired wire-type", () => {
    expect(KNOWN_LOOP_EVENT_TYPES.has("memory_accessed")).toBe(false);
  });
});
