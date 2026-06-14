/**
 * File: frontend/tests/unit/chat_v2/chatStore.activeSkill.test.ts
 * Purpose: Vitest coverage for the Sprint 57.116 loop_start active_skill user-turn stamp.
 * Category: Frontend / tests / unit / chat_v2
 * Scope: Phase 57 / Sprint 57.116 (Skills Inspector affordance)
 *
 * Description:
 *   The chat router stamps the opening loop_start frame with the server-confirmed
 *   force-load skill (or null). mergeEvent's loop_start case stamps that name onto
 *   the LAST user turn (the one that triggered the run) — only when truthy, so a
 *   null (the resume mirror / no force-load) never overwrites an existing chip.
 *
 * Modification History:
 *   - 2026-06-14: Initial creation (Sprint 57.116)
 */

import { afterEach, beforeEach, describe, expect, test } from "vitest";

import { useChatStore } from "@/features/chat_v2/store/chatStore";
import type { LoopEvent, Turn, UserTurn } from "@/features/chat_v2/types";

const userTurn = (id: string, text = "msg"): UserTurn => ({ role: "user", id, at: "10:00", text });

const agentTurn = (id: string): Turn => ({
  role: "agent",
  id,
  at: "10:01",
  stopReason: null,
  durationMs: null,
  blocks: [],
  tokensIn: null,
  tokensOut: null,
  tokensThinking: null,
  costUsd: null,
  traceId: null,
  spanId: null,
});

const loopStart = (active: string | null): LoopEvent => ({
  type: "loop_start",
  data: { session_id: "s1", request_id: "r1", active_skill: active },
});

const lastUser = (): UserTurn | undefined => {
  const turns = useChatStore.getState().turns;
  for (let i = turns.length - 1; i >= 0; i--) {
    if (turns[i].role === "user") return turns[i] as UserTurn;
  }
  return undefined;
};

describe("chatStore — loop_start active_skill stamp (Sprint 57.116)", () => {
  beforeEach(() => useChatStore.getState().reset());
  afterEach(() => useChatStore.getState().reset());

  test("stamps the last user turn when active_skill is set", () => {
    useChatStore.setState({ turns: [userTurn("u1")] });
    useChatStore.getState().mergeEvent(loopStart("release-notes"));
    expect(lastUser()?.activeSkill).toBe("release-notes");
  });

  test("a null active_skill leaves the user turn unstamped", () => {
    useChatStore.setState({ turns: [userTurn("u1")] });
    useChatStore.getState().mergeEvent(loopStart(null));
    expect(lastUser()?.activeSkill).toBeUndefined();
  });

  test("a later null does not clear an existing chip (resume-safe)", () => {
    useChatStore.setState({ turns: [userTurn("u1")] });
    useChatStore.getState().mergeEvent(loopStart("release-notes"));
    useChatStore.getState().mergeEvent(loopStart(null)); // e.g. a resume loop_start
    expect(lastUser()?.activeSkill).toBe("release-notes");
  });

  test("stamps the last USER turn, skipping a trailing agent turn", () => {
    useChatStore.setState({ turns: [userTurn("u1"), agentTurn("a1")] });
    useChatStore.getState().mergeEvent(loopStart("summarize"));
    const turns = useChatStore.getState().turns;
    expect((turns[0] as UserTurn).activeSkill).toBe("summarize");
    // the trailing agent turn carries no skill field (not mis-stamped)
    expect("activeSkill" in turns[1]).toBe(false);
  });
});
