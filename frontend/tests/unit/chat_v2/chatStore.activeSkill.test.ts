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
 *   - 2026-06-15: Sprint 57.120 — +turn_start carry-forward onto AgentTurn.activeSkill (3 cases)
 *   - 2026-06-14: Initial creation (Sprint 57.116)
 */

import { afterEach, beforeEach, describe, expect, test } from "vitest";

import { useChatStore } from "@/features/chat_v2/store/chatStore";
import type { AgentTurn, LoopEvent, Turn, UserTurn } from "@/features/chat_v2/types";

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
  cachedInputTokens: null, // Sprint 57.133: per-turn cache-hit tokens (null until llm_response)
  model: null, // Sprint 57.131: per-turn model (null until llm_request)
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

// Sprint 57.120 factories: turn_start pushes a new AgentTurn; message_injected
// pushes a mid-run injected (no-skill) user turn.
const turnStart = (): LoopEvent => ({ type: "turn_start", data: { turn_num: 1 } });
const messageInjected = (text: string): LoopEvent => ({
  type: "message_injected",
  data: { text },
});

const lastAgent = (): AgentTurn | undefined => {
  const turns = useChatStore.getState().turns;
  for (let i = turns.length - 1; i >= 0; i--) {
    if (turns[i].role === "agent") return turns[i] as AgentTurn;
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

describe("chatStore — turn_start carries activeSkill onto the AgentTurn (Sprint 57.120)", () => {
  beforeEach(() => useChatStore.getState().reset());
  afterEach(() => useChatStore.getState().reset());

  test("carries the trigger user turn's activeSkill onto the new AgentTurn", () => {
    useChatStore.setState({ turns: [userTurn("u1")] });
    useChatStore.getState().mergeEvent(loopStart("code-review")); // stamps u1.activeSkill
    useChatStore.getState().mergeEvent(turnStart()); // pushes the AgentTurn
    expect(lastAgent()?.activeSkill).toBe("code-review");
  });

  test("a mid-run injected user turn does not clear the loop's skill on a later turn_start", () => {
    useChatStore.setState({ turns: [userTurn("u1")] });
    useChatStore.getState().mergeEvent(loopStart("summarize")); // stamps u1
    useChatStore.getState().mergeEvent(turnStart()); // agent turn 1 — carries the skill
    useChatStore.getState().mergeEvent(messageInjected("do X")); // injected (no-skill) user turn
    useChatStore.getState().mergeEvent(turnStart()); // agent turn 2 — still the skill
    expect(lastAgent()?.activeSkill).toBe("summarize");
  });

  test("a new no-skill loop's turn_start leaves activeSkill undefined (no leak from a prior skilled loop)", () => {
    // a prior skilled loop
    useChatStore.setState({ turns: [userTurn("u1")] });
    useChatStore.getState().mergeEvent(loopStart("code-review"));
    useChatStore.getState().mergeEvent(turnStart());
    expect(lastAgent()?.activeSkill).toBe("code-review");
    // a fresh user message + a loop_start with NO force-load
    useChatStore.setState({ turns: [...useChatStore.getState().turns, userTurn("u2")] });
    useChatStore.getState().mergeEvent(loopStart(null)); // u2 stays unstamped
    useChatStore.getState().mergeEvent(turnStart()); // agent turn 2 — no skill (no leak)
    expect(lastAgent()?.activeSkill).toBeUndefined();
  });
});
