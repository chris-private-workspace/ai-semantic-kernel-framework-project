/**
 * File: frontend/tests/unit/verification/chatStore.verifications.test.ts
 * Purpose: Vitest tests for chatStore verifications slice (Sprint 57.11 US-5 Day 3 §3.3 + §3.4).
 * Category: Frontend / tests / unit / verification
 * Scope: Phase 57 / Sprint 57.11 Day 3 / US-5
 *
 * Description:
 *   Verifies appendVerification + clearVerifications reducers and the new
 *   verification_passed / verification_failed cases in mergeEvent (per
 *   AD-Frontend-SSE-Silent-Drop-Fix bundle codified by CONVENTION.md §7).
 *
 * Created: 2026-05-10 (Sprint 57.11 Day 3 §3.3+§3.4)
 */

import { afterEach, beforeEach, describe, expect, test } from "vitest";

import { useChatStore } from "@/features/chat_v2/store/chatStore";
import type { LoopEvent } from "@/features/chat_v2/types";
import type { VerificationEvent } from "@/features/verification/types";

describe("chatStore verifications slice (Sprint 57.11 US-5)", () => {
  beforeEach(() => {
    useChatStore.getState().reset();
  });

  afterEach(() => {
    useChatStore.getState().reset();
  });

  test("appendVerification appends to verifications array", () => {
    const ev1: VerificationEvent = {
      type: "verification_passed",
      data: { verifier: "v1", verifier_type: "rules_based", score: 0.95 },
    };
    const ev2: VerificationEvent = {
      type: "verification_failed",
      data: {
        verifier: "v2",
        verifier_type: "llm_judge",
        reason: "off-topic",
        suggested_correction: "stay focused",
      },
    };

    useChatStore.getState().appendVerification(ev1);
    useChatStore.getState().appendVerification(ev2);

    const state = useChatStore.getState();
    expect(state.verifications).toHaveLength(2);
    expect(state.verifications[0]).toEqual(ev1);
    expect(state.verifications[1]).toEqual(ev2);
  });

  test("clearVerifications resets array to empty", () => {
    useChatStore.getState().appendVerification({
      type: "verification_passed",
      data: { verifier: "v1", verifier_type: "rules_based", score: 0.9 },
    });
    expect(useChatStore.getState().verifications).toHaveLength(1);

    useChatStore.getState().clearVerifications();
    expect(useChatStore.getState().verifications).toEqual([]);
  });

  test("mergeEvent verification_passed/_failed routes to verifications array (SSE branch)", () => {
    // AD-Frontend-SSE-Silent-Drop-Fix: types.ts type union + KNOWN_LOOP_EVENT_TYPES
    // set both list these so parseSSEFrame doesn't drop; mergeEvent handles them.
    const passed: LoopEvent = {
      type: "verification_passed",
      data: { verifier: "v1", verifier_type: "rules_based", score: 0.99 },
    };
    const failed: LoopEvent = {
      type: "verification_failed",
      data: {
        verifier: "v2",
        verifier_type: "external",
        reason: "policy violation",
        suggested_correction: null,
      },
    };

    useChatStore.getState().mergeEvent(passed);
    useChatStore.getState().mergeEvent(failed);

    const state = useChatStore.getState();
    expect(state.verifications).toHaveLength(2);
    expect(state.verifications[0]).toEqual(passed);
    expect(state.verifications[1]).toEqual(failed);
    // Also recorded in rawEvents (audit trail)
    expect(state.rawEvents).toHaveLength(2);
  });
});
